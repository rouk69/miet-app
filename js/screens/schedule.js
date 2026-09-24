// Расписание: неделя цикла → день → пары. Данные тянутся с miet.ru живьём.

import { subjectBadge } from '../subjects.js';
import { icon } from '../icons.js';
import { esc, toast } from '../ui.js';
import { art, artState } from '../art.js';
import { settings, save } from '../store.js';
import {
  fetchSchedule, weekOfCycle, slotsOf, dayCounts, mondayOf, shortSemestr,
  gapsOf, humanGap, weekName, WEEK_SHORT, weekRange, studyWeek, aheadTo, DAY_SHORT, DAY_NAMES,
} from '../schedule.js';
import { refresh } from '../router.js';
import { haptic, hapticSelect } from '../tg.js';
import { screen, pickGroup, iconBtn, shortDate } from './common.js';

/**
 * Как звать преподавателя в строке.
 *
 * Приложение показывает короткое имя — на длинное в карточке нет места.
 * Но расписание приходит двумя путями: у miet.ru короткое лежит своим
 * полем, а из кеша бота может прийти только полное. Пусто — не рисуем
 * ничего, это лучше пустой строки со значком.
 */
export const teacherOf = l =>
  (l && (l.teacherShort || l.teacher)) || '';

/** Преподаватель и аудитория — одна строка на подгруппу. */
const whereLine = e => `
  <div class="lesson-meta">
    ${e.room ? `<span>${icon('door', 14)} ${esc(e.room)}</span>` : ''}
    ${teacherOf(e) ? `<span>${icon('teacher', 14)} ${esc(teacherOf(e))}</span>` : ''}
  </div>`;

/**
 * Карточка пары. Принимает слот из slotsOf, но переживает и одиночную
 * запись — на главной и в поиске приходит именно она.
 */
// Какой значок какому виду занятия. Лекция — доска, лабораторная —
// колба, практика и семинар — карандаш: это не украшение, а второй
// признак рядом с цветом, потому что цвет различают не все.
const KIND_ICONS = { lek: 'board', lab: 'flask', pr: 'pencil' };

/**
 * Полоска окна между парами.
 *
 * Стоит между строками, а не внутри: окно — это не занятие, и делать
 * из него такую же карточку значило бы прятать его среди пар. Здесь
 * важно ровно две вещи — сколько ждать и до которого часа.
 */
export const gapRow = g => `
  <div class="gap-row">
    <span class="gap-line"></span>
    <span class="gap-text">
      ${icon('clock', 13)}
      Окно ${esc(humanGap(g.minutes) || `${g.pairs} пары`)}
      ${g.from && g.to ? `· ${esc(g.from)}–${esc(g.to)}` : ''}
    </span>
    <span class="gap-line"></span>
  </div>`;

/** Пары дня вперемешку с окнами — в том порядке, в каком их проживают. */
export function dayRows(slots, now = null) {
  const gaps = gapsOf(slots);
  return slots.map((l, i) => {
    const after = gaps.find(g => g.after === l.pair);
    return lessonRow(l, now) + (after && i + 1 < slots.length ? gapRow(after) : '');
  }).join('');
}

export function lessonRow(l, now = null, showState = true) {
  const entries = l.entries || [l];
  const sameSubject = l.sameSubject ?? true;

  let state = '';
  if (now && showState) {
    const mins = now.getHours() * 60 + now.getMinutes();
    const to = m => { const [h, x] = m.split(':').map(Number); return h * 60 + x; };
    if (mins >= to(l.from) && mins < to(l.to)) state = 'live';
    else if (mins >= to(l.to)) state = 'past';
  }

  const body = sameSubject
    ? `<div class="lesson-name">${esc(l.subject || entries[0].subject)}</div>
       ${entries.map(whereLine).join('')}`
    : entries.map(e => `
        <div class="lesson-name">${esc(e.subject)}</div>
        ${whereLine(e)}`).join('');

  // Значок ставится по первому предмету слота: у пары с подгруппами
  // предметы бывают разные, но плашка одна на строку — рисовать два
  // значка в столбик значило бы спорить с собственной версткой.
  const badge = subjectBadge(l.subject || entries[0].subject, 30);

  const kind = sameSubject ? l.kind || entries[0].kind : '';
  const kindCls = sameSubject ? l.kindCls || entries[0].kindCls : 'oth';
  const flags = (sameSubject ? l.flags : null) || [];

  return `
    <div class="lesson ${state}">
      <div class="lesson-time">
        <div class="lesson-from">${esc(l.from)}</div>
        <div class="lesson-to">${esc(l.to)}</div>
        ${l.altFrom ? `<div class="lesson-alt">или ${esc(l.altFrom)}</div>` : ''}
      </div>
      ${badge}
      <div class="lesson-body">
        ${body}
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
          ${kind ? `<span class="kind ${kindCls}">
            ${icon(KIND_ICONS[kindCls] || 'clipboard', 12)}${esc(kind)}
          </span>` : ''}
          ${flags.map(f => `<span class="kind oth">${esc(f)}</span>`).join('')}
          ${entries.length > 1 ? '<span class="kind oth">подгруппы</span>' : ''}
          ${state === 'live' ? '<span class="live-badge"><i></i>идёт сейчас</span>' : ''}
        </div>
      </div>
    </div>`;
}

export default async function scheduleScreen(params = {}) {
  if (!settings.group) {
    const node = screen({
      title: 'Расписание',
      subtitle: 'Сначала выбери группу',
      body: `<div class="card has-art" style="padding:20px">
          <div class="has-art-body">
            <div class="row-subtitle" style="margin-bottom:16px">
              Расписание берётся напрямую с miet.ru и обновляется автоматически.
            </div>
            <button class="btn-primary" id="pick">Выбрать группу</button>
          </div>
          ${art('group', 84, 'art-aside')}
        </div>`,
    });
    node.querySelector('#pick').addEventListener('click', () => pickGroup(() => refresh()));
    return node;
  }

  const now = new Date();
  let sched;
  try {
    sched = await fetchSchedule(settings.group, { force: params.force });
  } catch (err) {
    const node = screen({
      title: 'Расписание',
      subtitle: settings.group,
      body: `<div class="card">
        ${artState('offline', 'Расписание не загрузилось', err.message)}
        <button class="btn-primary" id="retry" style="margin:0 20px 20px">
          Попробовать снова
        </button>
      </div>`,
    });
    node.querySelector('#retry').addEventListener('click', () => refresh());
    return node;
  }

  const curWeek = weekOfCycle(now, sched.semestr, settings.weekShift);
  const todayDay = ((now.getDay() + 6) % 7) + 1;
  // Неделя — это сдвиг от текущей: стрелками можно уйти и в следующий цикл,
  // а даты при этом честно идут дальше, а не возвращаются к началу круга.
  let off = params.week != null ? aheadTo(params.week, curWeek) : 0;
  let week = (curWeek + off) % 4;
  let day = params.day ?? (todayDay <= 6 ? todayDay : 1);
  const mondayAt = o => { const m = mondayOf(now); m.setDate(m.getDate() + o * 7); return m; };

  const node = screen({
    title: 'Расписание',
    subtitle: `${settings.group} · ${shortSemestr(sched.semestr)}`,
    actions: iconBtn('refresh', 'reload') + iconBtn('sliders', 'group'),
    body: `
      <div class="wk" id="weeks"></div>
      <div class="week-strip" id="days"></div>
      <div id="stale"></div>
      <div id="list" class="stack" style="margin-top:16px"></div>`,
  });

  const daysEl = node.querySelector('#days');
  const listEl = node.querySelector('#list');
  const staleEl = node.querySelector('#stale');

  /** Честная плашка: показываем сохранённое, потому что сайт молчит. */
  function drawStale() {
    staleEl.innerHTML = sched.stale
      ? `<div class="warn-note" style="margin-top:12px">
           ${icon('info', 16)}
           Показываю сохранённое расписание: ${esc(sched.why || 'сайт МИЭТ не ответил')}.
         </div>`
      : '';
  }

  /**
   * Карточка недели: официальное имя крупно, даты и номер учебной недели
   * под ним, стрелки по краям; ниже — четыре одинаковые ячейки цикла.
   * Всё умещается в ширину самого узкого телефона — ничего не уезжает.
   */
  // «Домой» — текущая неделя и сегодняшний день (в воскресенье — понедельник).
  const homeDay = todayDay <= 6 ? todayDay : 1;
  const away = () => off !== 0 || day !== homeDay;

  function drawWeeks() {
    const mon = mondayAt(off);
    const n = studyWeek(mon, sched.semestr);
    const when = off === 0 ? 'сейчас' : off === 1 ? 'следующая' : off === -1 ? 'прошлая'
      : off > 0 ? `через ${off} нед.` : `${-off} нед. назад`;
    node.querySelector('#weeks').innerHTML = `
      <div class="wk-head">
        <button class="wk-arrow" data-step="-1" aria-label="Предыдущая неделя">${icon('chevronLeft', 20)}</button>
        <div class="wk-title">
          <div class="wk-name">${esc(weekName(week))}</div>
          <div class="wk-sub">
            <span class="wk-when ${off === 0 ? 'now' : ''}">${esc(when)}</span>
            <span>${esc(weekRange(mon))}</span>${n ? `<span>${n}-я уч. неделя</span>` : ''}
          </div>
        </div>
        <button class="wk-arrow" data-step="1" aria-label="Следующая неделя">${icon('chevronRight', 20)}</button>
      </div>
      <div class="wk-seg">
        ${WEEK_SHORT.map(([a, b], w) => `
          <button class="wk-cell ${w === week ? 'active' : ''} ${w === curWeek ? 'cur' : ''}" data-week="${w}">
            <span class="wk-n">${a}</span><span class="wk-k">${b}</span>
          </button>`).join('')}
      </div>
      ${away() ? `<button class="wk-today" data-today>
        ${icon('calendar', 15)} ${todayDay <= 6 ? 'К сегодняшнему дню' : 'К текущей неделе'}
      </button>` : ''}`;
  }

  function drawDays() {
    const counts = dayCounts(sched, week);
    const mon = mondayAt(off);
    daysEl.innerHTML = [1, 2, 3, 4, 5, 6].map(d => {
      const date = new Date(mon);
      date.setDate(mon.getDate() + d - 1);
      const isToday = date.toDateString() === now.toDateString();
      return `
        <button class="week-day ${d === day ? 'active' : ''} ${isToday ? 'today' : ''}"
                data-day="${d}">
          <span class="week-day-name">${DAY_SHORT[d]}</span>
          <span class="week-day-num">${date.getDate()}</span>
          <span class="dot ${counts[d] ? '' : 'empty'}"></span>
        </button>`;
    }).join('');
  }

  function drawList() {
    const items = slotsOf(sched, week, day);
    const mon = mondayAt(off);
    mon.setDate(mon.getDate() + day - 1);
    const isToday = mon.toDateString() === now.toDateString();
    // Спросить про обед стоит только там, где он что-то меняет: в дне
    // есть 3-я пара, а группа ещё не сказала, когда у неё перерыв.
    const ask = !sched.lunch && items.some(s => s.pair === 3 && s.altFrom);
    listEl.innerHTML = `
      ${ask ? `
        <div class="lunch-ask">
          <div class="lunch-title">${icon('utensils', 17)} Когда у группы обед?</div>
          <div class="lunch-note">От этого зависит начало 3-й пары. Сайт МИЭТ пишет всем 12:00 — выбери, как у вас:</div>
          <div class="lunch-opts">
            <button class="lunch-opt" data-lunch="after3"><b>После 3-й пары</b><span>3-я в 12:00–13:20</span></button>
            <button class="lunch-opt" data-lunch="after2"><b>После 2-й пары</b><span>3-я в 12:30–13:50</span></button>
          </div>
        </div>` : ''}
      <div class="section-head" style="margin:0 2px 2px">
        <div class="section-title">${DAY_NAMES[day]}</div>
        <span class="muted" style="font-size:14px;font-weight:600">${shortDate(mon)}</span>
      </div>
      ${items.length
        ? dayRows(items, isToday ? now : null)
        : `<div class="card">${day === 6
          ? artState('rest', 'Суббота свободна', 'Пар в этот день нет')
          : artState('free', 'В этот день пар нет',
            'Свободно — можно закрыть хвосты или выдохнуть')}</div>`}
      ${items.length ? `<div class="fab-note">
          ${items.length} ${plural(items.length, 'пара', 'пары', 'пар')} ·
          источник: miet.ru${sched.cached ? ' · из кеша' : ''}
        </div>` : ''}`;
  }

  drawWeeks();
  drawDays();
  drawList();
  drawStale();

  node.querySelector('#weeks').addEventListener('click', e => {
    // Кнопок и стрелок много — легко уйти и потеряться. Одна кнопка
    // возвращает к сегодняшнему дню; видна, только когда ушёл.
    if (e.target.closest('[data-today]')) {
      off = 0; week = curWeek; day = homeDay;
      hapticSelect();
      drawWeeks(); drawDays(); drawList();
      return;
    }
    const step = e.target.closest('[data-step]');
    const cell = e.target.closest('[data-week]');
    if (!step && !cell) return;
    // Ячейка ведёт к ближайшей такой неделе (текущая — к «сейчас»),
    // стрелки листают по одной, в том числе в соседний цикл.
    if (step) off += +step.dataset.step;
    else off = aheadTo(+cell.dataset.week, curWeek);
    week = (((curWeek + off) % 4) + 4) % 4;
    hapticSelect();
    drawWeeks();
    drawDays();
    drawList();
  });

  listEl.addEventListener('click', async e => {
    const b = e.target.closest('[data-lunch]');
    if (!b) return;
    save({ lunch: { ...(settings.lunch || {}), [settings.group]: b.dataset.lunch } });
    hapticSelect();
    // Перечитываем из своей копии (поправка кладётся при выдаче) и
    // перерисовываем на месте — выбранные неделя и день остаются.
    try { sched = await fetchSchedule(settings.group); } catch { /* останется как было */ }
    drawDays();
    drawList();
    toast('Запомнил — время 3-й пары поправлено');
  });

  daysEl.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (!b) return;
    day = +b.dataset.day;
    hapticSelect();
    daysEl.querySelectorAll('.week-day').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    drawWeeks();
    drawList();
  });

  node.querySelector('[data-action="group"]').addEventListener('click', () =>
    pickGroup(() => refresh()));

  node.querySelector('[data-action="reload"]').addEventListener('click', async e => {
    const btn = e.currentTarget;
    haptic('medium');
    btn.innerHTML = '<div class="spinner"></div>';
    try {
      sched = await fetchSchedule(settings.group, { force: true });
      drawDays();
      drawList();
      drawStale();
      toast(sched.stale ? 'Сайт МИЭТ молчит — расписание прежнее'
        : 'Расписание обновлено');
    } catch (err) {
      toast(err.message);
    }
    btn.innerHTML = icon('refresh', 19);
  });

  void save;
  return node;
}

function plural(n, one, few, many) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

export { plural };
