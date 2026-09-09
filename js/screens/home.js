// Главная: что сейчас, расписание на сегодня, быстрые разделы, свежие новости.

import { icon } from '../icons.js';
import { esc, listCard, listRow } from '../ui.js';
import { data, settings } from '../store.js';
import { fetchSchedule, weekOfCycle, nowState, slotsOf, semesterStart, DAY_NAMES }
  from '../schedule.js';
import { go, switchTab } from '../router.js';
import { tgUser, openLink } from '../tg.js';
import { get, canTalk } from '../api.js';
import { screen, pickGroup, newsRow, humanDate, iconBtn } from './common.js';
import { lessonRow } from './schedule.js';
import { feedRow } from './feed.js';
import { flatten, pendingOf, subjectLook } from './tasks.js';
import { art, artState } from '../art.js';

// ОРИОКС и личный кабинет — внешние сервисы, но студенту они нужнее
// всего, поэтому стоят прямо на главной.
const QUICK = [
  { id: 'url:https://orioks.miet.ru/main/login', ico: 'chart', label: 'ОРИОКС' },
  { id: 'teachers', ico: 'teacher', label: 'Преподаватели' },
  { id: 'tasks', ico: 'backpack', label: 'Задания' },
  { id: 'url:https://account.miet.ru/', ico: 'key', label: 'Кабинет' },
  { id: 'campus:canteen', ico: 'utensils', label: 'Столовая' },
  { id: 'campus:library', ico: 'book', label: 'Библиотека' },
  { id: 'clubs', ico: 'sparkles', label: 'Кружки' },
  { id: 'useful-tab', ico: 'grid', label: 'Всё полезное' },
];

export default async function home() {
  const user = tgUser();
  const now = new Date();

  const node = screen({
    // Заголовок называет приложение, а не здоровается: «Привет, Дима»
    // человек читает один раз, а потом оно просто занимает верх экрана.
    // Имя осталось в приветственной карточке для тех, кто здесь впервые.
    title: 'НИУ МИЭТ',
    subtitle: 'Расписание, новости и жизнь университета',
    actions: iconBtn('search', 'search') + iconBtn('user', 'profile'),
    body: `
      <div id="hello-slot"></div>
      <div id="now-slot" class="stack"></div>
      <div id="study-slot"></div>

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
      <div class="list-card" id="fresh">
        ${(data.news || []).slice(0, 4).map(newsRow).join('')}
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

  // ── знакомство ──
  renderHello(node.querySelector('#hello-slot'), user);

  // ── карточка «сейчас» ──
  const slot = node.querySelector('#now-slot');
  renderNow(slot, now);

  // ── ближайшие дела из ОРИОКС ──
  renderStudy(node.querySelector('#study-slot'));

  // ── свежее из ленты ──
  // Пока сервер не ответил, на месте блока лежит архив из data/app.json:
  // он всегда под рукой и не оставляет главную пустой.
  renderFresh(node.querySelector('#fresh'));

  // ── обработчики ──
  node.querySelector('[data-action="search"]')?.addEventListener('click', () => go('search'));
  // Профиль перестал быть вкладкой, но с главной до него должно быть
  // одно нажатие: там группа, тема и всё своё.
  node.querySelector('[data-action="profile"]')?.addEventListener('click', () => go('profile'));
  node.addEventListener('click', e => {
    const q = e.target.closest('[data-quick]');
    if (q) {
      const raw = q.dataset.quick;
      if (raw.startsWith('url:')) return openLink(raw.slice(4));
      if (raw === 'useful-tab') return switchTab('useful');
      const [route, id] = raw.split(':');
      return go(route === 'campus' && id ? 'campusItem' : route, { id });
    }
    // Запись из ленты целиком читается там же — на главной только повод
    // туда заглянуть, поэтому ведём на вкладку, а не на отдельный экран.
    if (e.target.closest('[data-study]')) return go('tasks');
    if (e.target.closest('[data-feed]')) return switchTab('news');
    const n = e.target.closest('[data-news]');
    if (n) return go('article', { id: n.dataset.news });
    const g = e.target.closest('[data-go]');
    if (g) return switchTab(g.dataset.go);
    const row = e.target.closest('.list-row[data-id]');
    if (row) return go(row.dataset.id);
  });

  return node;
}

// Карточку «что это такое» человек читает один раз. Дальше она мешает:
// главная нужна, чтобы за две секунды увидеть свою пару.
const HELLO_KEY = 'miet-hello-seen';

/**
 * Короткий рассказ о приложении — только тем, кто здесь впервые, и
 * ровно до первого «Понятно».
 */
function renderHello(slot, user) {
  if (!slot) return;
  let seen = false;
  try {
    seen = localStorage.getItem(HELLO_KEY) === '1';
  } catch { /* приватный режим — покажем ещё раз, не страшно */ }
  if (seen) return;

  const name = user?.first_name ? `${user.first_name}, привет` : 'Привет';
  slot.innerHTML = `
    <div class="card hello">
      <div class="hello-title">${esc(name)}</div>
      <div class="hello-text">
        Это неофициальное приложение студентов МИЭТ. Здесь расписание твоей
        группы с живого сайта, лента новостей и объявлений, справочник
        преподавателей и аудиторий, кружки и всё, что обычно приходится
        искать по чатам.
      </div>
      <div class="hello-list">
        ${[
      ['calendar', 'Расписание', 'Пары на сегодня и всю неделю цикла'],
      ['news', 'Лента', 'Новости университета и объявления'],
      ['teacher', 'Преподаватели', 'Кто ведёт, где и с какими группами'],
      ['grid', 'Полезное', 'Баллы, кураторы, контакты, помощь с заданиями'],
    ].map(([ico, title, sub]) => `
          <div class="hello-row">
            <span class="hello-ico">${icon(ico, 17)}</span>
            <span><b>${esc(title)}</b> — ${esc(sub)}</span>
          </div>`).join('')}
      </div>
      <button class="btn-primary" id="hello-ok">Понятно</button>
    </div>`;

  slot.querySelector('#hello-ok').addEventListener('click', () => {
    try { localStorage.setItem(HELLO_KEY, '1'); } catch { /* не критично */ }
    slot.innerHTML = '';
  });
}

// Один обход ОРИОКС — это восемь запросов к серверу института, и идут
// они секундами. На главную возвращаются по десять раз за день, поэтому
// ответ живёт несколько минут: задания за это время не меняются, а
// институт не получает обход на каждое переключение вкладки.
let studyCache = null;
const STUDY_TTL = 5 * 60 * 1000;

const stillFresh = hit =>
  (hit && Date.now() - hit.at < STUDY_TTL ? hit.data : null);

/**
 * Ближайшие дела из ОРИОКС — три строки под расписанием.
 *
 * Экран «Задания» знает про них всё, но открывают его, когда про
 * задание и так вспомнили. Главную открывают просто так, по дороге на
 * пару, — и здесь ближайший срок стоит ровно там, где на него смотрят.
 *
 * Молча и последним: ОРИОКС отвечает секундами (обход всех дисциплин),
 * и задерживать из-за него расписание нельзя. Не подключён, не ответил,
 * нечего показать — блока просто нет, а звать подключаться на главной
 * незачем: для этого есть плитка «Задания».
 */
async function renderStudy(slot) {
  if (!slot || !canTalk || !settings.group) return;

  let data = stillFresh(studyCache);
  if (!data) {
    try {
      data = await get('/api/orioks', { timeout: 25000, retries: 0 });
    } catch { return; }
    studyCache = { at: Date.now(), data };
  }
  if (!data.linked || data.error || !data.tasks) return;

  let sched = null;
  let start = null;
  try {
    sched = await fetchSchedule(settings.group);
    start = semesterStart(sched.semestr);
  } catch { /* без расписания останутся недели вместо дней */ }

  // Три ближайших несданных. Больше — уже список дел, а он на своём
  // экране; здесь нужно только «что горит».
  const soon = pendingOf(flatten(data.tasks, sched, start, settings.weekShift))
    .slice(0, 3);
  if (!soon.length) return;

  slot.innerHTML = `
    <div class="section-head">
      <div class="section-title with-icon">${icon('backpack', 17)} Ближайшее</div>
      <button class="section-link" data-study="all">Все задания</button>
    </div>
    <div class="stack">${soon.map(studyRow).join('')}</div>`;
}

/** Строка дела: предмет виден значком, срок — словами, а не неделей. */
const studyRow = t => {
  const look = subjectLook(t.subject);
  const when = t.due
    ? `${WEEKDAYS_SHORT[t.due.getDay()]}, ${t.due.getDate()} ${MONTHS_SHORT[t.due.getMonth()]}`
    : `${t.week || '?'} нед`;
  const left = t.left === null ? ''
    : t.left < 0 ? 'просрочено'
      : t.left === 0 ? 'сегодня'
        : t.left === 1 ? 'завтра'
          : t.left < 7 ? `через ${t.left} дн`
            : `через ${Math.round(t.left / 7)} нед`;
  return `
    <button class="study-row ${esc(t.bucket)}" data-study="${t.idx}">
      <span class="study-badge tone-${look.tone}">${icon(look.glyph, 19)}</span>
      <span class="study-main">
        <span class="study-subject">${esc(t.subject)}</span>
        <span class="study-what">${esc(t.title.main)}</span>
      </span>
      <span class="study-when">
        <span class="study-day">${esc(when)}</span>
        <span class="study-left">${esc(left)}</span>
      </span>
    </button>`;
};

// Короткие подписи: в строку с предметом и сроком полные названия не
// влезают, а «ср, 10 сент» читается с одного взгляда.
const WEEKDAYS_SHORT = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
const MONTHS_SHORT = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн',
  'июл', 'авг', 'сент', 'окт', 'нояб', 'дек'];


/**
 * Свежее из ленты — четыре записи. Тоже асинхронно и молча: сервер здесь
 * необязателен, а падать главной из-за новостей незачем.
 */
async function renderFresh(slot) {
  if (!slot || !canTalk) return;
  try {
    const feed = await get('/api/feed?limit=4', { timeout: 6000, retries: 0 });
    if (feed.posts.length) slot.innerHTML = feed.posts.map(feedRow).join('');
  } catch { /* остаётся архив, который уже нарисован */ }
}

/** Рисует блок «что сейчас» — асинхронно, чтобы не задерживать экран. */
async function renderNow(slot, now) {
  if (!settings.group) {
    slot.innerHTML = `
      <div class="card has-art" style="padding:20px">
        <div class="now-kicker" style="color:var(--text-secondary)">Расписание</div>
        <div style="font-size:19px;font-weight:800;margin:8px 0 4px">Выбери свою группу</div>
        <div class="row-subtitle" style="margin-bottom:16px;max-width:210px">
          Покажу пары на сегодня, ближайшую и всю неделю
        </div>
        <button class="btn-primary" id="pick">Выбрать группу</button>
        ${art('group', 92, 'art-aside')}
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
    slot.innerHTML = `<div class="card">
        ${artState('offline', 'Расписание не загрузилось', err.message)}
      </div>`;
    return;
  }

  const week = weekOfCycle(now, sched.semestr, settings.weekShift);
  const { current, next, progress, day } = nowState(sched, week, now);
  const today = day <= 6 ? slotsOf(sched, week, day) : [];

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
      : `<div class="now-card rest has-art">
           <div class="now-kicker">${day > 6 ? 'Воскресенье' : 'На сегодня всё'}</div>
           <div class="now-title">Пар больше нет</div>
           <div class="now-meta muted">
             <span>${esc(settings.group)}</span><span>${week + 1}-я неделя цикла</span>
           </div>
           ${art(day > 6 ? 'rest' : 'done', 86, 'art-aside')}
         </div>`;

  slot.innerHTML = `
    ${card}
    <div class="section-head" style="margin-top:6px">
      <div class="section-title">${day <= 6 ? DAY_NAMES[day] : 'Расписание'}, ${humanDate(now).split(', ')[1]}</div>
      <button class="section-link" data-go="schedule">Вся неделя</button>
    </div>
    ${today.length
      ? `<div class="stack">${today.map(l => lessonRow(l, now)).join('')}</div>`
      : `<div class="card">${day > 6
        ? artState('rest', 'Воскресенье — выходной',
          'Расписание всей недели цикла — на своей вкладке')
        : artState('free', 'В этот день пар нет',
          'Свободно: можно закрыть хвосты или выдохнуть')}</div>`}`;
}
