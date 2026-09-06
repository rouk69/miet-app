// Расписание: неделя цикла → день → пары. Данные тянутся с miet.ru живьём.

import { icon } from '../icons.js';
import { esc, emptyState, toast } from '../ui.js';
import { settings, save } from '../store.js';
import {
  fetchSchedule, weekOfCycle, slotsOf, dayCounts, mondayOf, shortSemestr,
  DAY_SHORT, DAY_NAMES,
} from '../schedule.js';
import { refresh } from '../router.js';
import { haptic, hapticSelect } from '../tg.js';
import { screen, pickGroup, iconBtn, shortDate } from './common.js';

/** Преподаватель и аудитория — одна строка на подгруппу. */
const whereLine = e => `
  <div class="lesson-meta">
    ${e.room ? `<span>${icon('door', 14)} ${esc(e.room)}</span>` : ''}
    ${e.teacherShort ? `<span>${icon('teacher', 14)} ${esc(e.teacherShort)}</span>` : ''}
  </div>`;

/**
 * Карточка пары. Принимает слот из slotsOf, но переживает и одиночную
 * запись — на главной и в поиске приходит именно она.
 */
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

  const kind = sameSubject ? l.kind || entries[0].kind : '';
  const kindCls = sameSubject ? l.kindCls || entries[0].kindCls : 'oth';
  const flags = (sameSubject ? l.flags : null) || [];

  return `
    <div class="lesson ${state}">
      <div class="lesson-time">
        <div class="lesson-from">${esc(l.from)}</div>
        <div class="lesson-to">${esc(l.to)}</div>
      </div>
      <div class="lesson-body">
        ${body}
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
          ${kind ? `<span class="kind ${kindCls}">${esc(kind)}</span>` : ''}
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
      body: `<div class="card" style="padding:20px">
          <div class="row-subtitle" style="margin-bottom:16px">
            Расписание берётся напрямую с miet.ru и обновляется автоматически.
          </div>
          <button class="btn-primary" id="pick">Выбрать группу</button>
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
      body: emptyState(`Не удалось загрузить: ${err.message}`, 'refresh'),
    });
    return node;
  }

  const curWeek = weekOfCycle(now, sched.semestr, settings.weekShift);
  const todayDay = ((now.getDay() + 6) % 7) + 1;
  let week = params.week ?? curWeek;
  let day = params.day ?? (todayDay <= 6 ? todayDay : 1);

  const node = screen({
    title: 'Расписание',
    subtitle: `${settings.group} · ${shortSemestr(sched.semestr)}`,
    actions: iconBtn('refresh', 'reload') + iconBtn('sliders', 'group'),
    body: `
      <div class="pill-row" id="weeks">
        ${[0, 1, 2, 3].map(w => `
          <button class="pill ${w === week ? 'active' : ''}" data-week="${w}">
            ${w + 1}-я неделя${w === curWeek ? ' · сейчас' : ''}
          </button>`).join('')}
      </div>
      <div class="week-strip" id="days"></div>
      <div id="list" class="stack" style="margin-top:16px"></div>`,
  });

  const daysEl = node.querySelector('#days');
  const listEl = node.querySelector('#list');

  function drawDays() {
    const counts = dayCounts(sched, week);
    const mon = mondayOf(now);
    mon.setDate(mon.getDate() + (week - curWeek) * 7);
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
    const mon = mondayOf(now);
    mon.setDate(mon.getDate() + (week - curWeek) * 7 + day - 1);
    const isToday = mon.toDateString() === now.toDateString();
    listEl.innerHTML = `
      <div class="section-head" style="margin:0 2px 2px">
        <div class="section-title">${DAY_NAMES[day]}</div>
        <span class="muted" style="font-size:14px;font-weight:600">${shortDate(mon)}</span>
      </div>
      ${items.length
        ? items.map(l => lessonRow(l, isToday ? now : null)).join('')
        : emptyState('В этот день пар нет', 'clock')}
      ${items.length ? `<div class="fab-note">
          ${items.length} ${plural(items.length, 'пара', 'пары', 'пар')} ·
          источник: miet.ru${sched.cached ? ' · из кеша' : ''}
        </div>` : ''}`;
  }

  drawDays();
  drawList();

  node.querySelector('#weeks').addEventListener('click', e => {
    const b = e.target.closest('[data-week]');
    if (!b) return;
    week = +b.dataset.week;
    hapticSelect();
    node.querySelectorAll('#weeks .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    drawDays();
    drawList();
  });

  daysEl.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (!b) return;
    day = +b.dataset.day;
    hapticSelect();
    daysEl.querySelectorAll('.week-day').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
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
      toast('Расписание обновлено');
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
