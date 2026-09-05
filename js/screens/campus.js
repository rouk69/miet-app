// Инфраструктура кампуса: библиотека, столовая, общежития, спорт и прочее.

import { icon } from '../icons.js';
import { esc, emptyState, contactRows, listCard, listRow, lightbox } from '../ui.js';
import { data } from '../store.js';
import { go } from '../router.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

export default async function campusScreen() {
  const items = data.campus || [];
  const node = screen({
    title: 'Кампус',
    subtitle: 'Всё, что есть в университете',
    body: `<div class="stack">
        ${listCard(items.map(c => listRow({
      ico: c.icon, title: c.title, sub: c.sub,
      chevron: true, id: c.id, cls: 'tap',
    })))}
        <div class="section-head"><div class="section-title">Учёба</div></div>
        ${listCard([
      listRow({ ico: 'graduate', title: 'Институты', sub: `${(data.institutes || []).length} институтов и кафедр`, chevron: true, id: '@institutes', cls: 'tap' }),
      listRow({ ico: 'landmark', title: 'О МИЭТ', sub: 'История, контакты, реквизиты', chevron: true, id: '@about', cls: 'tap' }),
      listRow({ ico: 'link', title: 'Полезные ссылки', sub: 'Сервисы и разделы сайта', chevron: true, id: '@links', cls: 'tap' }),
      listRow({ ico: 'lifebuoy', title: 'Поддержка', sub: 'Автор приложения', chevron: true, id: '@support', cls: 'tap' }),
    ])}
      </div>`,
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('.list-row[data-id]');
    if (!row) return;
    const id = row.dataset.id;
    if (id === '@institutes') return go('institutes');
    if (id === '@about') return go('about');
    if (id === '@links') return go('links');
    if (id === '@support') return go('support');
    go('campusItem', { id });
  });
  return node;
}

/** Экран одного раздела кампуса. */
export async function campusItemScreen({ id }) {
  const c = (data.campus || []).find(x => x.id === id);
  if (!c) return screen({ title: 'Раздел', body: emptyState('Раздел не найден', 'helpCircle') });

  const paragraphs = (c.text || '').split(/\n{2,}/).map(p => p.trim()).filter(Boolean);

  const node = screen({
    body: `
      ${c.photos?.[0] ? `<div class="hero">
        <img src="img/${esc(c.photos[0])}" alt="">
        <div class="hero-fade"></div>
      </div>` : ''}
      <div class="screen-top">
        <div>
          <h1 class="h1-page small">${esc(c.title)}</h1>
          <p class="subtitle-page">${esc(c.sub)}</p>
        </div>
      </div>

      ${paragraphs.length ? `<div class="article-text" style="font-size:15px">
        ${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}
      </div>` : ''}

      ${c.photos?.length > 1 ? `
        <div class="section-head"><div class="section-title">Фото</div></div>
        <div class="gallery">
          ${c.photos.slice(1).map(p => `<img src="img/${esc(p)}" data-full="img/${esc(p)}" alt="" loading="lazy">`).join('')}
        </div>` : ''}

      ${(c.lead || c.phone || c.email || c.room) ? `
        <div class="section-head"><div class="section-title">Контакты</div></div>
        ${contactRows(c)}` : ''}

      ${c.links?.length ? `
        <div class="section-head"><div class="section-title">Разделы на сайте</div></div>
        ${listCard(c.links.map((l, i) => listRow({
      title: l.title, chevron: true, id: `link${i}`, cls: 'tap',
    })))}` : ''}

      <div style="margin-top:20px">
        <button class="btn-primary" id="open">${icon('external', 18)} Открыть на miet.ru</button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(c.url));
  node.addEventListener('click', e => {
    const img = e.target.closest('[data-full]');
    if (img) return lightbox(img.dataset.full);
    const row = e.target.closest('.list-row[data-id^="link"]');
    if (row) {
      const i = +row.dataset.id.replace('link', '');
      openLink(c.links[i]?.url);
    }
  });
  return node;
}
