// Полезные ссылки: сервисы МИЭТ, учёба, студенческая жизнь, общежитие.

import { icon } from '../icons.js';
import { esc, listCard, listRow, emptyState } from '../ui.js';
import { data } from '../store.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

const norm = s => String(s || '').toLowerCase().replace(/ё/g, 'е');

export default async function linksScreen() {
  const groups = data.links || [];
  const total = groups.reduce((n, g) => n + g.items.length, 0);

  const node = screen({
    title: 'Ссылки',
    subtitle: `${total} сервисов и разделов МИЭТ`,
    body: `
      <div class="search-box" style="margin-bottom:18px">
        ${icon('search', 19, 'muted')}
        <input id="lq" type="search" placeholder="Найти ссылку" autocomplete="off"
               enterkeyhint="search" spellcheck="false">
      </div>
      <div id="groups"></div>
      <div class="fab-note">Все ссылки ведут на официальные ресурсы МИЭТ.</div>`,
  });

  const box = node.querySelector('#groups');
  const input = node.querySelector('#lq');

  const row = it => listRow({
    emoji: it.emoji, title: it.title, sub: it.sub,
    chevron: true, id: it.url, cls: 'tap',
  });

  const draw = q => {
    const needle = norm(q);
    if (needle.length >= 2) {
      const found = groups.flatMap(g => g.items)
        .filter(it => norm(it.title).includes(needle) || norm(it.sub).includes(needle));
      box.innerHTML = found.length
        ? listCard(found.map(row))
        : emptyState(`Ничего не нашлось по «${q}»`, '🔍');
      return;
    }
    box.innerHTML = groups.map(g => `
      <div class="section-head"><div class="section-title">${g.emoji} ${esc(g.title)}</div></div>
      ${listCard(g.items.map(row))}`).join('');
  };

  draw('');
  input.addEventListener('input', () => draw(input.value));

  node.addEventListener('click', e => {
    const r = e.target.closest('.list-row[data-id]');
    if (r) openLink(r.dataset.id);
  });

  return node;
}
