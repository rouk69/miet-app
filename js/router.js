// Роутер: стек экранов + нижняя навигация. Системная кнопка «Назад»
// Telegram показывается только когда есть куда возвращаться.

import { icon } from './icons.js';
import { BackButton, haptic, hapticSelect, inTelegram } from './tg.js';
import { track } from './api.js';

const routes = new Map();
const stack = [];
let appEl, navEl;

export const TABS = [
  { id: 'home', label: 'Главная', ico: 'home' },
  { id: 'schedule', label: 'Расписание', ico: 'calendar' },
  { id: 'news', label: 'Новости', ico: 'news' },
  { id: 'clubs', label: 'Кружки', ico: 'sparkles' },
  { id: 'profile', label: 'Профиль', ico: 'user' },
];

const isTab = name => TABS.some(t => t.id === name);

export function register(name, renderFn) {
  routes.set(name, renderFn);
}

export function init(appNode, navNode) {
  appEl = appNode;
  navEl = navNode;
  navEl.innerHTML = TABS.map(t => `
    <button class="bottom-nav-item" data-tab="${t.id}">
      ${icon(t.ico, 22)}
      <span class="bottom-nav-label">${t.label}</span>
    </button>`).join('');
  navEl.addEventListener('click', e => {
    const b = e.target.closest('[data-tab]');
    if (!b) return;
    hapticSelect();
    switchTab(b.dataset.tab);
  });
  navEl.hidden = false;
}

function syncNav() {
  const cur = stack[stack.length - 1];
  const tabName = stack[0]?.name;
  navEl.hidden = false;
  navEl.querySelectorAll('[data-tab]').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabName);
  });
  if (stack.length > 1) BackButton.show(back);
  else BackButton.hide();
  void cur;
}

async function paint() {
  const entry = stack[stack.length - 1];
  const fn = routes.get(entry.name);
  if (!fn) {
    appEl.innerHTML = `<div class="screen"><div class="empty-state">Экран «${entry.name}» не найден</div></div>`;
    return;
  }
  appEl.innerHTML = `<div class="screen"><div class="stack">
      <div class="skeleton" style="height:34px;width:60%"></div>
      <div class="skeleton" style="height:120px"></div>
      <div class="skeleton" style="height:84px"></div>
      <div class="skeleton" style="height:84px"></div>
    </div></div>`;
  let node;
  try {
    node = await fn(entry.params || {});
  } catch (err) {
    console.error(err);
    node = document.createElement('div');
    node.className = 'screen';
    node.innerHTML = `<div class="empty-state">
        <div style="font-size:34px">⚠️</div>
        <div>${err.message || 'Что-то пошло не так'}</div>
      </div>`;
  }
  appEl.innerHTML = '';
  appEl.append(node);

  // Вне Telegram системной кнопки «Назад» нет — рисуем свою поверх экрана.
  if (!inTelegram && stack.length > 1) {
    const btn = document.createElement('button');
    btn.className = 'icon-btn back-fab';
    btn.innerHTML = icon('chevronLeft', 20);
    btn.addEventListener('click', back);
    appEl.append(btn);
    // Над обложкой кнопка висит поверх картинки и ничему не мешает,
    // а вот на заголовок экрана она бы налезла — освобождаем место.
    node.classList.add('with-back');
  }

  window.scrollTo(0, entry.scrollTop || 0);
  syncNav();
}

export function go(name, params = {}) {
  const cur = stack[stack.length - 1];
  if (cur) cur.scrollTop = window.scrollY;
  stack.push({ name, params, scrollTop: 0 });
  // В учёт идёт только имя экрана. Параметры (какая новость, какой кружок)
  // не пишем: это уже слежка за человеком, а не за тем, чем пользуются.
  track('screen', name);
  // Своя запись в истории — чтобы аппаратная «Назад» на Android и кнопка
  // браузера вели по стеку экранов, а не закрывали приложение.
  try { history.pushState({ depth: stack.length }, ''); } catch { /* не критично */ }
  haptic('light');
  paint();
}

/** Пятится на экран назад. Саму работу делает обработчик popstate. */
export function back() {
  if (stack.length <= 1) return;
  haptic('light');
  try { history.back(); } catch { popScreen(); }
}

function popScreen() {
  if (stack.length <= 1) return;
  stack.pop();
  paint();
}

window.addEventListener('popstate', popScreen);

export function switchTab(name) {
  if (stack.length === 1 && stack[0].name === name) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }
  track('tab', name);
  stack.length = 0;
  stack.push({ name, params: {}, scrollTop: 0 });
  paint();
}

/** Перерисовать текущий экран, сохранив позицию прокрутки. */
export function refresh() {
  const cur = stack[stack.length - 1];
  if (cur) cur.scrollTop = window.scrollY;
  paint();
}

export const current = () => stack[stack.length - 1];
export const depth = () => stack.length;
export { isTab };
