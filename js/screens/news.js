// Архив новостей МИЭТ и экран статьи.
//
// Это то, что собрано в data/app.json скриптами tools/ — снимок на момент
// сборки, с тегами и галереями. Живая лента (свежие новости и посты людей)
// живёт в screens/feed.js и приходит с сервера.

import { icon } from '../icons.js';
import { esc, emptyState, lightbox } from '../ui.js';
import { data, markRead } from '../store.js';
import { go } from '../router.js';
import { openLink } from '../tg.js';
import { screen, newsCard, iconBtn } from './common.js';

const key = t => String(t).toLowerCase().replace(/ё/g, 'е').trim();

/**
 * Список тегов по частоте. Сайт отдаёт один и тот же тег то с заглавной,
 * то со строчной («Наука» и «наука»), поэтому считаем без учёта регистра,
 * а показываем вариант с заглавной.
 */
function topTags(news, limit = 8) {
  const agg = new Map();
  for (const n of news) {
    for (const t of n.tags || []) {
      const k = key(t);
      const cur = agg.get(k) || { count: 0, label: t };
      cur.count++;
      if (/^[А-ЯЁA-Z]/.test(t) && !/^[А-ЯЁA-Z]/.test(cur.label)) cur.label = t;
      agg.set(k, cur);
    }
  }
  return [...agg.values()]
    .filter(v => v.count > 1)
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(v => v.label);
}

export default async function newsScreen() {
  const all = data.news || [];
  const tags = topTags(all);
  let active = 'all';

  const node = screen({
    title: 'Архив новостей',
    subtitle: `${all.length} публикаций, собранных с miet.ru`,
    actions: iconBtn('external', 'site'),
    body: `
      ${tags.length ? `<div class="pill-row" id="tags" style="margin-bottom:16px">
        <button class="pill active" data-tag="all">Все</button>
        ${tags.map(t => `<button class="pill" data-tag="${esc(t)}">${esc(t)}</button>`).join('')}
      </div>` : ''}
      <div class="stack" id="feed"></div>`,
  });

  const feed = node.querySelector('#feed');
  const draw = () => {
    const items = active === 'all'
      ? all
      : all.filter(n => (n.tags || []).some(t => key(t) === key(active)));
    feed.innerHTML = items.length
      ? items.map(newsCard).join('')
      : emptyState('По этому тегу пока пусто', 'inbox');
  };
  draw();

  node.querySelector('#tags')?.addEventListener('click', e => {
    const b = e.target.closest('[data-tag]');
    if (!b) return;
    active = b.dataset.tag;
    node.querySelectorAll('#tags .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    draw();
  });

  feed.addEventListener('click', e => {
    const c = e.target.closest('[data-news]');
    if (c) go('article', { id: c.dataset.news });
  });

  node.querySelector('[data-action="site"]').addEventListener('click', () =>
    openLink('https://www.miet.ru/news/'));

  return node;
}

/** Экран одной новости. */
export async function articleScreen({ id }) {
  const n = (data.news || []).find(x => x.id === String(id));
  if (!n) return screen({ title: 'Новость', body: emptyState('Новость не найдена', 'helpCircle') });
  markRead(n.id);

  const paragraphs = (n.text || '')
    .split(/\n{2,}/)
    .map(p => p.trim())
    .filter(Boolean);

  const node = screen({
    body: `
      ${n.cover ? `<img class="article-cover" src="img/${esc(n.cover)}" alt="">` : ''}
      <div class="article-title">${esc(n.title)}</div>
      <div class="news-date" style="margin-bottom:14px">${esc(n.date)}</div>
      ${n.tags?.length ? `<div class="tag-row" style="margin-bottom:18px">
        ${n.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}
      </div>` : ''}
      ${paragraphs.length
        ? `<div class="article-text">${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}</div>`
        : `<div class="row-subtitle" style="margin-bottom:18px">
             Полный текст — на сайте университета.
           </div>`}
      ${n.gallery?.length ? `
        <div class="section-head"><div class="section-title">Фото</div></div>
        <div class="gallery">
          ${n.gallery.map(g => `<img src="img/${esc(g)}" data-full="img/${esc(g)}" alt="" loading="lazy">`).join('')}
        </div>` : ''}
      <div style="margin-top:22px">
        <button class="btn-primary" id="open">
          ${icon('external', 18)} Открыть на miet.ru
        </button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(n.url));
  node.addEventListener('click', e => {
    const img = e.target.closest('[data-full]');
    if (img) lightbox(img.dataset.full);
  });
  return node;
}
