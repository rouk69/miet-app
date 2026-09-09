// Задания из ОРИОКС — список дел, а не выгрузка данных.
//
// Первая версия показывала всё подряд, сгруппированное по предметам, и
// была нечитаемой: у студента шесть-восемь дисциплин по пять-десять
// контрольных мероприятий в каждой, то есть полсотни строк, в которых
// не видно главного — что делать в ближайшие дни.
//
// Поэтому здесь один список, отсортированный по сроку и разбитый на
// «просрочено / эта неделя / следующая / потом». Предмет крупно, тип
// задания мелко: человек ищет глазами «Матанализ», а не «ДЗ №2».
// Сданное убрано вниз и свёрнуто — оно уже не дело.

import { icon } from '../icons.js';
import { esc, emptyState, toast, sheet, toggle } from '../ui.js';
import { get, post, account, canTalk } from '../api.js';
import { settings } from '../store.js';
import { fetchSchedule, semesterStart, mondayOf, weekOfCycle }
  from '../schedule.js';
import { refresh } from '../router.js';
import { hapticNotify, haptic, confirmDialog, openLink } from '../tg.js';
import { screen } from './common.js';

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

const WEEKDAYS = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];

/**
 * Понедельник учебной недели N.
 *
 * Считать от самой даты начала семестра нельзя: 1 сентября бывает
 * вторником, и тогда вторая неделя съезжала на день вперёд — ОРИОКС
 * показывал вторую, а приложение считало её концом четырнадцатое.
 * Недели везде начинаются с понедельника, и здесь тоже.
 */
export function weekMonday(start, week) {
  if (!start || !week) return null;
  const d = mondayOf(start);
  d.setDate(d.getDate() + (week - 1) * 7);
  return d;
}

/** Конец учебной недели N — крайний срок, если пары найти не удалось. */
function dueDate(start, week) {
  const d = weekMonday(start, week);
  if (d) d.setDate(d.getDate() + 6);
  return d;
}

// Тип мероприятия ОРИОКС → тип пары в расписании. Лабораторную сдают
// на лабораторной, контрольную пишут на практике: это не догадка, а
// то, как устроено занятие.
const KIND_TO_CLASS = [
  [/лаборатор/i, 'lab'],
  [/практич|контрольн|коллоквиум|тест|семинар|деловая игра|кейс/i, 'pr'],
  [/лекц/i, 'lek'],
];

/** Слова названия, по которым предмет узнаётся в другом источнике. */
export function subjectKey(name) {
  return String(name || '').toLowerCase()
    .replace(/[«»"'()]/g, ' ')
    .split(/[\s.,;:—–-]+/)
    .filter(w => w.length >= 5)
    .slice(0, 2)
    .join(' ');
}

/**
 * День пары, на которой это мероприятие сдают.
 *
 * ОРИОКС знает только номер недели, а человек живёт днями: «лаба на
 * второй неделе» и «лаба завтра» — про одно и то же, но понятно
 * второе. Ищем в расписании пару нужного предмета и вида на этой
 * неделе; если их несколько, берём последнюю — крайний срок.
 */
export function lessonDay(sched, start, event, discipline, shift) {
  if (!sched || !start || !event.week) return null;
  const monday = weekMonday(start, event.week);
  if (!monday) return null;

  const cycle = weekOfCycle(monday, sched.semestr, shift);
  const want = (KIND_TO_CLASS.find(([re]) => re.test(event.type || '')) || [])[1];
  const key = subjectKey(discipline);
  if (!key) return null;

  const sameWeek = (sched.lessons || []).filter(
    l => l.week === cycle && subjectKey(l.subject) === key);
  const exact = want ? sameWeek.filter(l => l.kindCls === want) : [];
  // Копия перед сортировкой: pop() опустошал сам массив, и «нашли
  // именно лабораторную» превращалось в «нашли хоть что-нибудь»
  // ровно в тот момент, когда это проверялось.
  const found = (exact.length ? exact : sameWeek).slice()
    .sort((a, b) => a.day - b.day || a.pair - b.pair).pop();
  if (!found) return null;

  const d = new Date(monday.getTime());
  d.setDate(d.getDate() + found.day - 1);
  return { date: d, lesson: found, exact: exact.length > 0 };
}

const humanDate = d =>
  d ? `${d.getDate()} ${MONTHS[d.getMonth()]}, ${WEEKDAYS[d.getDay()]}` : '';

function daysLeft(due) {
  if (!due) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((due - today) / 86400000);
}

/**
 * Название задания у ОРИОКС бывает кодом: «dz.1», «КТ.2», иногда пустым.
 * Человеку нужен смысл, поэтому главным делаем тип («Домашнее задание»),
 * а код показываем рядом — по нему задание ищут уже в самом ОРИОКС.
 */
function titleOf(t) {
  const name = (t.name || '').trim();
  const type = (t.type || '').trim();
  const looksLikeCode = name.length <= 6 || /^[a-zA-Z.\d\s]+$/.test(name);
  if (type && looksLikeCode) return { main: type, note: name };
  return { main: name || type || 'Задание', note: type === name ? '' : type };
}

// Виды работ для фильтра. Ключ — то, что ищем в типе мероприятия;
// у ОРИОКС названия длинные («Большое домашнее задание»), поэтому
// сравниваем по куску, а не целиком.
const KINDS = [
  { id: 'all', label: 'Всё', match: () => true },
  { id: 'hw', label: 'Домашние', match: t => /домашн|индивидуал|расчет|расчёт|курсов|реферат/i.test(t) },
  { id: 'lab', label: 'Лабы', match: t => /лаборатор/i.test(t) },
  { id: 'test', label: 'Контрольные', match: t => /контрольн|тест|коллоквиум|самостоятельн/i.test(t) },
];

// Группы по срочности. Порядок здесь же задаёт порядок на экране.
const BUCKETS = [
  { id: 'late', title: 'Просрочено', note: 'Срок уже прошёл' },
  { id: 'now', title: 'На этой неделе', note: '' },
  { id: 'next', title: 'На следующей неделе', note: '' },
  { id: 'later', title: 'Потом', note: '' },
  { id: 'nodate', title: 'Без срока', note: 'ОРИОКС не указал неделю' },
];

function bucketOf(left) {
  if (left === null) return 'nodate';
  if (left < 0) return 'late';
  if (left <= 7) return 'now';
  if (left <= 14) return 'next';
  return 'later';
}

function leftLabel(left) {
  if (left === null) return '';
  if (left < 0) return `${-left} дн назад`;
  if (left === 0) return 'сегодня';
  if (left === 1) return 'завтра';
  if (left < 7) return `через ${left} дн`;
  return `через ${Math.round(left / 7)} нед`;
}

const taskRow = t => `
  <div class="todo ${t.bucket}">
    <div class="todo-main">
      <div class="todo-subject">${esc(t.subject)}</div>
      <div class="todo-what">
        ${esc(t.title.main)}${t.title.note ? ` · ${esc(t.title.note)}` : ''}
      </div>
      ${t.materials && t.materials.length ? `
        <button class="todo-files" data-files="${t.idx}">
          ${icon('fileText', 14)}
          ${t.materials.length === 1 ? 'Файл задания'
            : `Файлов: ${t.materials.length}`}
        </button>` : ''}
    </div>
    <div class="todo-side">
      <div class="todo-when">${esc(t.due ? humanDate(t.due) : `${t.week || '?'} нед`)}</div>
      <div class="todo-left">
        ${esc(leftLabel(t.left))}${t.max_grade ? ` · ${t.max_grade} б.` : ''}
      </div>
      ${t.lesson ? `<div class="todo-lesson">
        ${esc(t.lesson.from || '')}${t.lesson.room ? ` · ${esc(t.lesson.room)}` : ''}
      </div>` : ''}
    </div>
  </div>`;

// Значок предмета. Читать название дисциплины целиком в списке никто
// не будет — глаз цепляется за цвет и форму, и уже по ним объявление
// находится среди других.
const SUBJECT_ICONS = [
  [/физик|механик|термодинам/i, 'atom', 4],
  [/матем|анализ|алгебр|геометр/i, 'sigma', 0],
  [/информат|программ|вычислит/i, 'code', 5],
  [/истори|философ|культур|право/i, 'landmark', 3],
  [/язык|английск|лингв/i, 'languages', 2],
  [/физическ.*культур|спорт/i, 'medal', 1],
  [/командн|коммуникац|психолог/i, 'users', 2],
  [/хими|биолог/i, 'microscope', 1],
  [/эконом|менеджмент|финанс/i, 'wallet', 3],
];

export function subjectLook(name) {
  for (const [re, glyph, tone] of SUBJECT_ICONS) {
    if (re.test(name || '')) return { glyph, tone };
  }
  // Незнакомый предмет получает свой постоянный цвет, а не случайный:
  // при следующем открытии он должен выглядеть так же.
  let sum = 0;
  for (const ch of String(name || '')) sum = (sum + ch.charCodeAt(0)) % 997;
  return { glyph: 'bookOpen', tone: sum % 6 };
}

/** Дата ОРИОКС «03.09.2026 15:05» — в то, как о ней говорят вслух. */
export function newsDate(raw) {
  const m = /^(\d{2})\.(\d{2})\.(\d{4})(?:\s+(\d{2}):(\d{2}))?/.exec(raw || '');
  if (!m) return { text: raw || '', fresh: false };
  const [, d, mo, y, hh, mm] = m;
  const when = new Date(+y, +mo - 1, +d, +(hh || 0), +(mm || 0));
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((today - new Date(+y, +mo - 1, +d)) / 86400000);
  const clock = hh ? `${hh}:${mm}` : '';
  if (days === 0) return { text: clock ? `сегодня, ${clock}` : 'сегодня', fresh: true };
  if (days === 1) return { text: 'вчера', fresh: true };
  if (days > 1 && days < 7) return { text: `${days} дн. назад`, fresh: days <= 2 };
  return { text: `${+d} ${MONTHS[+mo - 1]}`, fresh: false, when };
}

const newsRow = n => {
  const look = subjectLook(n.discipline);
  const date = newsDate(n.date);
  return `
  <button class="notice-card tone-${look.tone}" data-news="${esc(n.href)}">
    <div class="notice-badge">${icon(look.glyph, 20)}</div>
    <div class="notice-main">
      <div class="notice-top">
        <span class="notice-subject">
          ${esc(n.discipline || (n.course ? 'Дисциплина' : 'Институт'))}
        </span>
        ${date.fresh ? '<span class="notice-fresh">новое</span>' : ''}
        <span class="notice-date">${esc(date.text)}</span>
      </div>
      <div class="notice-title">${esc(n.title)}</div>
      ${n.preview ? `<div class="notice-preview">${esc(n.preview)}</div>` : ''}
      <div class="notice-foot">
        ${n.author ? `${icon('user', 13)}<span>${esc(n.author)}</span>` : ''}
        <span class="notice-open">Читать ${icon('chevronRight', 13)}</span>
      </div>
    </div>
  </button>`;
};

// Что за файл — видно по значку раньше, чем прочитано название: у
// преподавателей они называются «Федотова_ТА_КРиДК_СР1_Деловое письмо».
export function fileLook(name, link) {
  const what = (name + ' ' + (link || '')).toLowerCase();
  if (/\.pdf(\?|$|%|\s)/.test(what)) return { glyph: 'fileText', label: 'PDF' };
  if (/\.docx?(\?|$|%|\s)/.test(what)) return { glyph: 'edit', label: 'DOC' };
  if (/\.xlsx?(\?|$|%|\s)/.test(what)) return { glyph: 'grid', label: 'Таблица' };
  if (/\.pptx?(\?|$|%|\s)/.test(what)) return { glyph: 'palette', label: 'Слайды' };
  if (/\.zip|\.rar|\.7z/.test(what)) return { glyph: 'folder', label: 'Архив' };
  if (/ссылк|http/.test(what)) return { glyph: 'link', label: 'Ссылка' };
  return { glyph: 'clipboard', label: '' };
}

const fileRow = f => {
  const look = fileLook(f.name, f.link);
  return `
  <button class="notice-card file-card" data-link="${esc(f.link)}">
    <div class="notice-badge">${icon(look.glyph, 19)}</div>
    <div class="notice-main">
      <div class="notice-title">${esc(f.name)}</div>
      <div class="notice-foot">
        <span>${esc(f.subject)}</span>
        ${look.label ? `<span class="file-kind">${esc(look.label)}</span>` : ''}
        <span class="notice-open">Открыть ${icon('external', 13)}</span>
      </div>
    </div>
  </button>`;
};

/**
 * Всё, что ОРИОКС знает о заданиях, — одним плоским списком со сроками.
 *
 * Предмет здесь часть строки, а не заголовок блока: задание нельзя
 * понять в отрыве от него, а группировка по дисциплинам давала полсотни
 * строк, в которых не видно главного — что делать в ближайшие дни.
 *
 * Живёт отдельно от экрана, потому что тот же список нужен главной: она
 * показывает из него три ближайших дела.
 */
export function flatten(tasks, sched, start, shift) {
  const all = [];
  (tasks.disciplines || []).forEach(d => (d.events || []).forEach(e => {
    const at = lessonDay(sched, start, e, d.name, shift);
    const due = at ? at.date : dueDate(start, e.week);
    const left = daysLeft(due);
    all.push({
      ...e,
      idx: all.length,
      // Пара, на которой сдают: по ней и показываем день вместо
      // безликого «конца второй недели».
      lesson: at ? at.lesson : null,
      exactDay: !!(at && at.exact),
      subject: d.name,
      title: titleOf(e),
      due,
      left,
      bucket: bucketOf(left),
    });
  }));
  return all;
}

/**
 * Несданные задания, ближайшие сверху.
 *
 * Формальности (посещаемость, «порядок НБС») и события сессии сюда не
 * попадают: сдавать там нечего, а строк они дают больше трети.
 */
export function pendingOf(all) {
  return all.filter(t => t.task && !t.done)
    .sort((a, b) => (a.left ?? 9999) - (b.left ?? 9999));
}

const doneRow = t => `
  <div class="todo done">
    <div class="todo-main">
      <div class="todo-subject">${esc(t.subject)}</div>
      <div class="todo-what">${esc(t.title.main)}</div>
    </div>
    <div class="todo-side">
      <div class="todo-grade">${t.grade} из ${t.max_grade}</div>
    </div>
  </div>`;

export default async function tasksScreen() {
  if (!canTalk) {
    return screen({
      title: 'Задания',
      body: emptyState('Раздел работает внутри Telegram', 'backpack'),
    });
  }

  let data;
  let news = [];
  // Доступ к сайту ОРИОКС — это не то же самое, что подключение: токен
  // может быть жив, а сессия сайта кончиться. Объявления и подписка на
  // них есть только при живой сессии.
  let web = false;
  try {
    const both = await Promise.all([
      get('/api/orioks', { timeout: 25000 }),
      // Объявления не должны мешать заданиям: не пришли — экран
      // работает дальше, просто без них.
      get('/api/orioks/news', { timeout: 25000 }).catch(() => ({ news: [] })),
    ]);
    data = both[0];
    news = both[1].news || [];
    web = both[1].web === true;
  } catch (err) {
    return screen({
      title: 'Задания',
      body: `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`,
    });
  }

  if (!data.linked) return notLinked();
  if (data.error) return linkedButBroken(data.error);

  // Расписание нужно целиком, а не только ради начала семестра: по нему
  // находится день пары, на которой задание и сдают.
  let start = null;
  let sched = null;
  if (settings.group) {
    try {
      sched = await fetchSchedule(settings.group);
      start = semesterStart(sched.semestr);
    } catch { /* без дат покажем недели */ }
  }

  const all = flatten(data.tasks, sched, start, settings.weekShift);

  // ОРИОКС отдаёт вперемешку с заданиями формальности: посещаемость,
  // «порядок НБС», семестровый план. Сдавать там нечего, а строк они
  // дают больше трети — из-за них список и был нечитаемым.
  const tasks = all.filter(t => t.task);
  const session = all.filter(t => t.session)
    .sort((a, b) => (a.left ?? 9999) - (b.left ?? 9999));
  const formal = all.filter(t => !t.task && !t.session);

  const pending = pendingOf(all);
  const done = tasks.filter(t => t.done);

  const soon = pending.filter(t => t.left !== null && t.left <= 7).length;

  // Вложения со всех мероприятий разом, включая те, что висят не на
  // заданиях: у живого студента половина файлов лежит именно там.
  const files = [];
  all.forEach(t => (t.materials || []).forEach(
    m => files.push({ ...m, subject: t.subject, event: t.title.main })));

  const node = screen({
    title: 'Задания',
    subtitle: start ? 'Сроки, баллы и файлы из ОРИОКС'
      : 'Выбери группу в профиле, чтобы видеть даты',
    actions: `<button class="icon-btn" data-action="orioks">${icon('external', 19)}</button>`,
    body: `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${pending.length}</div>
          <div class="kpi-label">Не сдано</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${soon}</div>
          <div class="kpi-label">На этой неделе</div>
        </div>
      </div>

      ${news.length ? `
        <div class="section-head">
          <div class="section-title with-icon">
            ${icon('megaphone', 17)} Что задали
          </div>
          ${news.length > 3 ? `<button class="section-link"
            id="toggle-news">${news.length}</button>` : ''}
        </div>
        <p class="section-note">
          Объявления преподавателей — то, что они пишут к занятию.
        </p>
        <div class="notice-list">
          ${news.slice(0, 3).map(newsRow).join('')}
        </div>
        <div class="notice-list" id="news-rest" hidden>
          ${news.slice(3).map(newsRow).join('')}
        </div>` : ''}

      ${web ? `
        <div class="list-card watch-card">
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">Сообщать о новом</div>
              <div class="row-subtitle">
                Бот напишет в личку, когда преподаватель выложит
                объявление. Проверяет днём, раз в полтора часа.
              </div>
            </div>
            ${toggle(data.notify !== false, 'watch')}
          </div>
        </div>` : ''}

      <div class="pill-row" id="kinds" style="margin:14px 0 4px">
        ${KINDS.map(k => `
          <button class="pill ${k.id === 'all' ? 'active' : ''}"
                  data-kind="${k.id}">${esc(k.label)}</button>`).join('')}
      </div>

      <div id="task-list"></div>

      ${session.length ? `
        <div class="section-head"><div class="section-title with-icon">${icon('award', 17)} Сессия</div></div>
        <p class="section-note">Экзамены и зачёты — ими семестр кончается.</p>
        <div class="list-card">${session.map(taskRow).join('')}</div>` : ''}

      ${done.length ? `
        <div class="section-head">
          <div class="section-title">Сдано</div>
          <button class="section-link" id="toggle-done">${done.length}</button>
        </div>
        <div class="list-card" id="done-list" hidden>
          ${done.map(doneRow).join('')}
        </div>` : ''}

      ${files.length ? `
        <div class="section-head">
          <div class="section-title with-icon">${icon('folder', 17)} Файлы от преподавателей</div>
          <button class="section-link" id="toggle-files">${files.length}</button>
        </div>
        <p class="section-note">
          Методички, условия и бланки. Это всё, что ОРИОКС знает о
          заданиях сверх их названий.
        </p>
        <div class="notice-list" id="files-list" hidden>
          ${files.map(fileRow).join('')}
        </div>` : ''}

      ${formal.length ? `
        <div class="section-head">
          <div class="section-title">Не задания</div>
          <button class="section-link" id="toggle-formal">${formal.length}</button>
        </div>
        <p class="section-note">
          Посещаемость, активность и записи для порядка — сдавать нечего.
        </p>
        <div class="list-card" id="formal-list" hidden>
          ${formal.map(t => `
            <div class="todo done">
              <div class="todo-main">
                <div class="todo-subject">${esc(t.subject)}</div>
                <div class="todo-what">${esc(t.title.main)}</div>
              </div>
              <div class="todo-side">
                <div class="todo-left">${t.max_grade ? `до ${t.max_grade} б.` : '—'}</div>
              </div>
            </div>`).join('')}
        </div>` : ''}

      <div class="section-head"><div class="section-title">По предметам</div></div>
      <div class="list-card">
        ${data.tasks.disciplines.map(d => {
      const left = d.events.filter(e => e.task && !e.done).length;
      return `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(d.name)}</div>
              <div class="row-subtitle">
                ${d.current_grade ?? 0} из ${d.max_grade ?? 0} б.
                ${d.control_form ? ` · ${esc(d.control_form)}` : ''}
              </div>
            </div>
            <div class="list-row-value ${left ? '' : 'muted'}">
              ${left ? `${left} ост.` : 'всё'}
            </div>
          </div>`;
    }).join('')}
      </div>

      <button class="btn-secondary danger-btn" id="unlink" style="margin-top:14px">
        Отключить ОРИОКС
      </button>
      <div class="fab-note">
        Текста задания в ОРИОКС нет вовсе — ни в приложении, ни на сайте.
        Есть файлы, которые выложил преподаватель: они собраны здесь и
        открываются в ОРИОКС.
      </div>`,
  });

  // Список перерисовывается на месте: фильтр по виду работы не должен
  // перезагружать экран и терять прокрутку.
  const listBox = node.querySelector('#task-list');
  let kind = KINDS[0];
  const unfolded = new Set();

  const drawList = () => {
    const items = pending.filter(t => kind.match(`${t.type} ${t.name}`));
    const groups = BUCKETS
      .map(b => ({ ...b, items: items.filter(t => t.bucket === b.id) }))
      .filter(b => b.items.length);

    if (!groups.length) {
      listBox.innerHTML = emptyState(
        kind.id === 'all' ? 'Всё сдано — свободен' : 'Таких работ нет', 'check');
      return;
    }
    listBox.innerHTML = groups.map(g => {
      // «Потом» у студента — полсотни записей: развёрнутым этот блок и
      // превращал экран в простыню. Сворачиваем, оставляя счётчик.
      const folded = g.id === 'later' && g.items.length > 6
        && !unfolded.has(g.id);
      return `
        <div class="section-head">
          <div class="section-title">${esc(g.title)}</div>
          ${folded ? `<button class="section-link" data-unfold="${g.id}">
            ${g.items.length}</button>` : ''}
        </div>
        ${g.note ? `<p class="section-note">${esc(g.note)}</p>` : ''}
        <div class="list-card">
          ${(folded ? g.items.slice(0, 3) : g.items).map(taskRow).join('')}
        </div>`;
    }).join('');
  };
  drawList();

  node.querySelector('#kinds').addEventListener('click', e => {
    const b = e.target.closest('[data-kind]');
    if (!b) return;
    kind = KINDS.find(k => k.id === b.dataset.kind);
    node.querySelectorAll('#kinds .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    drawList();
  });

  listBox.addEventListener('click', e => {
    const filesBtn = e.target.closest('[data-files]');
    if (filesBtn) return filesSheet(all[+filesBtn.dataset.files]);
    const more = e.target.closest('[data-unfold]');
    if (!more) return;
    // Перерисовываем список целиком вместо поиска соседних узлов: так
    // разметка может меняться, не ломая обработчик.
    unfolded.add(more.dataset.unfold);
    drawList();
  });

  const toggler = (btnId, listId, count) =>
    node.querySelector(btnId)?.addEventListener('click', e => {
      const list = node.querySelector(listId);
      list.hidden = !list.hidden;
      e.target.textContent = list.hidden ? count : 'скрыть';
    });
  toggler('#toggle-done', '#done-list', done.length);
  toggler('#toggle-files', '#files-list', files.length);
  toggler('#toggle-news', '#news-rest', news.length);
  node.addEventListener('click', e => {
    const row = e.target.closest('[data-news]');
    if (row) newsSheet(row.dataset.news, news);
  });
  node.querySelector('#files-list')?.addEventListener('click', e => {
    const row = e.target.closest('[data-link]');
    if (row) openLink(row.dataset.link);
  });
  toggler('#toggle-formal', '#formal-list', formal.length);
  node.querySelector('[data-toggle="watch"]')?.addEventListener('click', async e => {
    const t = e.currentTarget;
    const on = !t.classList.contains('on');
    // Переключаем сразу, а откатываем при отказе: подписка — мелочь, и
    // ждать ответа сервера, глядя на неподвижный тумблер, незачем.
    t.classList.toggle('on', on);
    haptic('light');
    try {
      await post('/api/orioks/notify', { on });
      data.notify = on;
    } catch (err) {
      toast(err.message);
      t.classList.toggle('on', !on);
    }
  });
  node.querySelector('[data-action="orioks"]').addEventListener('click',
    () => openLink('https://orioks.miet.ru/main/login'));
  node.querySelector('#unlink').addEventListener('click', async () => {
    if (!await confirmDialog('Отключить ОРИОКС? Токен будет отозван.')) return;
    try {
      await post('/api/orioks/unlink', {});
      account.orioks = false;
      hapticNotify('success');
      refresh();
    } catch (err) { toast(err.message); }
  });

  return node;
}

// ─────────────── подключение ───────────────

function notLinked() {
  const node = screen({
    title: 'Задания',
    subtitle: 'Что задали, что сдать и файлы из ОРИОКС',
    body: `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:8px">Подключи ОРИОКС</div>
        <div class="row-subtitle" style="line-height:1.55">
          Приложение соберёт все контрольные мероприятия семестра в один
          список: что сдавать, к какому числу и сколько это даёт баллов.
          Ближайшее — сверху, просроченное — отдельно.
        </div>
      </div>

      <div class="warn-note" style="margin-top:12px">
        ${icon('shield', 16)}
        Пароль не сохраняется. ОРИОКС меняет его на токен — в базе лежит
        только токен, и отозвать его можно кнопкой «Отключить».
      </div>

      <button class="btn-primary" id="link" style="margin-top:14px">
        Подключить
      </button>`,
  });

  node.querySelector('#link').addEventListener('click', linkSheet);
  return node;
}

function linkedButBroken(message) {
  const node = screen({
    title: 'Задания',
    body: `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:6px">ОРИОКС не ответил</div>
        <div class="row-subtitle" style="margin-bottom:14px">${esc(message)}</div>
        <button class="btn-primary" id="relink">Подключить заново</button>
      </div>`,
  });
  node.querySelector('#relink').addEventListener('click', linkSheet);
  return node;
}

function linkSheet() {
  sheet({
    title: 'Вход в ОРИОКС',
    body: `
      <div class="field-group">
        <div class="field-label">Логин</div>
        <input class="field-input" id="olog" autocomplete="username"
               autocapitalize="none" spellcheck="false"
               placeholder="тот же, что при входе в ОРИОКС">
      </div>
      <div class="field-group">
        <div class="field-label">Пароль</div>
        <input class="field-input" id="opass" type="password"
               autocomplete="current-password">
      </div>
      <div class="warn-note">
        ${icon('shield', 16)}
        Пароль уходит в ОРИОКС за доступом к твоему кабинету и нигде не
        сохраняется — ни в боте, ни в телефоне. Доступ нужен, чтобы
        показать текст заданий: в кратком виде ОРИОКС отдаёт только их
        названия. Отключишь — доступ стирается сразу.
      </div>
      <button class="btn-primary" id="ogo" style="margin-top:12px">Войти</button>`,
    onMount(root, close) {
      const go = root.querySelector('#ogo');
      go.addEventListener('click', async () => {
        const login = root.querySelector('#olog').value.trim();
        const password = root.querySelector('#opass').value;
        if (!login || !password) return toast('Введи логин и пароль');
        go.disabled = true;
        go.textContent = 'Подключаю…';
        try {
          await post('/api/orioks/link', { login, password }, { timeout: 45000 });
          account.orioks = true;
          hapticNotify('success');
          close();
          refresh();
        } catch (err) {
          toast(err.message);
          go.disabled = false;
          go.textContent = 'Войти';
        }
      });
    },
  });
}


/**
 * Файлы одного задания.
 *
 * Открываются в ОРИОКС, а не скачиваются сюда: ссылка живёт под
 * сессией института, и подменять её собственным хранилищем значило бы
 * копировать чужие материалы неизвестно куда.
 */
function filesSheet(task) {
  const items = task.materials || [];
  sheet({
    title: task.title.main,
    body: `
      <div class="notice-head tone-${subjectLook(task.subject).tone}">
        <div class="notice-badge">
          ${icon(subjectLook(task.subject).glyph, 22)}
        </div>
        <div class="notice-head-text">
          <div class="notice-subject">${esc(task.subject)}</div>
          <div class="notice-head-meta">
            ${icon('clipboard', 13)}
            <span>${esc(task.title.main)}</span>
          </div>
        </div>
      </div>
      <div class="notice-list">
        ${items.map((m, i) => {
          const look = fileLook(m.name, m.link);
          return `
          <button class="notice-card file-card" data-open="${i}">
            <div class="notice-badge">${icon(look.glyph, 19)}</div>
            <div class="notice-main">
              <div class="notice-title">${esc(m.name)}</div>
              <div class="notice-foot">
                ${m.kind ? `<span>${esc(m.kind)}</span>` : ''}
                ${look.label
                  ? `<span class="file-kind">${esc(look.label)}</span>` : ''}
                <span class="notice-open">Открыть ${icon('external', 13)}</span>
              </div>
            </div>
          </button>`;
        }).join('')}
      </div>
      <div class="fab-note">
        Откроется в ОРИОКС. Если попросит войти — это обычный вход,
        приложение тут ни при чём.
      </div>`,
    onMount(root) {
      root.addEventListener('click', e => {
        const row = e.target.closest('[data-open]');
        if (row) openLink(items[+row.dataset.open].link);
      });
    },
  });
}


/**
 * Объявление преподавателя целиком.
 *
 * Текст тянется отдельным запросом, а не вместе со списком: объявлений
 * бывает два десятка, а читают обычно одно, и качать все ради этого —
 * лишние секунды на каждом открытии экрана.
 */
async function newsSheet(href, list) {
  const known = (list || []).find(n => n.href === href) || {};
  const look = subjectLook(known.discipline);
  const date = newsDate(known.date);

  sheet({
    title: known.title || 'Объявление',
    body: `
      <div class="notice-head tone-${look.tone}">
        <div class="notice-badge">${icon(look.glyph, 22)}</div>
        <div class="notice-head-text">
          <div class="notice-subject">
            ${esc(known.discipline || 'Объявление')}
          </div>
          <div class="notice-head-meta">
            ${known.author ? `${icon('user', 13)}
              <span>${esc(known.author)}</span>` : ''}
            ${date.text ? `${icon('clock', 13)}
              <span>${esc(date.text)}</span>` : ''}
          </div>
        </div>
      </div>
      <div class="notice-body" id="notice-body">
        <div class="skeleton notice-skeleton"></div>
        <div class="skeleton notice-skeleton"></div>
        <div class="skeleton notice-skeleton short"></div>
      </div>`,
    onMount(root) {
      const box = root.querySelector('#notice-body');
      post('/api/orioks/news', { item: href }, { timeout: 25000 })
        .then(r => {
          const it = r.item || {};
          if (!it.text) {
            box.innerHTML = emptyState(
              r.error || 'ОРИОКС не отдал текст объявления', 'info');
            return;
          }
          box.innerHTML = it.text.split('\n').filter(Boolean)
            .map(line => NUMBERED.test(line)
              ? `<p class="notice-item">${linkify(line)}</p>`
              : `<p>${linkify(line)}</p>`).join('');
        })
        .catch(err => { box.innerHTML = emptyState(err.message, 'info'); });

      box.addEventListener('click', e => {
        const a = e.target.closest('a[data-url]');
        if (!a) return;
        e.preventDefault();
        openLink(a.dataset.url);
      });
    },
  });
}



/**
 * Текст со ссылками: преподаватели дают в объявлениях литературу
 * ссылками, и оставлять их непрожимаемой строкой — значит заставлять
 * переписывать адрес руками.
 *
 * Экранируем по кускам, а не целиком: экранированный текст уже нельзя
 * разбирать регулярным выражением, не рискуя склеить разметку.
 */
export function linkify(text) {
  const parts = String(text).split(/(https?:\/\/[^\s<>"']+)/g);
  return parts.map((part, i) => {
    if (i % 2 === 0) return esc(part);
    const shown = part.length > 48 ? part.slice(0, 45) + '…' : part;
    return `<a href="#" data-url="${esc(part)}">${esc(shown)}</a>`;
  }).join('');
}


// Строка списка внутри объявления: «1.», «2)», «А)», «·». Преподаватели
// пишут задания перечнем, и сплошным текстом он читается вдвое хуже.
export const NUMBERED = /^\s*(?:[0-9]{1,2}\s*[.)]|[А-Яа-яA-Za-z]\s*\)|[·•\-–])\s+/;
