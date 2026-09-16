// Розыгрыш: своя ссылка, свой счёт, общая таблица.
//
// Экран собран вокруг одного действия — отправить ссылку. Поэтому кнопка
// «Поделиться» стоит выше объяснений: тот, кто уже всё понял, не должен
// пролистывать правила, чтобы до неё добраться.
//
// Правила показаны целиком и до участия, а не мелким шрифтом после.
// Человек, который привёл двадцать друзей и узнал в конце, что половина
// не засчиталась, справедливо считает себя обманутым.

import { icon } from '../icons.js';
import { esc, el, segmented, bindChoice, emptyState, toast, skeleton } from '../ui.js';
import { get } from '../api.js';
import { screen } from './common.js';
import { haptic, hapticNotify, openLink, tg } from '../tg.js';

// Правила лежат в клиенте, а не приезжают с сервером: это описание того,
// как считает сервер, и расходиться они не должны. Менять их вместе с
// логикой в bot/raffle.py.
const RULES = [
  ['Отправь свою ссылку',
   'Она у каждого своя и лежит выше. Кидай в чат группы, потока, друзьям'],
  ['Человек открывает бота по ней',
   'Именно по твоей ссылке — она закрепляет его за тобой навсегда'],
  ['И выбирает свою группу',
   'Только после этого переход идёт в зачёт: заглянуть и уйти не считается'],
  ['В счёт идут живые люди',
   'Аккаунт без ника, без фото и без премиума в зачёт не попадает'],
  ['Один человек — одно очко',
   'Повторные заходы, вторые аккаунты и те, кто уже пользовался приложением, не считаются'],
];

const DAYS = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];

/** Подпись дня для полоски: из «2026-09-16» в «ср». */
export function dayLabel(iso) {
  const [y, m, d] = String(iso || '').split('-').map(Number);
  if (!y || !m || !d) return '';
  return DAYS[new Date(Date.UTC(y, m - 1, d)).getUTCDay()] || '';
}

/**
 * Полоска переходов за неделю.
 *
 * Высота столбика считается от максимума за ту же неделю, а не от общего
 * рекорда: сравнивать сегодня хочется со вчера. Нулевой день рисуется
 * чёрточкой, а не пустотой, — иначе непонятно, был день или его данные
 * не приехали.
 */
function weekBars(week = []) {
  const max = Math.max(1, ...week.map(d => d.count || 0));
  return `<div class="raffle-week">${week.map(d => `
    <div class="raffle-day" title="${esc(d.date)}: ${d.count}">
      ${d.count ? `<div class="raffle-day-num">${d.count}</div>` : ''}
      <div class="raffle-bar" style="height:${d.count ? Math.round(6 + 54 * d.count / max) : 3}px"></div>
      <div class="raffle-day-name">${esc(dayLabel(d.date))}</div>
    </div>`).join('')}</div>`;
}

const PLACE_TONE = ['gold', 'silver', 'bronze'];

/** Карточка розыгрыша: название, срок и призовые места. */
function banner(s) {
  const left = s.days_left;
  return `
    <div class="raffle-banner">
      ${left === null || left === undefined ? '' : `
        <div class="raffle-left">${icon('clock', 14)} ${left === 0
          ? 'последний день' : `осталось ${left} ${plural(left, 'день', 'дня', 'дней')}`}</div>`}
      <div class="raffle-banner-title">${esc(s.title || 'Розыгрыш')}</div>
      ${s.note ? `<div class="raffle-banner-note">${esc(s.note)}</div>` : ''}
      ${s.prizes?.length ? `<div class="raffle-prizes">${s.prizes.map(p => `
        <div class="raffle-prize ${PLACE_TONE[p.place - 1] || ''}">
          <div class="raffle-prize-place">${p.place} место</div>
          <div class="raffle-prize-text">${p.emoji ? `${esc(p.emoji)} ` : ''}${esc(p.text)}</div>
        </div>`).join('')}</div>` : ''}
    </div>`;
}

export function plural(n, one, few, many) {
  const a = Math.abs(n) % 100;
  const b = a % 10;
  if (a > 10 && a < 20) return many;
  if (b > 1 && b < 5) return few;
  return b === 1 ? one : many;
}

/** Три числа наверху: что засчитано, что ещё ждёт и какое место. */
function counters(s) {
  return `
    <div class="raffle-counts">
      <div class="raffle-count"><b>${s.counted}</b><span>засчитано</span></div>
      <div class="raffle-count"><b>${s.waiting}</b><span>ждут группу</span></div>
      <div class="raffle-count"><b>${s.place || '—'}</b><span>место</span></div>
    </div>`;
}

function mainTab(s) {
  return `
    ${banner(s)}
    <div class="raffle-card">
      ${counters(s)}
      <div class="raffle-week-head">приходят по твоей ссылке</div>
      ${weekBars(s.week)}
    </div>
    <button class="btn-primary raffle-share" data-act="share">Поделиться ссылкой</button>
    <button class="raffle-copy" data-act="copy">${icon('clipboard', 16)} Скопировать ссылку</button>
    <div class="section-head"><div class="section-title">Как это работает</div></div>
    <div class="list-card">
      ${RULES.map(([title, note], i) => `
        <div class="raffle-rule">
          <div class="raffle-rule-num">${i + 1}</div>
          <div>
            <div class="raffle-rule-title">${esc(title)}</div>
            <div class="raffle-rule-note">${esc(note)}</div>
          </div>
        </div>`).join('')}
    </div>
    ${s.rules_note ? `<p class="raffle-fineprint">${esc(s.rules_note)}</p>` : ''}`;
}

/** Первое место посередине и выше — так пьедестал читается без подписей. */
function podium(top) {
  const [first, second, third] = [top[0], top[1], top[2]];
  const step = (p, cls) => !p ? `<div class="raffle-step ${cls} empty"></div>` : `
    <div class="raffle-step ${cls}">
      <div class="raffle-face ${cls}">${avatar(p)}</div>
      <div class="raffle-step-name">${esc(p.name)}</div>
      <div class="raffle-step-count">${p.count} ${plural(p.count, 'человек', 'человека', 'человек')}</div>
      <div class="raffle-podium-block ${cls}">${p.place}</div>
    </div>`;
  return `<div class="raffle-podium">
    ${step(second, 'silver')}${step(first, 'gold')}${step(third, 'bronze')}</div>`;
}

/**
 * Аватар: картинка, если Telegram её отдал, иначе первая буква имени.
 * Ссылки на фото живут недолго, поэтому падение картинки заменяется
 * буквой прямо на месте, а не оставляет дыру.
 */
function avatar(p) {
  const letter = esc((p.name || '?').trim().charAt(0).toUpperCase());
  if (!p.photo) return `<span class="raffle-letter">${letter}</span>`;
  return `<img src="${esc(p.photo)}" alt="" loading="lazy"
    onerror="this.replaceWith(Object.assign(document.createElement('span'),
      {className:'raffle-letter',textContent:'${letter}'}))">`;
}

function boardRows(list) {
  return list.map(p => `
    <div class="raffle-row ${p.me ? 'me' : ''}">
      <div class="raffle-place">${p.place}</div>
      <div class="raffle-face small">${avatar(p)}</div>
      <div class="raffle-who">
        <div class="raffle-name">${esc(p.name)}</div>
        ${p.username ? `<div class="raffle-nick">@${esc(p.username)}</div>` : ''}
      </div>
      ${p.marked ? `<div class="raffle-mark" title="Спорных приглашений: ${p.marked}">⚠ ${p.marked}</div>` : ''}
      <div class="raffle-score">${p.count}</div>
    </div>`).join('');
}

function boardTab(b) {
  if (!b.top.length) {
    return emptyState('Пока никто никого не привёл — можешь стать первым', 'medal');
  }
  // Списком идёт всё, что не поместилось на пьедестал, — считаем по
  // ПОРЯДКУ, а не по месту: при равном счёте место общее, и пятеро
  // первых с одним очком вырезали бы друг друга из списка.
  const rest = b.top.slice(3);
  const me = b.me || {};
  return `
    ${podium(b.top)}
    ${rest.length ? `<div class="list-card raffle-list">${boardRows(rest)}</div>` : ''}
    ${me.count && !me.in_top ? `
      <div class="raffle-mine-head">Ты</div>
      <div class="list-card raffle-list">${boardRows([{
        place: me.place, name: 'Ты', username: '', photo: '',
        count: me.count, me: true,
      }])}</div>` : ''}
    <p class="raffle-fineprint">Участников: ${b.players}. При равном счёте выше тот,
      кто набрал его раньше</p>`;
}

export default async function raffleScreen() {
  const node = screen({
    title: 'Розыгрыш',
    subtitle: 'Приглашай друзей — и поднимайся в таблице',
    body: `${segmented([
      { id: 'main', label: 'Главное' },
      { id: 'board', label: 'Лидерборд' },
    ], 'main', 'raffle')}
    <div class="raffle-body">${skeleton(140)}</div>`,
  });

  const body = node.querySelector('.raffle-body');
  let state = null;
  let board = null;

  // Ссылка нужна и на вкладке таблицы (кнопка «Поделиться» никуда не
  // девается), поэтому состояние грузится один раз и держится здесь.
  const loadMain = async () => {
    if (!state) state = await get('/api/raffle');
    return state;
  };

  const show = async tab => {
    body.innerHTML = skeleton(140);
    try {
      if (tab === 'board') {
        board = board || await get('/api/raffle/board');
        body.innerHTML = boardTab(board);
      } else {
        body.innerHTML = mainTab(await loadMain());
      }
    } catch (err) {
      // 404 здесь означает «раздел закрыт»: владелец ещё не открыл его
      // всем. Это не поломка, и пугать человека ошибкой незачем.
      body.innerHTML = emptyState(
        /404/.test(err.message) ? 'Розыгрыш пока не начался' : err.message, 'medal');
    }
  };

  bindChoice(node, 'raffle', show, 'seg');
  show('main');

  node.addEventListener('click', e => {
    const btn = e.target.closest('[data-act]');
    if (!btn || !state?.link) return;
    haptic('medium');
    if (btn.dataset.act === 'share') {
      // Через t.me/share Telegram сам показывает выбор чата. Свой список
      // чатов нарисовать нельзя: мини-приложение их не видит.
      const text = state.title
        ? `${state.title} — расписание МИЭТ в одном приложении`
        : 'Расписание МИЭТ в одном приложении';
      openLink(`https://t.me/share/url?url=${encodeURIComponent(state.link)}`
        + `&text=${encodeURIComponent(text)}`);
      return;
    }
    copy(state.link);
  });

  return node;
}

/**
 * Копирование в буфер. В WebView Telegram clipboard-API бывает закрыт,
 * поэтому есть запасной путь через скрытое поле: иначе кнопка молча
 * ничего не делала бы.
 */
function copy(text) {
  const done = () => { hapticNotify('success'); toast('Ссылка скопирована'); };
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(done, () => fallback(text, done));
    return;
  }
  fallback(text, done);
}

function fallback(text, done) {
  const field = el(`<textarea style="position:fixed;opacity:0;pointer-events:none"></textarea>`);
  field.value = text;
  document.body.appendChild(field);
  field.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch { ok = false; }
  field.remove();
  if (ok) return done();
  // Совсем не вышло — показываем ссылку, чтобы её можно было выделить
  // руками. Пустая кнопка хуже некрасивого решения.
  tg?.showAlert?.(text) ?? toast(text);
}
