// Две группы рядом: где вы вместе, где разошлись и когда оба свободны.
//
// Спрашивают об этом по-разному, но вопрос один: «когда мы можем
// встретиться». Поэтому экран считает не только общие пары (лекции
// потока, куда идут обе группы), но и общие окна — слоты, в которые
// свободны оба. Второе на практике нужнее первого: именно в окно можно
// договориться, а на общей лекции и так увидитесь.
//
// Расписание берётся тем же путём, что и своё, — у бота, с откатом на
// miet.ru и на вчерашнюю копию. Отдельной серверной части здесь нет: два
// расписания сравниваются на месте, и лишний маршрут только добавил бы
// точку отказа.

import { icon } from '../icons.js';
import { esc, emptyState, pillRow, bindChoice, skeleton, listCard, listRow } from '../ui.js';
import { settings, save } from '../store.js';
import { artState } from '../art.js';
import { screen, pickGroup } from './common.js';
import { subjectBadge } from '../subjects.js';
import { haptic } from '../tg.js';
import {
  fetchSchedule, weekOfCycle, slotsOf, DAY_SHORT, DAY_NAMES,
} from '../schedule.js';

// С чем сравниваем. Живёт в модуле, а не в параметрах экрана: человек
// возвращается сюда к той же паре групп, а не выбирает её каждый раз.
let other = '';

/**
 * Одно ли это занятие у двух групп.
 *
 * Сверяются названия, а не аудитории: на потоковой лекции у групп
 * совпадает всё, но в расписании МИЭТ у одной может стоять «3105», а у
 * другой — «3105 / 3107», и сравнение по кабинету развалилось бы на
 * ровном месте. Название чистится от регистра, пробелов и точек:
 * «Физика. Оптика» и «Физика.Оптика» — один предмет.
 */
export const sameLesson = (a, b) => norm(a) === norm(b) && Boolean(norm(a));

const norm = s => String(s || '').toLowerCase().replace(/[\s.«»"'-]/g, '');

/**
 * День двух групп по слотам звонков.
 *
 * Слот попадает в разбор, если пара есть хоть у кого-то: пустые слоты до
 * начала и после конца дня — это не «оба свободны», а «день ещё не
 * начался». Окном считается только дырка ВНУТРИ занятого времени.
 */
export function compareDay(mine, theirs) {
  const pairs = [...new Set([...mine.map(s => s.pair), ...theirs.map(s => s.pair)])]
    .sort((a, b) => a - b);
  if (!pairs.length) return { rows: [], together: 0, both: 0, free: 0 };

  const first = pairs[0];
  const last = pairs[pairs.length - 1];
  const byPair = (list, p) => list.find(s => s.pair === p) || null;

  const rows = [];
  let together = 0;
  let both = 0;
  let free = 0;
  for (let p = first; p <= last; p++) {
    const a = byPair(mine, p);
    const b = byPair(theirs, p);
    let state = 'one';
    if (a && b) state = sameLesson(a.subject, b.subject) ? 'together' : 'both';
    else if (!a && !b) state = 'free';
    if (state === 'together') together++;
    else if (state === 'both') both++;
    else if (state === 'free') free++;
    rows.push({ pair: p, a, b, state, from: (a || b)?.from, to: (a || b)?.to });
  }
  return { rows, together, both, free };
}

/** Сколько общих пар в каждый день недели — для полоски дней. */
export function weekTogether(mine, theirs, week) {
  return [0, 1, 2, 3, 4, 5, 6].map(d => d === 0 ? null
    : compareDay(slotsOf(mine, week, d), slotsOf(theirs, week, d)));
}

const STATE_NOTE = {
  together: 'вместе',
  both: 'у каждого своё',
  one: 'у одного',
  free: 'свободны оба',
};

function slotRow(row, mineName, otherName) {
  const cell = (s, group) => s
    ? `<div class="cmp-cell">
         ${subjectBadge(s.subject || s.entries?.[0]?.subject, 26)}
         <div class="cmp-cell-text">
           <div class="cmp-subject">${esc(s.subject || s.entries?.[0]?.subject || '—')}</div>
           <div class="cmp-where">${esc(s.entries?.[0]?.room || '')}</div>
         </div>
       </div>`
    : `<div class="cmp-cell empty"><span>${esc(group)} — свободна</span></div>`;

  return `
    <div class="cmp-row ${row.state}">
      <div class="cmp-time">
        <b>${row.pair}</b>
        <span>${esc(row.from || '')}</span>
      </div>
      <div class="cmp-pair">
        ${row.state === 'together'
    ? `<div class="cmp-cell whole">
             ${subjectBadge(row.a.subject, 30)}
             <div class="cmp-cell-text">
               <div class="cmp-subject">${esc(row.a.subject)}</div>
               <div class="cmp-where">
                 ${esc(row.a.entries?.[0]?.room || '')} · обе группы
               </div>
             </div>
           </div>`
    : cell(row.a, mineName) + cell(row.b, otherName)}
      </div>
      <div class="cmp-tag ${row.state}">${STATE_NOTE[row.state]}</div>
    </div>`;
}

export default async function compareScreen() {
  const mineName = settings.group;
  if (!mineName) {
    const node = screen({
      title: 'Две группы',
      body: `<div class="card has-art" style="padding:20px">
        <div class="has-art-body">
          <div class="row-subtitle" style="margin-bottom:16px">
            Сначала выбери свою группу — с ней и будем сравнивать.
          </div>
          <button class="btn-primary" id="pick">Выбрать группу</button>
        </div>
        ${artState('group', '', '')}
      </div>`,
    });
    node.querySelector('#pick').addEventListener('click',
      () => pickGroup(g => { save({ group: g }); location.reload(); }));
    return node;
  }

  const now = new Date();
  let week = 0;                      // уточним по расписанию, оно знает семестр
  let day = Math.min(((now.getDay() + 6) % 7) + 1, 6);

  const node = screen({
    title: 'Две группы',
    subtitle: 'Общие пары и общие окна',
    body: `
      <div class="cmp-picks">
        <button class="cmp-pick" data-pick="mine">
          <span class="cmp-pick-label">Моя группа</span>
          <span class="cmp-pick-name">${esc(mineName)}</span>
        </button>
        <span class="cmp-vs">${icon('shuffle', 16)}</span>
        <button class="cmp-pick" data-pick="other">
          <span class="cmp-pick-label">Сравнить с</span>
          <span class="cmp-pick-name">${other ? esc(other) : 'выбрать'}</span>
        </button>
      </div>
      <div id="cmpbody" style="margin-top:14px"></div>`,
  });

  const body = node.querySelector('#cmpbody');
  // Пока человек сам не выбрал неделю, она берётся из расписания. После
  // выбора его не перебиваем: иначе переключатель отщёлкивал бы назад.
  let weekPicked = false;

  const drawEmpty = () => {
    body.innerHTML = `<div class="card has-art" style="padding:20px">
      <div class="has-art-body">
        <div class="row-subtitle">
          Выбери вторую группу — покажу, в какие дни у вас общие пары и
          когда вы оба свободны.
        </div>
      </div>
      ${artState('group', '', '')}
    </div>`;
  };

  const drawAll = async () => {
    body.innerHTML = skeleton(160);
    let mine;
    let theirs;
    try {
      // Оба запроса сразу: последовательно это два ожидания сети вместо
      // одного, а расписание второй группы у бота обычно уже в кеше.
      [mine, theirs] = await Promise.all([
        fetchSchedule(mineName), fetchSchedule(other),
      ]);
    } catch (err) {
      body.innerHTML = emptyState(err.message || 'Расписание не загрузилось', 'calendar');
      return;
    }

    // Неделю цикла считает расписание: семестр известен только ему, а
    // от него зависит, с какой недели цикл начался.
    if (!weekPicked) {
      week = weekOfCycle(now, mine.semestr, settings.weekShift);
      weekPicked = true;
    }
    const perDay = weekTogether(mine, theirs, week);
    const weekTotal = perDay.reduce((n, d) => n + (d ? d.together : 0), 0);
    const cmp = perDay[day] || { rows: [], together: 0, both: 0, free: 0 };

    body.innerHTML = `
      ${pillRow([0, 1, 2, 3].map(w => ({ id: String(w), label: `${w + 1}-я неделя` })),
    String(week), 'cmpweek')}

      <div class="cmp-sum">
        <div class="cmp-sum-num">${weekTotal}</div>
        <div class="cmp-sum-text">
          ${weekTotal ? 'общих пар на этой неделе цикла' : 'общих пар на этой неделе нет'}
          <span>${esc(mineName)} и ${esc(other)}</span>
        </div>
      </div>

      <div class="week-strip" id="cmpdays">
        ${[1, 2, 3, 4, 5, 6].map(d => {
    const c = perDay[d];
    return `
          <button class="week-day ${d === day ? 'active' : ''}" data-cmpday="${d}">
            <span class="week-day-name">${DAY_SHORT[d]}</span>
            <span class="cmp-day-num ${c && c.together ? 'hot' : ''}">
              ${c && c.together ? c.together : '·'}
            </span>
          </button>`;
  }).join('')}
      </div>

      <div class="section-head" style="margin-top:14px">
        <div class="section-title">${DAY_NAMES[day]}</div>
      </div>

      ${cmp.rows.length ? `
        <div class="cmp-counts">
          <div><b>${cmp.together}</b><span>вместе</span></div>
          <div><b>${cmp.both}</b><span>у каждого своё</span></div>
          <div><b>${cmp.free}</b><span>окно у обоих</span></div>
        </div>
        <div class="cmp-list">
          ${cmp.rows.map(r => slotRow(r, mineName, other)).join('')}
        </div>`
    : `<div class="card">${artState('free', 'В этот день пар нет ни у кого',
      'Выбери другой день или неделю цикла')}</div>`}`;

    bindChoice(node, 'cmpweek', id => { week = +id; weekPicked = true; drawAll(); });
    body.querySelector('#cmpdays')?.addEventListener('click', e => {
      const b = e.target.closest('[data-cmpday]');
      if (!b) return;
      day = +b.dataset.cmpday;
      haptic('light');
      drawAll();
    });
  };

  node.addEventListener('click', e => {
    const pick = e.target.closest('[data-pick]');
    if (!pick) return;
    haptic('light');
    if (pick.dataset.pick === 'mine') {
      // Своя группа меняется здесь же: сравнивать чужую с чужой можно, но
      // тогда экран перестаёт отвечать на вопрос «когда МЫ встретимся».
      pickGroup(g => { save({ group: g }); location.reload(); });
      return;
    }
    pickGroup(g => {
      other = g;
      pick.querySelector('.cmp-pick-name').textContent = g;
      drawAll();
    });
  });

  if (other) drawAll();
  else drawEmpty();
  return node;
}
