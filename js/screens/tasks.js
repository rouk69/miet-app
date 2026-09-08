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
import { esc, emptyState, toast, sheet } from '../ui.js';
import { get, post, account, canTalk } from '../api.js';
import { settings } from '../store.js';
import { fetchSchedule, semesterStart } from '../schedule.js';
import { refresh } from '../router.js';
import { hapticNotify, confirmDialog, openLink } from '../tg.js';
import { screen } from './common.js';

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

const WEEKDAYS = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];

/** Конец учебной недели N — до него задание и сдают. */
function dueDate(start, week) {
  if (!start || !week) return null;
  const d = new Date(start.getTime());
  d.setDate(d.getDate() + (week - 1) * 7 + 6);
  return d;
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
    </div>
  </div>`;

const fileRow = f => `
  <div class="todo file-row" data-link="${esc(f.link)}">
    <div class="todo-main">
      <div class="todo-subject">${esc(f.name)}</div>
      <div class="todo-what">
        ${esc(f.subject)}${f.kind ? ` · ${esc(f.kind)}` : ''}
      </div>
    </div>
    <div class="todo-side">${icon('external', 16)}</div>
  </div>`;

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
      body: emptyState('Раздел работает внутри Telegram', 'clipboard'),
    });
  }

  let data;
  try {
    data = await get('/api/orioks', { timeout: 25000 });
  } catch (err) {
    return screen({
      title: 'Задания',
      body: `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`,
    });
  }

  if (!data.linked) return notLinked();
  if (data.error) return linkedButBroken(data.error);

  let start = null;
  if (settings.group) {
    try {
      const sched = await fetchSchedule(settings.group);
      start = semesterStart(sched.semestr);
    } catch { /* без дат покажем недели */ }
  }

  // Разворачиваем всё в один плоский список: предмет — часть строки, а
  // не заголовок блока, иначе задание нельзя понять в отрыве от него.
  const all = [];
  data.tasks.disciplines.forEach(d => d.events.forEach(e => {
    const due = dueDate(start, e.week);
    const left = daysLeft(due);
    all.push({
      ...e,
      idx: all.length,
      subject: d.name,
      title: titleOf(e),
      due,
      left,
      bucket: bucketOf(left),
    });
  }));

  // ОРИОКС отдаёт вперемешку с заданиями формальности: посещаемость,
  // «порядок НБС», семестровый план. Сдавать там нечего, а строк они
  // дают больше трети — из-за них список и был нечитаемым.
  const tasks = all.filter(t => t.task);
  const session = all.filter(t => t.session)
    .sort((a, b) => (a.left ?? 9999) - (b.left ?? 9999));
  const formal = all.filter(t => !t.task && !t.session);

  const pending = tasks.filter(t => !t.done)
    .sort((a, b) => (a.left ?? 9999) - (b.left ?? 9999));
  const done = tasks.filter(t => t.done);

  const soon = pending.filter(t => t.left !== null && t.left <= 7).length;

  // Вложения со всех мероприятий разом, включая те, что висят не на
  // заданиях: у живого студента половина файлов лежит именно там.
  const files = [];
  all.forEach(t => (t.materials || []).forEach(
    m => files.push({ ...m, subject: t.subject, event: t.title.main })));

  const node = screen({
    title: 'Что сдать',
    subtitle: start ? 'Сроки — по твоему расписанию'
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

      <div class="pill-row" id="kinds" style="margin:14px 0 4px">
        ${KINDS.map(k => `
          <button class="pill ${k.id === 'all' ? 'active' : ''}"
                  data-kind="${k.id}">${esc(k.label)}</button>`).join('')}
      </div>

      <div id="task-list"></div>

      ${session.length ? `
        <div class="section-head"><div class="section-title">Сессия</div></div>
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
          <div class="section-title">Файлы от преподавателей</div>
          <button class="section-link" id="toggle-files">${files.length}</button>
        </div>
        <p class="section-note">
          Методички, условия и бланки. Это всё, что ОРИОКС знает о
          заданиях сверх их названий.
        </p>
        <div class="list-card" id="files-list" hidden>
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
  node.querySelector('#files-list')?.addEventListener('click', e => {
    const row = e.target.closest('[data-link]');
    if (row) openLink(row.dataset.link);
  });
  toggler('#toggle-formal', '#formal-list', formal.length);
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
    title: 'Что сдать',
    subtitle: 'Задания и сроки из ОРИОКС',
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
    title: 'Что сдать',
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
      <div class="row-subtitle" style="margin-bottom:12px">
        ${esc(task.subject)}
      </div>
      <div class="list-card">
        ${items.map((m, i) => `
          <div class="todo file-row" data-open="${i}">
            <div class="todo-main">
              <div class="todo-subject">${esc(m.name)}</div>
              ${m.kind ? `<div class="todo-what">${esc(m.kind)}</div>` : ''}
            </div>
            <div class="todo-side">${icon('external', 16)}</div>
          </div>`).join('')}
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
