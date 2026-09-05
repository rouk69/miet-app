// Общий поиск: новости, кружки, институты, разделы кампуса и группы.

import { icon } from '../icons.js';
import { esc, listCard, listRow, emptyState } from '../ui.js';
import { data, settings, save } from '../store.js';
import { go, switchTab } from '../router.js';
import { haptic } from '../tg.js';
import { screen } from './common.js';

const norm = s => String(s || '').toLowerCase().replace(/ё/g, 'е');

function collect(q) {
  const n = norm(q);
  if (n.length < 2) return [];
  const hit = t => norm(t).includes(n);
  const out = [];

  for (const g of data.groups || []) {
    if (norm(g).replace(/\s+/g, '').includes(n.replace(/\s+/g, ''))) {
      out.push({ kind: 'group', ico: 'users', title: g, sub: 'Учебная группа', id: g });
    }
    if (out.length > 6) break;
  }
  for (const c of data.clubs || []) {
    if (hit(c.title) || hit(c.tagline) || hit(c.cat)) {
      out.push({ kind: 'club', ico: c.icon || 'sparkles', title: c.title, sub: c.cat, id: c.id });
    }
  }
  for (const c of data.campus || []) {
    if (hit(c.title) || hit(c.sub)) {
      out.push({ kind: 'campusItem', ico: c.icon, title: c.title, sub: c.sub, id: c.id });
    }
  }
  for (const i of data.institutes || []) {
    if (hit(i.name) || hit(i.short) || hit(i.director) || (i.departments || []).some(hit)) {
      out.push({ kind: 'institute', ico: 'graduate', title: i.name, sub: i.short, id: i.id });
    }
  }
  for (const a of data.news || []) {
    if (hit(a.title) || hit(a.text)) {
      out.push({ kind: 'article', ico: 'news', title: a.title, sub: a.date, id: a.id });
    }
    if (out.length > 60) break;
  }
  return out.slice(0, 60);
}

export default async function searchScreen() {
  const node = screen({
    title: 'Поиск',
    subtitle: 'Пары, кружки, институты, новости',
    body: `
      <div class="search-box" style="margin-bottom:16px">
        ${icon('search', 19, 'muted')}
        <input id="q" type="search" placeholder="Что ищем?" autocomplete="off"
               enterkeyhint="search" spellcheck="false">
      </div>
      <div id="res"></div>`,
  });

  const input = node.querySelector('#q');
  const res = node.querySelector('#res');

  const HINTS = ['ПИН-31', 'хор', 'бассейн', 'столовая', 'общежитие', 'стипендия'];
  const idle = () => `
    <div class="section-head" style="margin-top:4px"><div class="section-title">Попробуй</div></div>
    <div class="pill-row">
      ${HINTS.map(h => `<button class="pill" data-hint="${esc(h)}">${esc(h)}</button>`).join('')}
    </div>`;

  const draw = () => {
    const q = input.value.trim();
    if (q.length < 2) { res.innerHTML = idle(); return; }
    const items = collect(q);
    res.innerHTML = items.length
      ? listCard(items.map((r, i) => listRow({
        ico: r.ico, title: r.title, sub: r.sub,
        chevron: true, id: String(i), cls: 'tap',
      })))
      : emptyState(`Ничего не нашлось по «${q}»`, 'search');
    res.dataset.payload = JSON.stringify(items);
  };

  draw();
  input.addEventListener('input', draw);
  setTimeout(() => input.focus({ preventScroll: true }), 150);

  node.addEventListener('click', e => {
    const hint = e.target.closest('[data-hint]');
    if (hint) { input.value = hint.dataset.hint; draw(); return; }
    const row = e.target.closest('.list-row[data-id]');
    if (!row) return;
    const items = JSON.parse(res.dataset.payload || '[]');
    const r = items[+row.dataset.id];
    if (!r) return;
    haptic('light');
    if (r.kind === 'group') {
      save({ group: r.id });
      return switchTab('schedule');
    }
    go(r.kind, { id: r.id });
  });

  void settings;
  return node;
}
