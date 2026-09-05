// Кружки, секции и студенческие объединения МИЭТ.

import { icon } from '../icons.js';
import { esc, emptyState, contactRows, lightbox, toast, listCard, listRow } from '../ui.js';
import { data, toggleFavorite, isFavorite, settings } from '../store.js';
import { go } from '../router.js';
import { openLink, haptic } from '../tg.js';
import { screen, iconBtn } from './common.js';

const CATS = ['Все', 'Спорт', 'Творчество', 'Медиа', 'Наука',
  'Добро', 'Досуг', 'Объединения', 'Избранное'];

const clubCard = c => `
  <div class="tile" data-club="${esc(c.id)}">
    ${c.photos?.[0] ? `<img class="tile-cover" src="img/${esc(c.photos[0])}" alt="" loading="lazy">` : ''}
    <div class="tile-body">
      <div class="tile-head">
        <span class="tile-icon">${icon(c.icon || 'sparkles', 17)}</span>
        <span class="tile-title">${esc(c.title)}</span>
        ${isFavorite(c.id) ? '<span style="color:var(--danger)">♥</span>' : ''}
      </div>
      ${c.tagline ? `<div class="tile-sub">${esc(c.tagline)}</div>` : ''}
      <div class="chip-row">
        <span class="chip">${esc(c.cat)}</span>
        ${c.place ? `<span class="chip">${icon('pin', 13)} ${esc(c.place)}</span>` : ''}
        ${c.free ? `<span class="chip free">${esc(c.free)}</span>` : ''}
      </div>
    </div>
  </div>`;

export default async function clubsScreen() {
  const all = data.clubs || [];
  let cat = 'Все';

  const node = screen({
    title: 'Кружки',
    subtitle: `${all.length} клубов, секций и объединений МИЭТ`,
    actions: iconBtn('search', 'search'),
    body: `
      <div class="pill-row" id="cats" style="margin-bottom:16px">
        ${CATS.map(c => `<button class="pill ${c === cat ? 'active' : ''}" data-cat="${esc(c)}">${esc(c)}</button>`).join('')}
      </div>
      <div class="stack" id="list"></div>

      <div class="section-head"><div class="section-title">Где всё происходит</div></div>
      <div class="list-card">
        <div class="list-row tap" data-campus="dk">
          <div class="icon-tile">${icon('drama', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">Дом культуры МИЭТ</div>
            <div class="row-subtitle">Зал на 640 мест, репетиционные</div>
          </div>
          <span class="chevron">${icon('chevronRight', 18)}</span>
        </div>
        <div class="list-row tap" data-campus="sport">
          <div class="icon-tile">${icon('stadium', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">Спорткомплекс</div>
            <div class="row-subtitle">Бассейн, залы, стадион</div>
          </div>
          <span class="chevron">${icon('chevronRight', 18)}</span>
        </div>
      </div>`,
  });

  const list = node.querySelector('#list');
  const draw = () => {
    const items = cat === 'Все' ? all
      : cat === 'Избранное' ? all.filter(c => isFavorite(c.id))
        : all.filter(c => c.cat === cat);
    list.innerHTML = items.length
      ? items.map(clubCard).join('')
      : emptyState(cat === 'Избранное'
        ? 'Отметь кружок сердечком — он появится здесь'
        : 'В этой категории пока пусто', 'sparkles');
  };
  draw();

  node.querySelector('#cats').addEventListener('click', e => {
    const b = e.target.closest('[data-cat]');
    if (!b) return;
    cat = b.dataset.cat;
    node.querySelectorAll('#cats .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    draw();
  });

  node.addEventListener('click', e => {
    const c = e.target.closest('[data-club]');
    if (c) return go('club', { id: c.dataset.club });
    const s = e.target.closest('[data-campus]');
    if (s) return go('campusItem', { id: s.dataset.campus });
    if (e.target.closest('[data-action="search"]')) return go('search');
  });

  return node;
}

/** Экран одного кружка. */
export async function clubScreen({ id }) {
  const c = (data.clubs || []).find(x => x.id === id);
  if (!c) return screen({ title: 'Кружок', body: emptyState('Не найдено', 'helpCircle') });

  const paragraphs = (c.about || '').split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
  const fav = isFavorite(c.id);

  const node = screen({
    body: `
      ${c.photos?.[0] ? `<div class="hero">
        <img src="img/${esc(c.photos[0])}" alt="">
        <div class="hero-fade"></div>
      </div>` : ''}
      <div class="screen-top">
        <div>
          <h1 class="h1-page small">${esc(c.title)}</h1>
          ${c.tagline ? `<p class="subtitle-page">${esc(c.tagline)}</p>` : ''}
        </div>
        <div class="header-actions">
          <button class="icon-btn" id="fav" style="color:${fav ? 'var(--danger)' : 'var(--text-tertiary)'}">
            ${icon('heart', 19)}
          </button>
        </div>
      </div>

      <div class="chip-row" style="margin:0 0 18px">
        <span class="chip">${esc(c.cat)}</span>
        ${c.place ? `<span class="chip">${icon('pin', 13)} ${esc(c.place)}</span>` : ''}
        ${c.free ? `<span class="chip free">${esc(c.free)}</span>` : ''}
      </div>

      ${paragraphs.length ? `<div class="article-text" style="font-size:15px">
        ${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}
      </div>` : ''}

      ${c.photos?.length > 1 ? `
        <div class="section-head"><div class="section-title">Фото</div></div>
        <div class="gallery">
          ${c.photos.slice(1).map(p => `<img src="img/${esc(p)}" data-full="img/${esc(p)}" alt="" loading="lazy">`).join('')}
        </div>` : ''}

      ${c.social?.length ? `
        <div class="section-head"><div class="section-title">Соцсети</div></div>
        ${listCard(c.social.map((s, i) => listRow({
      ico: s.label === 'Telegram' ? 'messageCircle' : s.label === 'YouTube' ? 'video' : 'globe',
      title: s.label, sub: s.url.replace(/^https?:\/\//, '').slice(0, 46),
      chevron: true, id: `soc${i}`, cls: 'tap',
    })))}` : ''}

      ${contactRows(c) ? `
        <div class="section-head"><div class="section-title">Контакты</div></div>
        ${contactRows(c)}` : ''}

      <div style="margin-top:20px">
        <button class="btn-primary" id="open">${icon('external', 18)} Страница на miet.ru</button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(c.url));
  node.querySelector('#fav').addEventListener('click', e => {
    const added = toggleFavorite(c.id);
    haptic('medium');
    e.currentTarget.style.color = added ? 'var(--danger)' : 'var(--text-tertiary)';
    toast(added ? 'Добавлено в избранное' : 'Убрано из избранного');
  });
  node.addEventListener('click', e => {
    const img = e.target.closest('[data-full]');
    if (img) return lightbox(img.dataset.full);
    const soc = e.target.closest('.list-row[data-id^="soc"]');
    if (soc) openLink(c.social[+soc.dataset.id.replace('soc', '')]?.url);
  });

  void settings;
  return node;
}
