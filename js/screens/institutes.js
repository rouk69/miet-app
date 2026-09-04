// Институты МИЭТ: список и карточка института с кафедрами и контактами.

import { icon } from '../icons.js';
import { esc, emptyState, contactRows, listCard, listRow } from '../ui.js';
import { data } from '../store.js';
import { go } from '../router.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';
import { plural } from './schedule.js';

export default async function institutesScreen() {
  const items = data.institutes || [];
  const node = screen({
    title: 'Институты',
    subtitle: `${items.length} ${plural(items.length, 'институт', 'института', 'институтов')} МИЭТ`,
    body: `<div class="stack">
      ${items.map(i => `
        <div class="tile" data-inst="${esc(i.id)}">
          ${i.photo ? `<img class="tile-cover" src="img/${esc(i.photo)}" alt="" loading="lazy">` : ''}
          <div class="tile-body">
            <div class="tile-head">
              <span class="tile-title">${esc(i.name)}</span>
              ${i.short ? `<span class="chip">${esc(i.short)}</span>` : ''}
            </div>
            ${i.director ? `<div class="tile-sub">${icon('teacher', 13)} ${esc(i.director)}</div>` : ''}
            ${i.departments?.length ? `<div class="chip-row">
              <span class="chip">${i.departments.length} ${plural(i.departments.length, 'подразделение', 'подразделения', 'подразделений')}</span>
              ${i.room ? `<span class="chip">${icon('door', 13)} ${esc(i.room)}</span>` : ''}
            </div>` : ''}
          </div>
        </div>`).join('')}
    </div>`,
  });

  node.addEventListener('click', e => {
    const t = e.target.closest('[data-inst]');
    if (t) go('institute', { id: t.dataset.inst });
  });
  return node;
}

export async function instituteScreen({ id }) {
  const i = (data.institutes || []).find(x => x.id === id);
  if (!i) return screen({ title: 'Институт', body: emptyState('Институт не найден', '🤷') });

  const node = screen({
    body: `
      ${i.photo ? `<div class="hero">
        <img src="img/${esc(i.photo)}" alt="">
        <div class="hero-fade"></div>
      </div>` : ''}
      <div class="screen-top">
        <div>
          <h1 class="h1-page small">${esc(i.name)}</h1>
          ${i.short ? `<p class="subtitle-page">${esc(i.short)}</p>` : ''}
        </div>
      </div>

      ${i.about ? `<div class="article-text" style="font-size:15px;margin-bottom:6px">
        <p>${esc(i.about)}</p></div>` : ''}

      <div class="section-head"><div class="section-title">Контакты</div></div>
      ${contactRows(i) || emptyState('Контакты — на сайте института', '📞')}

      ${i.departments?.length ? `
        <div class="section-head"><div class="section-title">Кафедры и подразделения</div></div>
        ${listCard(i.departments.map(d => listRow({ title: d })))}` : ''}

      <div style="margin-top:20px">
        <button class="btn-primary" id="open">${icon('external', 18)} Открыть на miet.ru</button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(i.url));
  return node;
}
