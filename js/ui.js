// Мелкие компоненты по образцу дизайн-кита: списки-карточки, пилюли,
// сегмент-контрол, шторка снизу, пустое состояние.

import { icon } from './icons.js';
import { haptic, hapticSelect } from './tg.js';

export const esc = s => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

/** Строит DOM-узел из HTML-строки. */
export function el(html) {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

/** Делегирование: клик по любому потомку, подходящему под селектор. */
export function on(root, selector, handler, event = 'click') {
  root.addEventListener(event, e => {
    const target = e.target.closest(selector);
    if (target && root.contains(target)) handler(e, target);
  });
}

// ─────────────── строки списка ───────────────

export function listRow({ emoji, ico, title, sub, value, chevron = false, id = '', cls = '' }) {
  const left = emoji
    ? `<div class="emoji-tile">${emoji}</div>`
    : ico
      ? `<div class="list-row-icon" style="background:var(--primary-dim);color:var(--primary)">${icon(ico, 18)}</div>`
      : '';
  return `
    <div class="list-row ${cls}" ${id ? `data-id="${esc(id)}"` : ''}>
      ${left}
      <div class="list-row-body">
        <div class="row-title">${esc(title)}</div>
        ${sub ? `<div class="row-subtitle">${esc(sub)}</div>` : ''}
      </div>
      ${value ? `<div class="list-row-value">${esc(value)}</div>` : ''}
      ${chevron ? `<span class="chevron">${icon('chevronRight', 18)}</span>` : ''}
    </div>`;
}

export const listCard = rows => `<div class="list-card">${rows.join('')}</div>`;

// ─────────────── пилюли и сегменты ───────────────

/** items: [{id, label}] — горизонтальный скроллящийся ряд. */
export function pillRow(items, activeId, name = 'pill') {
  return `<div class="pill-row" data-pills="${name}">${items.map(i => `
    <button class="pill ${i.id === activeId ? 'active' : ''}" data-pill="${esc(i.id)}">
      ${i.emoji ? `${i.emoji} ` : ''}${esc(i.label)}
    </button>`).join('')}</div>`;
}

export function segmented(items, activeId, name = 'seg') {
  return `<div class="segmented" data-seg="${name}">${items.map(i => `
    <button class="segmented-item ${i.id === activeId ? 'active' : ''}" data-segitem="${esc(i.id)}">
      ${esc(i.label)}
    </button>`).join('')}</div>`;
}

/** Вешает обработчик выбора на ряд пилюль или сегмент-контрол. */
export function bindChoice(root, name, onChange, kind = 'pill') {
  const attr = kind === 'pill' ? 'pill' : 'segitem';
  const container = root.querySelector(`[data-${kind === 'pill' ? 'pills' : 'seg'}="${name}"]`);
  if (!container) return;
  container.addEventListener('click', e => {
    const btn = e.target.closest(`[data-${attr}]`);
    if (!btn) return;
    const active = kind === 'pill' ? 'pill' : 'segmented-item';
    container.querySelectorAll(`.${active}`).forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    hapticSelect();
    onChange(btn.dataset[attr]);
  });
}

// ─────────────── прочее ───────────────

export const emptyState = (text, emoji = '🗂') => `
  <div class="empty-state">
    <div style="font-size:34px">${emoji}</div>
    <div>${esc(text)}</div>
  </div>`;

export const toggle = (on, id = '') =>
  `<div class="toggle ${on ? 'on' : ''}" ${id ? `data-toggle="${esc(id)}"` : ''}>
     <div class="toggle-knob"></div>
   </div>`;

export const kpi = (number, label) =>
  `<div class="kpi-tile"><div class="kpi-number">${esc(number)}</div>
   <div class="kpi-label">${esc(label)}</div></div>`;

export const skeleton = (h = 74) =>
  `<div class="skeleton" style="height:${h}px"></div>`;

// ─────────────── шторка снизу ───────────────

const layer = () => document.getElementById('layer');

/**
 * Шторка снизу. Возвращает объект с close(). Контент передаётся строкой,
 * onMount получает корневой узел тела — там можно навесить обработчики.
 */
export function sheet({ title, body, onMount, cancel = 'Отмена', height }) {
  const backdrop = el('<div class="sheet-backdrop"></div>');
  const node = el(`
    <div class="sheet">
      <div class="sheet-handle"></div>
      <div class="sheet-header">
        <button class="sheet-cancel">${esc(cancel)}</button>
        <div class="sheet-title">${esc(title)}</div>
      </div>
      <div class="sheet-body" ${height ? `style="max-height:${height}"` : ''}>${body}</div>
    </div>`);

  let closed = false;
  function close() {
    if (closed) return;
    closed = true;
    node.style.transition = 'transform .2s ease';
    node.style.transform = 'translate(-50%, 100%)';
    backdrop.style.transition = 'opacity .2s ease';
    backdrop.style.opacity = '0';
    setTimeout(() => { backdrop.remove(); node.remove(); }, 200);
    document.body.style.overflow = '';
  }

  backdrop.addEventListener('click', close);
  node.querySelector('.sheet-cancel').addEventListener('click', () => { haptic(); close(); });

  layer().append(backdrop, node);
  document.body.style.overflow = 'hidden';
  onMount?.(node.querySelector('.sheet-body'), close);
  return { close, node };
}

/** Короткое всплывающее сообщение по центру снизу. */
export function toast(message) {
  const t = el(`<div style="
    position:fixed; left:50%; bottom:calc(100px + var(--safe-bottom));
    transform:translateX(-50%); z-index:200; max-width:80%;
    background:rgba(21,23,28,.9); color:#fff; font-size:14px; font-weight:600;
    padding:11px 18px; border-radius:999px; text-align:center;
    opacity:0; transition:opacity .2s ease;">${esc(message)}</div>`);
  layer().append(t);
  requestAnimationFrame(() => { t.style.opacity = '1'; });
  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 250);
  }, 1900);
}

/** Полноэкранный просмотр фото по тапу. */
export function lightbox(src) {
  const b = el(`<div style="
    position:fixed; inset:0; z-index:150; background:rgba(0,0,0,.92);
    display:flex; align-items:center; justify-content:center; padding:20px;">
    <img src="${esc(src)}" style="max-width:100%; max-height:100%;
      border-radius:14px; object-fit:contain">
  </div>`);
  b.addEventListener('click', () => b.remove());
  layer().append(b);
}

/** Ряд контактов: телефон, почта, аудитория — каждый кликабелен. */
export function contactRows({ lead, phone, inner, email, room, address, site }) {
  const rows = [];
  if (lead) rows.push(listRow({ ico: 'teacher', title: lead, sub: 'Руководитель' }));
  if (phone) rows.push(`<a class="list-row tap" href="tel:${esc(phone.replace(/[^\d+]/g, ''))}">
      <div class="list-row-icon" style="background:var(--primary-dim);color:var(--primary)">${icon('phone', 18)}</div>
      <div class="list-row-body"><div class="row-title">${esc(phone)}</div>
      <div class="row-subtitle">${inner ? `Внутренний ${esc(inner)}` : 'Телефон'}</div></div>
    </a>`);
  if (email) rows.push(`<a class="list-row tap" href="mailto:${esc(email)}">
      <div class="list-row-icon" style="background:var(--primary-dim);color:var(--primary)">${icon('mail', 18)}</div>
      <div class="list-row-body"><div class="row-title">${esc(email)}</div>
      <div class="row-subtitle">Почта</div></div>
    </a>`);
  if (room) rows.push(listRow({ ico: 'door', title: `Аудитория ${room}`, sub: 'Где найти' }));
  if (address) rows.push(listRow({ ico: 'pin', title: address, sub: 'Адрес' }));
  if (site) rows.push(listRow({ ico: 'external', title: site, sub: 'Сайт' }));
  return rows.length ? listCard(rows) : '';
}
