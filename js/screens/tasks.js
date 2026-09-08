// Задания из ОРИОКС: что сдать, когда и на сколько баллов.
//
// В ОРИОКС домашние задания живут контрольными мероприятиями: у каждого
// есть название, тип, учебная неделя сдачи и баллы. Текста задания и
// файлов API не отдаёт — поэтому экран честно отвечает на вопрос «что и
// когда сдавать», а не заменяет собой ОРИОКС.
//
// Неделю в дату превращаем здесь: начало семестра считается из
// расписания, и второй раз выводить его на сервере значило бы получить
// два разных ответа на один вопрос.

import { icon } from '../icons.js';
import { esc, emptyState, toast, sheet } from '../ui.js';
import { get, post, account, canTalk } from '../api.js';
import { settings } from '../store.js';
import { fetchSchedule, semesterStart } from '../schedule.js';
import { refresh } from '../router.js';
import { hapticNotify, confirmDialog, openLink } from '../tg.js';
import { screen } from './common.js';

const MONTHS = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг',
  'сен', 'окт', 'ноя', 'дек'];

/** Понедельник учебной недели N от начала семестра. */
function weekDate(start, week) {
  if (!start || !week) return null;
  const d = new Date(start.getTime());
  d.setDate(d.getDate() + (week - 1) * 7);
  return d;
}

const human = d => d ? `${d.getDate()} ${MONTHS[d.getMonth()]}` : '';

/** Сколько дней осталось: по этому же числу задания и сортируются. */
function daysLeft(date) {
  if (!date) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  // Срок — конец недели, а не её понедельник: задание сдают в течение
  // недели, и пугать человека раньше времени незачем.
  const due = new Date(date.getTime());
  due.setDate(due.getDate() + 6);
  return Math.round((due - today) / 86400000);
}

function dueLabel(left) {
  if (left === null) return 'срок не указан';
  if (left < 0) return `просрочено на ${-left} дн`;
  if (left === 0) return 'сегодня последний день';
  if (left === 1) return 'остался день';
  if (left < 7) return `осталось ${left} дн`;
  return `осталось ${Math.round(left / 7)} нед`;
}

const taskRow = (t, start) => {
  const date = weekDate(start, t.week);
  const left = t.done ? null : daysLeft(date);
  const urgent = left !== null && left <= 7;
  const late = left !== null && left < 0;
  return `
    <div class="task ${t.done ? 'done' : ''} ${late ? 'late' : urgent ? 'soon' : ''}">
      <div class="task-mark">
        ${t.done ? icon('check', 16) : icon(t.homework ? 'edit' : 'clipboard', 16)}
      </div>
      <div class="task-body">
        <div class="task-name">${esc(t.name)}</div>
        <div class="task-meta">
          ${t.type ? `<span>${esc(t.type)}</span>` : ''}
          ${date ? `<span>${icon('calendar', 13)} ${esc(human(date))} · ${t.week} нед</span>` : ''}
          ${t.done
    ? `<span class="task-grade">${t.grade} из ${t.max_grade}</span>`
    : `<span class="${late ? 'task-late' : urgent ? 'task-soon' : ''}">
         ${esc(dueLabel(left))}</span>
       <span class="task-grade">до ${t.max_grade} б.</span>`}
        </div>
      </div>
    </div>`;
};

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

  // Начало семестра берём из расписания своей группы: в ОРИОКС его нет,
  // а без него номер недели остаётся числом без смысла.
  let start = null;
  if (settings.group) {
    try {
      const sched = await fetchSchedule(settings.group);
      start = semesterStart(sched.semestr);
    } catch { /* покажем без дат — недели всё равно видны */ }
  }

  const all = [];
  data.tasks.disciplines.forEach(d => d.events.forEach(e =>
    all.push({ ...e, subject: d.name })));

  const pending = all.filter(t => !t.done)
    .sort((a, b) => (a.week || 99) - (b.week || 99));
  const soon = pending.filter(t => {
    const left = daysLeft(weekDate(start, t.week));
    return left !== null && left <= 14;
  });

  const node = screen({
    title: 'Задания',
    subtitle: `${data.tasks.done} из ${data.tasks.total} сдано`,
    actions: `<button class="icon-btn" data-action="orioks">${icon('external', 19)}</button>`,
    body: `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${pending.length}</div>
          <div class="kpi-label">Осталось сдать</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${soon.length}</div>
          <div class="kpi-label">В ближайшие две недели</div>
        </div>
      </div>

      ${soon.length ? `
        <div class="section-head"><div class="section-title">Ближайшее</div></div>
        <div class="stack">${soon.map(t => `
          <div class="card" style="padding:0">
            <div class="task-subject">${esc(t.subject)}</div>
            ${taskRow(t, start)}
          </div>`).join('')}</div>` : ''}

      <div class="section-head"><div class="section-title">По предметам</div></div>
      ${data.tasks.disciplines.map(d => {
      const left = d.events.filter(e => !e.done).length;
      return `
        <div class="card" style="padding:0;margin-bottom:10px">
          <div class="task-subject">
            ${esc(d.name)}
            <span class="task-subject-note">
              ${d.current_grade ?? 0} из ${d.max_grade ?? 0} б.${
  left ? ` · ${left} не сдано` : ' · всё сдано'}
            </span>
          </div>
          ${d.events.map(e => taskRow(e, start)).join('')
        || '<div class="task-empty">Контрольных мероприятий нет</div>'}
        </div>`;
    }).join('')}

      <button class="btn-secondary danger-btn" id="unlink" style="margin-top:14px">
        Отключить ОРИОКС
      </button>
      <div class="fab-note">
        Данные приходят из ОРИОКС по токену. Текст задания и файлы там же —
        их API не отдаёт, поэтому за подробностями всё равно в ОРИОКС.
      </div>`,
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
    subtitle: 'Что сдать и когда — из ОРИОКС',
    body: `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:8px">Подключи ОРИОКС</div>
        <div class="row-subtitle" style="line-height:1.55">
          Приложение покажет все контрольные мероприятия семестра: что за
          задание, к какой неделе сдавать, сколько даёт баллов и что уже
          закрыто. Сроки посчитаются в даты по твоему расписанию.
        </div>
      </div>

      <div class="warn-note" style="margin-top:12px">
        ${icon('shield', 16)}
        Пароль не сохраняется. ОРИОКС меняет его на токен — в базе лежит
        только токен, и отозвать его можно в любой момент кнопкой
        «Отключить».
      </div>

      <button class="btn-primary" id="link" style="margin-top:14px">
        Подключить
      </button>

      <div class="fab-note">
        Логин и пароль — те же, что для входа в ОРИОКС.
      </div>`,
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
        Пароль уходит в ОРИОКС за токеном и нигде не сохраняется.
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
          await post('/api/orioks/link', { login, password }, { timeout: 30000 });
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
