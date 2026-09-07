// Преподаватели и аудитории: поиск по расписанию всего университета.
//
// miet.ru отвечает только на вопрос «что у группы», поэтому «где сейчас
// Иванов» и «что идёт в 3105» собирает сервер (bot/directory.py) — раз в
// сутки обходит все группы и складывает плоский индекс. Здесь только
// показ найденного.

import { icon } from '../icons.js';
import { esc, emptyState } from '../ui.js';
import { get, canTalk } from '../api.js';
import { go } from '../router.js';
import { settings } from '../store.js';
import { screen } from './common.js';
import { DAY_NAMES } from '../schedule.js';

const KIND_NAMES = { lek: 'лекция', pr: 'практика', lab: 'лаборатор.', oth: '' };

/** Пара в списке: время, предмет, где и с кем. */
const slotRow = (s, showTeacher) => `
  <div class="lesson">
    <div class="lesson-time">
      <div class="lesson-from">${esc(s.from || '')}</div>
      <div class="lesson-to">${esc(s.to || '')}</div>
    </div>
    <div class="lesson-body">
      <div class="lesson-name">${esc(s.subject || 'Занятие')}</div>
      <div class="lesson-meta">
        ${s.kind && KIND_NAMES[s.kind]
    ? `<span class="kind ${esc(s.kind)}">${KIND_NAMES[s.kind]}</span>` : ''}
        ${showTeacher && s.teacher
    ? `<span>${icon('teacher', 14)} ${esc(s.teacher)}</span>` : ''}
        ${s.room ? `<span>${icon('door', 14)} ${esc(s.room)}</span>` : ''}
        <span>${icon('users', 14)} ${esc(s.groups.join(', '))}</span>
      </div>
    </div>
  </div>`;

/**
 * Пары, разложенные по неделям цикла и дням. Плоский список из сорока
 * занятий читать невозможно, а «неделя 2, среда» — уже ответ.
 */
function timetable(slots, showTeacher) {
  const weeks = [[], [], [], []];
  slots.forEach(s => weeks[s.week % 4]?.push(s));
  return weeks.map((week, i) => {
    if (!week.length) return '';
    const days = {};
    week.forEach(s => (days[s.day] = days[s.day] || []).push(s));
    return `
      <div class="section-head"><div class="section-title">${i + 1}-я неделя</div></div>
      ${Object.keys(days).sort().map(d => `
        <div class="day-block">
          <div class="day-name">${esc(DAY_NAMES[d] || 'День ' + d)}</div>
          <div class="stack">${days[d].map(s => slotRow(s, showTeacher)).join('')}</div>
        </div>`).join('')}`;
  }).join('');
}

// ─────────────── список ───────────────

export default async function directoryScreen({ mode = 'teachers' } = {}) {
  const rooms = mode === 'rooms';

  if (!canTalk) {
    return screen({
      title: rooms ? 'Аудитории' : 'Преподаватели',
      body: emptyState('Справочник работает внутри Telegram', 'teacher'),
    });
  }

  const node = screen({
    title: rooms ? 'Аудитории' : 'Преподаватели',
    subtitle: rooms ? 'Что и когда идёт в кабинете'
      : 'Кто ведёт, где и с какими группами',
    body: `
      <div class="search-box" style="margin-bottom:12px">
        ${icon('search', 19, 'muted')}
        <input id="dq" type="search" autocomplete="off" spellcheck="false"
               placeholder="${rooms ? 'Например, 3105' : 'Фамилия преподавателя'}">
      </div>
      <div id="dlist"><div class="skeleton" style="height:140px"></div></div>
      <div class="fab-note" id="dnote"></div>`,
  });

  const list = node.querySelector('#dlist');
  const note = node.querySelector('#dnote');

  const draw = async q => {
    try {
      const r = await get(`/api/directory/${rooms ? 'rooms' : 'teachers'}`
        + `?q=${encodeURIComponent(q)}`);
      const items = rooms ? r.rooms : r.teachers;
      list.innerHTML = items.length
        ? `<div class="list-card">${items.map(x => `
            <div class="list-row tap" data-name="${esc(x.name)}">
              <div class="icon-tile">${icon(rooms ? 'door' : 'teacher', 19)}</div>
              <div class="list-row-body">
                <div class="row-title">${esc(x.name)}</div>
                <div class="row-subtitle">
                  ${x.lessons} ${plural(x.lessons, 'пара', 'пары', 'пар')} в цикле${
  rooms ? '' : ` · ${x.groups} ${plural(x.groups, 'группа', 'группы', 'групп')}`}
                </div>
              </div>
              <span class="chevron">${icon('chevronRight', 18)}</span>
            </div>`).join('')}</div>`
        : emptyState(q ? 'Ничего не нашлось' : 'Справочник ещё собирается', 'search');
      note.innerHTML = r.meta?.built_at
        ? `По расписанию ${esc(r.meta.semestr || '')} · обновлено ${esc(when(r.meta.built_at))}`
        : 'Справочник собирается — обычно это занимает несколько минут после запуска бота.';
    } catch (err) {
      list.innerHTML = `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`;
    }
  };

  draw('');

  let timer = null;
  node.querySelector('#dq').addEventListener('input', e => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    timer = setTimeout(() => draw(q), 250);
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-name]');
    if (row) go(rooms ? 'room' : 'teacher', { name: row.dataset.name });
  });

  return node;
}

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

/** Когда собран индекс — «сегодня» понятнее, чем «2026-09-07 03:00». */
function when(ts) {
  const d = new Date(String(ts).replace(' ', 'T') + 'Z');
  const hours = Math.floor((Date.now() - d.getTime()) / 3600000);
  if (hours < 1) return 'только что';
  if (hours < 24) return `${hours} ч назад`;
  return d.toLocaleDateString('ru-RU');
}

// ─────────────── карточка ───────────────

export async function teacherScreen({ name }) {
  return card(name, false);
}

export async function roomScreen({ name }) {
  return card(name, true);
}

async function card(name, rooms) {
  let found;
  try {
    found = await get(`/api/directory/${rooms ? 'room' : 'teacher'}`
      + `?name=${encodeURIComponent(name)}`);
  } catch (err) {
    return screen({ title: name, body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const mine = settings.group
    ? found.slots.filter(s => s.groups.includes(settings.group))
    : [];

  return screen({
    title: name,
    subtitle: rooms
      ? `${found.slots.length} ${plural(found.slots.length, 'пара', 'пары', 'пар')} в цикле`
      : found.subjects.slice(0, 3).join(' · '),
    body: `
      <div class="kpi-grid">
        ${kpiTile(found.slots.length, 'Пар в цикле')}
        ${rooms
    ? kpiTile(found.teachers.length, 'Преподавателей')
    : kpiTile(found.groups.length, 'Групп')}
      </div>

      ${mine.length ? `
        <div class="section-head"><div class="section-title">У твоей группы</div></div>
        <p class="section-note">${esc(settings.group)} — ${mine.length}
          ${plural(mine.length, 'пара', 'пары', 'пар')} в цикле</p>
        <div class="stack">${mine.map(s => slotRow(s, !rooms)).join('')}</div>` : ''}

      ${!rooms && found.rooms.length ? `
        <div class="section-head"><div class="section-title">Аудитории</div></div>
        <div class="chip-row">${found.rooms.map(r =>
      `<span class="chip">${esc(r)}</span>`).join('')}</div>` : ''}

      ${rooms && found.teachers.length ? `
        <div class="section-head"><div class="section-title">Кто ведёт</div></div>
        <div class="chip-row">${found.teachers.map(t =>
      `<span class="chip">${esc(t)}</span>`).join('')}</div>` : ''}

      <div class="section-head"><div class="section-title">Всё расписание</div></div>
      ${timetable(found.slots, !rooms)}`,
  });
}

const kpiTile = (n, label) =>
  `<div class="kpi-tile"><div class="kpi-number">${n}</div>
   <div class="kpi-label">${esc(label)}</div></div>`;
