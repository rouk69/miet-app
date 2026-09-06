// Общие куски экранов: шапка, выбор группы, карточка новости.

import { icon } from '../icons.js';
import { esc, el, sheet, listRow, listCard, emptyState } from '../ui.js';
import { data, settings, save } from '../store.js';
import { haptic } from '../tg.js';
import { syncGroup } from '../api.js';

/** Экран-контейнер с заголовком и подзаголовком. */
export function screen({ title, subtitle, actions = '', body, small = false }) {
  const node = el(`<div class="screen"></div>`);
  node.innerHTML = `
    ${title ? `<div class="screen-top">
      <div>
        <h1 class="h1-page ${small ? 'small' : ''}">${esc(title)}</h1>
        ${subtitle ? `<p class="subtitle-page">${esc(subtitle)}</p>` : ''}
      </div>
      ${actions ? `<div class="header-actions">${actions}</div>` : ''}
    </div>` : ''}
    ${body}`;
  return node;
}

export const iconBtn = (name, action) =>
  `<button class="icon-btn" data-action="${esc(action)}">${icon(name, 19)}</button>`;

/**
 * Шторка выбора учебной группы: поиск по 346 группам с моментальной
 * фильтрацией. onPick получает название группы.
 */
export function pickGroup(onPick) {
  const groups = data.groups || [];
  const body = `
    <div class="search-box" style="margin-bottom:12px">
      ${icon('search', 19, 'muted')}
      <input id="gq" type="search" placeholder="Например, ПИН-31" autocomplete="off"
             enterkeyhint="search" spellcheck="false">
    </div>
    <div class="sheet-list" id="glist"></div>`;

  sheet({
    title: 'Выбор группы',
    body,
    onMount(root, close) {
      const input = root.querySelector('#gq');
      const list = root.querySelector('#glist');

      const draw = q => {
        const needle = q.trim().toLowerCase().replace(/\s+/g, '');
        const found = needle
          ? groups.filter(g => g.toLowerCase().replace(/\s+/g, '').includes(needle))
          : groups;
        if (!found.length) {
          list.innerHTML = emptyState('Такой группы нет', 'search');
          return;
        }
        list.innerHTML = listCard(found.slice(0, 120).map(g => listRow({
          title: g,
          id: g,
          cls: 'tap',
          value: g === settings.group ? '✓' : '',
        })));
      };

      draw('');
      input.addEventListener('input', () => draw(input.value));
      list.addEventListener('click', e => {
        const row = e.target.closest('[data-id]');
        if (!row) return;
        haptic('medium');
        save({ group: row.dataset.id });
        // Единственное место, где группу выбирают руками, — отсюда и
        // сообщаем её боту, чтобы в личке было то же расписание.
        syncGroup(row.dataset.id);
        close();
        onPick?.(row.dataset.id);
      });
      setTimeout(() => input.focus({ preventScroll: true }), 120);
    },
  });
}

/** Большая карточка новости с обложкой. */
export const newsCard = n => `
  <div class="news-card" data-news="${esc(n.id)}">
    ${n.cover ? `<img class="news-cover" src="img/${esc(n.cover)}" alt="" loading="lazy">` : ''}
    <div class="news-body">
      <div class="news-title">${esc(n.title)}</div>
      <div class="news-date">${esc(n.date)}</div>
    </div>
  </div>`;

/** Компактная строка новости для главной. */
export const newsRow = n => `
  <div class="news-row" data-news="${esc(n.id)}">
    ${n.cover ? `<img src="img/${esc(n.cover)}" alt="" loading="lazy">` : `<div class="icon-tile" style="width:62px;height:62px;border-radius:14px">${icon('news', 24)}</div>`}
    <div style="flex:1;min-width:0">
      <div class="news-row-title">${esc(n.title)}</div>
      <div class="news-date" style="margin-top:5px">${esc(n.date)}</div>
    </div>
  </div>`;

const MONTHS_GEN = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
const WEEKDAYS = ['воскресенье', 'понедельник', 'вторник', 'среда',
  'четверг', 'пятница', 'суббота'];

export const humanDate = (d = new Date()) =>
  `${WEEKDAYS[d.getDay()]}, ${d.getDate()} ${MONTHS_GEN[d.getMonth()]}`;

export const shortDate = (d = new Date()) =>
  `${d.getDate()} ${MONTHS_GEN[d.getMonth()]}`;
