// Разбор статистики по дням: не «сколько», а «кто именно и когда».
//
// Дневные графики в сводке отвечают на вопрос «растёт ли», но не
// отвечают на «что было во вторник». Здесь наоборот: выбираешь день —
// видишь список людей, время первого и последнего касания и чем они
// занимались.

import { icon } from '../icons.js';
import { esc, emptyState, listCard } from '../ui.js';
import { get } from '../api.js';
import { go } from '../router.js';
import { haptic, openLink } from '../tg.js';
import { screen } from './common.js';

const KIND_NAMES = {
  open: 'Заходы в приложение', tab: 'Переключения вкладок',
  screen: 'Открытия экранов', bot: 'Обращения к боту',
};

const TAB_NAMES = {
  home: 'Главная', schedule: 'Расписание', news: 'Лента', useful: 'Полезное',
  clubs: 'Кружки', profile: 'Профиль',
};

const dayLabel = iso => `${iso.slice(8, 10)}.${iso.slice(5, 7)}`;

const WEEK = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
const weekdayOf = iso => WEEK[new Date(iso + 'T12:00:00Z').getUTCDay()];

/**
 * Полоса часов суток. Двадцать четыре столбика читаются с одного взгляда
 * и отвечают на вопрос, в какое время писать объявление.
 */
function hoursStrip(hours) {
  const max = Math.max(1, ...hours.map(h => h.count));
  return `
    <div class="hours">
      ${hours.map(h => `
        <div class="hour-col" title="${h.hour}:00 — ${h.count}">
          <div class="hour-bar" style="height:${Math.round(h.count / max * 100)}%"></div>
          <div class="hour-tick">${h.hour % 6 === 0 ? h.hour : ''}</div>
        </div>`).join('')}
    </div>`;
}

export default async function adminDaysScreen({ date } = {}) {
  if (date) return dayScreen(date);

  let list;
  try {
    list = await get('/api/admin/days?days=30');
  } catch (err) {
    return screen({ title: 'По дням', body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const days = [...list.days].reverse();      // свежие сверху
  const max = Math.max(1, ...days.map(d => d.actions));

  const node = screen({
    title: 'По дням',
    subtitle: 'Выбери день — увидишь, кто в нём был',
    body: days.some(d => d.actions) ? `
      <div class="list-card">
        ${days.map(d => `
          <div class="list-row tap" data-date="${d.date}">
            <div class="list-row-body">
              <div class="row-title">
                ${esc(dayLabel(d.date))} · ${esc(weekdayOf(d.date))}
              </div>
              <div class="row-subtitle">
                ${d.people} ${plural(d.people, 'человек', 'человека', 'человек')} ·
                ${d.actions} ${plural(d.actions, 'действие', 'действия', 'действий')}
              </div>
            </div>
            <div class="day-bar">
              <i style="width:${Math.round(d.actions / max * 100)}%"></i>
            </div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>`).join('')}
      </div>`
      : emptyState('Пока нечего разбирать — событий не было', 'calendar'),
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-date]');
    if (row) {
      haptic('light');
      go('adminDay', { date: row.dataset.date });
    }
  });
  return node;
}

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

export async function dayScreen({ date }) {
  let day;
  try {
    day = await get(`/api/admin/day?date=${encodeURIComponent(date)}`);
  } catch (err) {
    return screen({ title: date, body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const total = Object.values(day.kinds).reduce((a, b) => a + b, 0);

  const node = screen({
    title: `${dayLabel(day.date)} · ${weekdayOf(day.date)}`,
    subtitle: `${day.people.length} ${plural(day.people.length, 'человек', 'человека', 'человек')}, ${total} ${plural(total, 'действие', 'действия', 'действий')}`,
    body: `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${day.people.length}</div>
          <div class="kpi-label">Были в этот день</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${day.newcomers}</div>
          <div class="kpi-label">Пришли впервые</div>
        </div>
      </div>

      <div class="section-head"><div class="section-title">Часы</div></div>
      <p class="section-note">Когда именно заходили — по московскому времени.</p>
      <div class="card" style="padding:14px">${hoursStrip(day.hours)}</div>

      ${Object.keys(day.kinds).length ? `
        <div class="section-head"><div class="section-title">Что делали</div></div>
        ${listCard(Object.entries(day.kinds).map(([k, n]) => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(KIND_NAMES[k] || k)}</div>
            </div>
            <div class="list-row-value tnum">${n}</div>
          </div>`))}` : ''}

      ${day.tabs.length ? `
        <div class="section-head"><div class="section-title">Разделы этого дня</div></div>
        ${listCard(day.tabs.map(t => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(TAB_NAMES[t.name] || t.name)}</div>
            </div>
            <div class="list-row-value tnum">${t.count}</div>
          </div>`))}` : ''}

      <div class="section-head"><div class="section-title">Кто был</div></div>
      <p class="section-note">Тапни, чтобы открыть карточку человека.</p>
      ${day.people.length ? `<div class="list-card">
        ${day.people.map(p => `
          <div class="list-row tap" data-user="${p.id}">
            <div class="list-row-body">
              <div class="row-title">
                ${esc(p.name)}${p.username ? ` · <span class="muted-name">@${esc(p.username)}</span>` : ''}
              </div>
              <div class="row-subtitle">
                ${esc(p.first_at?.slice(0, 5) || '')}–${esc(p.last_at?.slice(0, 5) || '')}
                ${p.group ? ` · ${esc(p.group)}` : ''}
                ${p.bot ? ` · бот: ${p.bot}` : ''}
              </div>
            </div>
            <div class="list-row-value tnum">${p.actions}</div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>`).join('')}
      </div>` : emptyState('В этот день никого не было', 'users')}`,
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-user]');
    if (row) go('adminUser', { id: +row.dataset.user });
  });
  return node;
}

export { hoursStrip, plural, KIND_NAMES, TAB_NAMES, dayLabel, weekdayOf };
void openLink;
