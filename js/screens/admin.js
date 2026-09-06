// Админка: статистика, список людей, роли и доступы.
//
// Экран целиком живёт на сервере: здесь нет ни одной цифры из localStorage.
// Кнопка входа в профиле спрятана от посторонних, но это только удобство —
// решает всё равно сервер, и каждый запрос отсюда он проверяет заново.

import { icon } from '../icons.js';
import { esc, listCard, listRow, segmented, bindChoice, toggle, toast,
  emptyState, kpi } from '../ui.js';
import { get, post, account } from '../api.js';
import { data } from '../store.js';
import { TABS, go, refresh } from '../router.js';
import { haptic, hapticNotify, confirmDialog } from '../tg.js';
import { screen } from './common.js';

// Какую вкладку админки показывать. Живёт в модуле, а не в параметрах
// экрана: возврат из карточки человека должен вернуть на список, а не
// на статистику.
let tab = 'stats';

const TAB_META = Object.fromEntries(TABS.map(t => [t.id, t]));

const SCREEN_NAMES = {
  article: 'Новость', club: 'Кружок', campus: 'Кампус',
  campusItem: 'Раздел кампуса', institute: 'Институт', institutes: 'Институты',
  about: 'О МИЭТ', search: 'Поиск', links: 'Полезные ссылки',
  support: 'Поддержка', admin: 'Админка', adminUser: 'Карточка человека',
};

const ROLE_NAMES = { admin: 'Полный админ', moderator: 'Модератор', none: 'Без роли' };

// ─────────────── мелкие помощники ───────────────

/**
 * Время с сервера приходит в UTC строкой «2026-09-06 09:12:44». Без явного
 * Z браузер прочитал бы её как местное время и показал «через 3 часа».
 */
const parseTs = ts => new Date(String(ts || '').replace(' ', 'T') + 'Z');

function ago(ts) {
  if (!ts) return 'никогда';
  const min = Math.floor((Date.now() - parseTs(ts).getTime()) / 60000);
  if (min < 1) return 'только что';
  if (min < 60) return `${min} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const d = Math.floor(h / 24);
  if (d === 1) return 'вчера';
  if (d < 30) return `${d} дн назад`;
  return parseTs(ts).toLocaleDateString('ru-RU');
}

const dayLabel = iso => iso.slice(8, 10) + '.' + iso.slice(5, 7);

const fullName = u =>
  [u.first_name, u.last_name].filter(Boolean).join(' ') || `id ${u.id}`;

const avatar = (u, size = 44) => (u.photo_url
  ? `<img class="avatar" src="${esc(u.photo_url)}" alt=""
       style="width:${size}px;height:${size}px;object-fit:cover">`
  : `<div class="avatar" style="width:${size}px;height:${size}px;font-size:${Math.round(size / 2.6)}px">
       ${esc((u.first_name || '?')[0])}</div>`);

/**
 * Столбчатый график по дням. Своими руками, без библиотеки: у приложения
 * нет сборки, а тянуть чужой скрипт ради четырнадцати прямоугольников —
 * это лишние полтораста килобайт на телефон.
 */
function bars(title, series, tone = 'primary') {
  const max = Math.max(1, ...series.map(p => p.count));
  const last = series[series.length - 1] || { date: '', count: 0 };
  return `
    <div class="card chart-card">
      <div class="chart-title">${esc(title)}</div>
      <div class="chart-last">${esc(dayLabel(last.date))}: <b>${last.count}</b></div>
      <div class="bars">
        ${series.map((p, i) => `
          <div class="bar-col" title="${esc(p.date)}: ${p.count}">
            <div class="bar bar-${tone}" style="height:${Math.max(2, Math.round(p.count / max * 100))}%"></div>
            <div class="bar-day">${i % 3 === 0 || i === series.length - 1 ? esc(dayLabel(p.date)) : ''}</div>
          </div>`).join('')}
      </div>
    </div>`;
}

const errorCard = err => `
  <div class="card" style="padding:18px">
    <div class="row-title" style="margin-bottom:6px">Не получилось загрузить</div>
    <div class="row-subtitle">${esc(err.message)}</div>
  </div>`;

// ─────────────── экран админки ───────────────

export default async function adminScreen() {
  const node = screen({
    title: 'Админка',
    body: `
      <div class="pill-row admin-tabs" id="atabs">
        ${[['stats', 'Статистика'], ['users', 'Юзеры'], ['roles', 'Роли']]
    .map(([id, label]) => `
          <button class="pill ${tab === id ? 'active' : ''}" data-atab="${id}">${label}</button>`).join('')}
      </div>
      <div id="apane"><div class="skeleton" style="height:120px"></div></div>`,
  });

  const pane = node.querySelector('#apane');
  node.querySelector('#atabs').addEventListener('click', e => {
    const b = e.target.closest('[data-atab]');
    if (!b || b.dataset.atab === tab) return;
    tab = b.dataset.atab;
    haptic('light');
    refresh();
  });

  paint(pane);
  return node;
}

async function paint(pane) {
  try {
    if (tab === 'stats') pane.innerHTML = await statsPane();
    else if (tab === 'users') await usersPane(pane);
    else await rolesPane(pane);
  } catch (err) {
    pane.innerHTML = errorCard(err);
  }
}

// ─────────────── вкладка «Статистика» ───────────────

async function statsPane() {
  const s = await get('/api/admin/stats?days=14');
  const t = s.totals;

  const f = s.feed || {};
  const tiles = [
    [t.users, 'Всего пользователей'],
    [t.today, 'Активны сегодня'],
    [t.week, 'Активны за 7 дней'],
    [t.subs, 'Подписок на расписание'],
    [t.app, 'Открывали приложение'],
    [t.bot, 'Писали боту'],
    [t.premium, 'С Telegram Premium'],
    [t.blocked, 'Заблокировано'],
  ];

  const feedTiles = [
    [f.posts ?? 0, 'Постов в ленте'],
    [f.news ?? 0, 'Новостей с miet.ru'],
    [f.comments ?? 0, 'Комментариев'],
    [f.reads ?? 0, 'Прочтений'],
    [f.reactions ?? 0, 'Реакций'],
    [f.votes ?? 0, 'Голосов в опросах'],
    [f.pending ?? 0, 'Ждут одобрения'],
  ];

  const sections = s.tabs.length ? listCard(s.tabs.map(x => {
    const meta = TAB_META[x.name];
    return `
      <div class="list-row">
        <div class="icon-tile">${icon(meta?.ico || 'grid', 19)}</div>
        <div class="list-row-body">
          <div class="row-title">${esc(meta?.label || x.name)}</div>
          <div class="row-subtitle">${x.share}% от всех открытий вкладок</div>
        </div>
        <div class="list-row-value tnum">${x.count}</div>
      </div>`;
  })) : emptyState('Вкладки ещё никто не открывал', 'grid');

  const screens = s.screens.length ? listCard(s.screens.map(x => listRow({
    title: SCREEN_NAMES[x.name] || x.name,
    value: String(x.count),
  }))) : '';

  const groups = s.groups.length ? listCard(s.groups.map(x => listRow({
    title: x.name, value: String(x.count),
  }))) : emptyState('Группу пока никто не выбрал', 'users');

  const cmds = s.bot_commands.length ? listCard(s.bot_commands.map(x => listRow({
    title: x.name, value: String(x.count),
  }))) : '';

  return `
    <div class="kpi-grid">${tiles.map(([n, l]) => kpi(n, l)).join('')}</div>

    <div class="section-head"><div class="section-title">Лента</div></div>
    <p class="section-note">Посты людей, новости с сайта и что с ними делают.</p>
    <div class="kpi-grid">${feedTiles.map(([n, l]) => kpi(n, l)).join('')}</div>

    <div class="section-head"><div class="section-title">Активность</div></div>
    <p class="section-note">Заходы в приложение, новые люди и обращения к боту по дням.</p>
    <div class="stack">
      ${bars('Заходы в приложение', s.opens, 'primary')}
      ${bars('Новые пользователи', s.newcomers, 'success')}
      ${bars('Обращения к боту', s.commands, 'warning')}
    </div>

    <div class="section-head"><div class="section-title">Какие разделы смотрят</div></div>
    <p class="section-note">Сколько раз открывали каждую вкладку нижнего меню.</p>
    ${sections}

    ${screens ? `<div class="section-head"><div class="section-title">Экраны внутри разделов</div></div>${screens}` : ''}

    <div class="section-head"><div class="section-title">Популярные группы</div></div>
    <p class="section-note">Расписание какой группы люди выбрали своим.</p>
    ${groups}

    ${cmds ? `<div class="section-head"><div class="section-title">Что нажимают в боте</div></div>${cmds}` : ''}`;
}

// ─────────────── вкладка «Юзеры» ───────────────

const userRow = u => `
  <div class="list-row tap" data-user="${u.id}">
    ${avatar(u)}
    <div class="list-row-body">
      <div class="row-title">${esc(fullName(u))}${u.username ? ` · <span class="muted-name">@${esc(u.username)}</span>` : ''}</div>
      <div class="row-subtitle">
        ${u.blocked ? 'Заблокирован · ' : ''}${u.role && u.role !== 'none' ? esc(ROLE_NAMES[u.role]) + ' · ' : ''}Последний раз: ${esc(ago(u.last_seen))}
      </div>
    </div>
    <span class="chevron">${icon('chevronRight', 18)}</span>
  </div>`;

async function usersPane(pane) {
  let offset = 0;
  let query = '';
  const PAGE = 50;

  pane.innerHTML = `
    <p class="section-note" style="margin-top:0">
      Все, кто хоть раз открывал мини-апп или писал боту. Тапни, чтобы
      посмотреть подробную статистику.
    </p>
    <div class="search-box" style="margin-bottom:12px">
      ${icon('search', 19, 'muted')}
      <input id="uq" type="search" placeholder="Имя, ник, группа или id"
             autocomplete="off" spellcheck="false">
    </div>
    <div id="ulist"><div class="skeleton" style="height:120px"></div></div>
    <div id="umore"></div>`;

  const list = pane.querySelector('#ulist');
  const more = pane.querySelector('#umore');

  async function load(reset) {
    if (reset) offset = 0;
    const page = await get(
      `/api/admin/users?limit=${PAGE}&offset=${offset}&q=${encodeURIComponent(query)}`);
    const html = page.users.length
      ? listCard(page.users.map(userRow))
      : emptyState('Никого не нашлось', 'search');
    if (reset) list.innerHTML = html;
    else list.insertAdjacentHTML('beforeend', html);
    offset += page.users.length;
    more.innerHTML = offset < page.total
      ? `<button class="btn-secondary" id="umorebtn" style="margin-top:12px">
           Показать ещё · осталось ${page.total - offset}</button>`
      : (page.total ? `<div class="fab-note">Всего ${page.total}</div>` : '');
  }

  // Ввод «дребезжит» специально: список грузится с сервера, и запрос на
  // каждую букву при быстром наборе обгонял бы сам себя.
  let timer = null;
  pane.querySelector('#uq').addEventListener('input', e => {
    query = e.target.value.trim();
    clearTimeout(timer);
    timer = setTimeout(() => load(true).catch(err => { list.innerHTML = errorCard(err); }), 250);
  });

  pane.addEventListener('click', e => {
    if (e.target.closest('#umorebtn')) {
      load(false).catch(err => toast(err.message));
      return;
    }
    const row = e.target.closest('[data-user]');
    if (row) go('adminUser', { id: +row.dataset.user });
  });

  await load(true);
}

// ─────────────── вкладка «Роли» ───────────────

async function rolesPane(pane) {
  // Отдельного списка ролей на сервере нет: людей с ролью единицы, и проще
  // отфильтровать первую страницу, чем заводить ради этого маршрут.
  const page = await get('/api/admin/users?limit=200');
  const held = page.users.filter(u => (u.role && u.role !== 'none') || u.blocked);
  pane.innerHTML = `
    <p class="section-note" style="margin-top:0">
      Кому что выдано. Роль назначается в карточке человека — открой его во
      вкладке «Юзеры».
    </p>
    ${held.length ? listCard(held.map(userRow))
    : emptyState('Роли пока никому не выданы', 'shield')}
    <div class="section-head"><div class="section-title">Как это работает</div></div>
    <div class="card" style="padding:16px">
      <div class="row-subtitle" style="line-height:1.55">
        <b>Полный админ</b> видит всё и раздаёт роли. <b>Модератор</b> —
        только то, что отмечено тумблерами. Человеку без роли можно открыть
        доступ к разделам: саму админку он не увидит, но сможет писать в
        выбранное.<br><br>
        Владельцы из переменной <b>ADMIN_IDS</b> — постоянные админы: их
        нельзя ни разжаловать, ни заблокировать отсюда, иначе можно было бы
        одним тапом закрыть себе вход.
      </div>
    </div>`;
}

// ─────────────── карточка человека ───────────────

export async function adminUserScreen({ id }) {
  let card;
  try {
    card = await get(`/api/admin/users/${id}`);
  } catch (err) {
    return screen({ title: 'Человек', body: errorCard(err) });
  }

  const perms = await get('/api/admin/perms').catch(() => ({ perms: [], roles: [] }));
  const access = card.access;
  const clubs = data.clubs || [];

  const maxDay = Math.max(1, ...card.activity.map(d => d.count));
  const heat = card.activity.map(d => {
    const level = d.count === 0 ? 0 : Math.min(4, Math.ceil(d.count / maxDay * 4));
    return `<div class="heat-cell heat-${level}" title="${esc(d.date)}: ${d.count}"></div>`;
  }).join('');

  const feed = card.feed.length ? listCard(card.feed.map(f => {
    const label =
      f.kind === 'open' ? 'Открыл приложение'
        : f.kind === 'tab' ? `Вкладка «${TAB_META[f.name]?.label || f.name}»`
          : f.kind === 'screen' ? `Экран «${SCREEN_NAMES[f.name] || f.name}»`
            : `Бот: ${f.name}`;
    const ico = f.kind === 'open' ? 'zap'
      : f.kind === 'tab' ? 'grid' : f.kind === 'screen' ? 'fileText' : 'messageCircle';
    return listRow({ ico, title: label, sub: ago(f.ts) });
  })) : emptyState('Действий пока нет', 'clock');

  const canRole = account.is_admin && !access.root;
  const canBlock = (account.is_admin || account.perms.includes('users_block'))
    && !access.root && account.id !== card.id;

  const node = screen({
    title: fullName(card),
    body: `
      <div class="card" style="padding:14px 16px;display:flex;gap:12px;align-items:center">
        ${avatar(card, 46)}
        <div style="min-width:0">
          <div class="row-title">${esc(fullName(card))}${card.username ? ` · <span class="muted-name">@${esc(card.username)}</span>` : ''}</div>
          <div class="row-subtitle">
            ${access.root ? 'Владелец' : esc(ROLE_NAMES[access.role])}
            ${card.premium ? ' · Premium' : ''}
            · Последний раз: ${esc(ago(card.last_seen))}
          </div>
          <div class="row-subtitle">
            id ${card.id}${card.group ? ` · группа ${esc(card.group)}` : ' · группа не выбрана'}
          </div>
        </div>
      </div>

      ${canBlock ? `
        <button class="btn-secondary danger-btn" id="block" style="margin-top:12px">
          ${access.blocked ? 'Разблокировать' : 'Заблокировать'}
        </button>` : ''}

      <div class="kpi-grid" style="margin-top:12px">
        ${kpi(card.counts.opens, 'Заходов в приложение')}
        ${kpi(card.counts.tabs, 'Открытий вкладок')}
        ${kpi(card.counts.screens, 'Открытий экранов')}
        ${kpi(card.counts.commands, 'Обращений к боту')}
      </div>

      <div class="section-head"><div class="section-title">Активность за 30 дней</div></div>
      <div class="card heat-card">${heat}</div>

      <div class="section-head"><div class="section-title">Лента действий</div></div>
      ${feed}

      ${canRole ? `
        <div class="section-head"><div class="section-title">Роль в админке</div></div>
        ${segmented([
      { id: 'admin', label: 'Полный админ' },
      { id: 'moderator', label: 'Модератор' },
      { id: 'none', label: 'Без роли' },
    ], access.role, 'role')}
        <div class="list-card" id="perms" style="margin-top:12px">
          ${perms.perms.map(p => `
            <div class="list-row">
              <div class="list-row-body"><div class="row-title">${esc(p.label)}</div></div>
              ${toggle(access.granted.includes(p.id), p.id)}
            </div>`).join('')}
        </div>
        <button class="btn-primary" id="saveRole" style="margin-top:14px">Сохранить роль</button>

        <div class="section-head"><div class="section-title">Доступ к разделам</div></div>
        <p class="section-note">
          Это не роль в админке — человек не получит саму админку, только
          сможет писать в выбранное.
        </p>
        <div class="list-card" id="sections">
          ${clubs.map(c => `
            <div class="list-row">
              <div class="icon-tile">${icon(c.icon || 'sparkles', 19)}</div>
              <div class="list-row-body"><div class="row-title">Кружок «${esc(c.title)}»</div></div>
              ${toggle(access.granted_sections.includes(c.id), 'sec:' + c.id)}
            </div>`).join('')}
        </div>
        <button class="btn-primary" id="saveSections" style="margin-top:14px">Сохранить доступ</button>
      ` : `
        <div class="section-head"><div class="section-title">Роль</div></div>
        <div class="card" style="padding:16px">
          <div class="row-subtitle">
            ${access.root
    ? 'Это владелец из ADMIN_IDS — его роль задаётся переменной окружения и отсюда не меняется.'
    : 'Роли раздаёт только полный админ.'}
          </div>
        </div>`}`,
  });

  // Тумблеры переключаются на месте, а сохраняются кнопкой — как на любом
  // экране настроек: случайный тап по списку из девяти прав не должен
  // немедленно менять человеку доступ.
  node.addEventListener('click', e => {
    const t = e.target.closest('[data-toggle]');
    if (!t) return;
    t.classList.toggle('on');
    haptic('light');
  });

  if (canRole) {
    let role = access.role;
    bindChoice(node, 'role', v => { role = v; }, 'seg');

    node.querySelector('#saveRole').addEventListener('click', async () => {
      const picked = [...node.querySelectorAll('#perms [data-toggle].on')]
        .map(t => t.dataset.toggle);
      const sections = [...node.querySelectorAll('#sections [data-toggle].on')]
        .map(t => t.dataset.toggle.slice(4));
      try {
        await post(`/api/admin/users/${card.id}/role`,
          { role, perms: picked, sections });
        hapticNotify('success');
        toast(role === 'none' ? 'Роль снята' : `Сохранено: ${ROLE_NAMES[role]}`);
      } catch (err) {
        toast(err.message);
      }
    });

    // Роль и доступы уходят одним запросом — сервер хранит их в одной
    // строке. Кнопки две, потому что на экране это два разных разговора,
    // и «Сохранить доступ» внизу списка кружков ищут именно там.
    node.querySelector('#saveSections').addEventListener('click', () => {
      node.querySelector('#saveRole').click();
    });
  }

  const blockBtn = node.querySelector('#block');
  blockBtn?.addEventListener('click', async () => {
    const next = !access.blocked;
    if (next && !await confirmDialog(
      `Заблокировать ${fullName(card)}? Бот перестанет отвечать, приложение покажет заглушку.`)) return;
    try {
      await post(`/api/admin/users/${card.id}/block`, { blocked: next });
      access.blocked = next;
      blockBtn.textContent = next ? 'Разблокировать' : 'Заблокировать';
      hapticNotify('success');
      toast(next ? 'Заблокирован' : 'Разблокирован');
    } catch (err) {
      toast(err.message);
    }
  });

  return node;
}
