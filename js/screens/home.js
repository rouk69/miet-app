// Главная: что сейчас, расписание на сегодня, быстрые разделы, свежие новости.

import { icon } from '../icons.js';
import { esc, listCard, listRow, emptyState } from '../ui.js';
import { data, settings } from '../store.js';
import { fetchSchedule, weekOfCycle, nowState, lessonsOf, DAY_NAMES } from '../schedule.js';
import { go, switchTab } from '../router.js';
import { tgUser, openLink } from '../tg.js';
import { screen, pickGroup, newsRow, humanDate, iconBtn } from './common.js';
import { lessonRow } from './schedule.js';

// ОРИОКС и личный кабинет — внешние сервисы, но студенту они нужнее
// всего, поэтому стоят прямо на главной.
const QUICK = [
  { id: 'url:https://orioks.miet.ru/main/login', ico: 'chart', label: 'ОРИОКС' },
  { id: 'url:https://account.miet.ru/', ico: 'key', label: 'Кабинет' },
  { id: 'campus:canteen', ico: 'utensils', label: 'Столовая' },
  { id: 'campus:library', ico: 'book', label: 'Библиотека' },
  { id: 'campus:dorm', ico: 'homes', label: 'Общежития' },
  { id: 'campus:scholarship', ico: 'wallet', label: 'Стипендии' },
  { id: 'links', ico: 'link', label: 'Ссылки' },
  { id: 'campus', ico: 'compass', label: 'Все разделы' },
];

export default async function home() {
  const user = tgUser();
  const name = user?.first_name ? `Привет, ${user.first_name}` : 'МИЭТ';
  const now = new Date();

  const node = screen({
    title: name,
    subtitle: humanDate(now),
    actions: iconBtn('search', 'search'),
    body: `
      <div id="now-slot" class="stack"></div>

      <div class="section-head"><div class="section-title">Разделы</div></div>
      <div class="quick-grid">
        ${QUICK.map(q => `<button class="quick-item" data-quick="${q.id}">
            <span class="quick-icon">${icon(q.ico, 21)}</span>
            <span class="quick-label">${esc(q.label)}</span>
          </button>`).join('')}
      </div>

      <div class="section-head">
        <div class="section-title">Новости</div>
        <button class="section-link" data-go="news">Все</button>
      </div>
      <div class="list-card">
        ${(data.news || []).slice(0, 5).map(newsRow).join('')}
      </div>

      <div class="section-head"><div class="section-title">Университет</div></div>
      <div class="kpi-grid">
        ${(data.university?.facts || []).map(f =>
    `<div class="kpi-tile"><div class="kpi-number">${esc(f.k)}</div>
           <div class="kpi-label">${esc(f.v)}</div></div>`).join('')}
      </div>
      <div style="margin-top:10px">
        ${listCard([
      listRow({ ico: 'landmark', title: 'О МИЭТ', sub: 'История, факты, контакты', chevron: true, id: 'about', cls: 'tap' }),
      listRow({ ico: 'graduate', title: 'Институты', sub: `${(data.institutes || []).length} подразделений`, chevron: true, id: 'institutes', cls: 'tap' }),
      listRow({ ico: 'lifebuoy', title: 'Поддержка', sub: 'Автор приложения', chevron: true, id: 'support', cls: 'tap' }),
    ])}
      </div>

      <div class="fab-note">Данные с miet.ru · обновлено ${esc(data.meta?.generated || '')}</div>`,
  });

  // ── карточка «сейчас» ──
  const slot = node.querySelector('#now-slot');
  renderNow(slot, now);

  // ── обработчики ──
  node.querySelector('[data-action="search"]')?.addEventListener('click', () => go('search'));
  node.addEventListener('click', e => {
    const q = e.target.closest('[data-quick]');
    if (q) {
      const raw = q.dataset.quick;
      if (raw.startsWith('url:')) return openLink(raw.slice(4));
      const [route, id] = raw.split(':');
      return go(route === 'campus' && id ? 'campusItem' : route, { id });
    }
    const n = e.target.closest('[data-news]');
    if (n) return go('article', { id: n.dataset.news });
    const g = e.target.closest('[data-go]');
    if (g) return switchTab(g.dataset.go);
    const row = e.target.closest('.list-row[data-id]');
    if (row) return go(row.dataset.id);
  });

  return node;
}

/** Рисует блок «что сейчас» — асинхронно, чтобы не задерживать экран. */
async function renderNow(slot, now) {
  if (!settings.group) {
    slot.innerHTML = `
      <div class="card" style="padding:20px">
        <div class="now-kicker" style="color:var(--text-secondary)">Расписание</div>
        <div style="font-size:19px;font-weight:800;margin:8px 0 4px">Выбери свою группу</div>
        <div class="row-subtitle" style="margin-bottom:16px">
          Покажу пары на сегодня, ближайшую и всю неделю
        </div>
        <button class="btn-primary" id="pick">Выбрать группу</button>
      </div>`;
    slot.querySelector('#pick').addEventListener('click', () =>
      pickGroup(() => location.reload()));
    return;
  }

  slot.innerHTML = `<div class="skeleton" style="height:132px"></div>`;
  let sched;
  try {
    sched = await fetchSchedule(settings.group);
  } catch (err) {
    slot.innerHTML = `<div class="card" style="padding:18px">
        <div class="row-title">Расписание не загрузилось</div>
        <div class="row-subtitle" style="margin-top:4px">${esc(err.message)}</div>
      </div>`;
    return;
  }

  const week = weekOfCycle(now, sched.semestr, settings.weekShift);
  const { current, next, progress, day } = nowState(sched, week, now);
  const today = day <= 6 ? lessonsOf(sched, week, day) : [];

  const card = current
    ? `<div class="now-card">
         <div class="now-kicker">Сейчас идёт</div>
         <div class="now-title">${esc(current.subject)}</div>
         <div class="now-meta">
           <span>${icon('clock', 15)} ${esc(current.from)}–${esc(current.to)}</span>
           ${current.room ? `<span>${icon('door', 15)} ${esc(current.room)}</span>` : ''}
           ${current.teacherShort ? `<span>${icon('teacher', 15)} ${esc(current.teacherShort)}</span>` : ''}
         </div>
         <div class="now-progress"><i style="width:${Math.round(progress * 100)}%"></i></div>
       </div>`
    : next
      ? `<div class="now-card">
           <div class="now-kicker">Следующая пара</div>
           <div class="now-title">${esc(next.subject)}</div>
           <div class="now-meta">
             <span>${icon('clock', 15)} в ${esc(next.from)}</span>
             ${next.room ? `<span>${icon('door', 15)} ${esc(next.room)}</span>` : ''}
             ${next.teacherShort ? `<span>${icon('teacher', 15)} ${esc(next.teacherShort)}</span>` : ''}
           </div>
         </div>`
      : `<div class="now-card rest">
           <div class="now-kicker">${day > 6 ? 'Воскресенье' : 'На сегодня всё'}</div>
           <div class="now-title">Пар больше нет</div>
           <div class="now-meta muted">
             <span>${esc(settings.group)}</span><span>${week + 1}-я неделя цикла</span>
           </div>
         </div>`;

  slot.innerHTML = `
    ${card}
    <div class="section-head" style="margin-top:6px">
      <div class="section-title">${day <= 6 ? DAY_NAMES[day] : 'Расписание'}</div>
      <button class="section-link" data-go="schedule">Вся неделя</button>
    </div>
    ${today.length
      ? `<div class="stack">${today.map(l => lessonRow(l, now)).join('')}</div>`
      : emptyState(day > 6 ? 'Воскресенье — выходной' : 'В этот день пар нет', 'clock')}`;
}
