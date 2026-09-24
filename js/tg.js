// Интеграция с Telegram Mini Apps. Портировано с tg.ts из дизайн-кита:
// safe-area, тактильная отдача, кнопка «Назад», цвет шапки.
// Вне Telegram (обычный браузер) всё молча деградирует — приложение работает.

export const tg = window.Telegram?.WebApp || null;
export const inTelegram = Boolean(tg?.initData !== undefined && tg?.platform !== 'unknown');

// Метод может быть на объекте, но отсутствовать в текущей версии клиента —
// тогда вызов бросает WebAppMethodUnsupported. Проверять поле недостаточно.
function supports(minVersion) {
  return Boolean(tg?.isVersionAtLeast?.(minVersion));
}

// В полноэкранном режиме контент уходит под статусбар и под пилюли
// Telegram, поэтому складываем системный отступ (вырез, полоса жестов)
// и contentSafeAreaInset — то место, которое клиент занял своими
// кнопками. Из этой суммы `.screen` берёт верхний отступ, и заголовок
// экрана под пилюли не залезает.
function applySafeArea() {
  if (!tg) return;
  const sys = tg.safeAreaInset || { top: 0, bottom: 0 };
  const content = tg.contentSafeAreaInset || { top: 0, bottom: 0 };
  const top = Math.max(0, (sys.top || 0) + (content.top || 0));
  const bottom = Math.max(0, sys.bottom || 0);
  document.documentElement.style.setProperty('--tg-safe-top', `${top}px`);
  document.documentElement.style.setProperty('--tg-safe-bottom', `${bottom}px`);
}

export function syncChrome(theme) {
  const color = theme === 'dark' ? '#0F1014' : '#EEF0F5';
  try {
    tg?.setHeaderColor?.(color);
    tg?.setBackgroundColor?.(color);
  } catch { /* старый клиент — не критично */ }
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', color);
}

// Полный экран вместо полосы Telegram.
//
// В обычном режиме клиент рисует сверху свою полосу с именем бота и
// отчёркивает её линией — снаружи это выглядит рамкой вокруг чужой
// страницы, вставленной в переписку. В полноэкранном полосы нет, а
// «закрыть», «свернуть» и «меню» лежат накладными пилюлями поверх
// содержимого: приложение выглядит приложением, а не сайтом в окне.
// Кнопки при этом никуда не деваются — они те же, просто без рамки.
//
// Отступ под пилюли приходит в contentSafeAreaInset и складывается с
// системным в --tg-safe-top (см. applySafeArea), из которого `.screen`
// берёт верхний отступ. Поэтому заголовок экрана и круглые кнопки
// рядом с ним под пилюли не залезают.
//
// Только мобильные клиенты: на десктопе мини-приложение и так в своём
// окне, и полноэкранный режим там либо не поддержан, либо разворачивает
// окно на весь монитор — ни то ни другое не нужно.
const DESKTOP = ['tdesktop', 'macos', 'web', 'weba', 'webk', 'unknown'];

function goFullscreen() {
  if (!supports('8.0') || !tg?.requestFullscreen) return;
  if (DESKTOP.includes(tg.platform)) return;
  try {
    tg.requestFullscreen();
  } catch { /* клиент отказал — остаёмся в обычном режиме */ }
}

// Чем стилям отличить один режим от другого: в полноэкранном пилюли
// Telegram лежат поверх нашего первого экрана.
function markFullscreen() {
  document.documentElement.classList.toggle('tg-fullscreen',
    Boolean(tg?.isFullscreen));
  applySafeArea();
}

export function initTelegram(theme = 'light', onThemeChange = null) {
  if (!tg) return;
  try {
    tg.ready();
    tg.expand();
    // Вертикальные свайпы по умолчанию сворачивают мини-апп — это ломает
    // прокрутку длинных списков и шторок.
    tg.disableVerticalSwipes?.();
    syncChrome(theme);
    applySafeArea();
    goFullscreen();
    tg.onEvent?.('safeAreaChanged', applySafeArea);
    tg.onEvent?.('contentSafeAreaChanged', applySafeArea);
    tg.onEvent?.('fullscreenChanged', markFullscreen);
    // Отказ тоже событие: клиент старый или режим запрещён — тогда
    // живём в обычном, и пометки на странице быть не должно.
    tg.onEvent?.('fullscreenFailed', markFullscreen);
    // Человек может переключить тему Telegram, не закрывая мини-апп.
    // Кто на это откликается, решает вызывающий: у него настройки.
    if (onThemeChange) tg.onEvent?.('themeChanged', onThemeChange);
  } catch { /* вне Telegram просто нет WebApp API */ }
}

// Тактильная отдача появилась в 6.1 — без проверки старый клиент сыпал
// предупреждениями в консоль на каждое нажатие.
export function haptic(style = 'light') {
  if (!supports('6.1')) return;
  try { tg?.HapticFeedback?.impactOccurred?.(style); } catch { /* не критично */ }
}

export function hapticNotify(type) {
  if (!supports('6.1')) return;
  try { tg?.HapticFeedback?.notificationOccurred?.(type); } catch { /* не критично */ }
}

export function hapticSelect() {
  if (!supports('6.1')) return;
  try { tg?.HapticFeedback?.selectionChanged?.(); } catch { /* не критично */ }
}

/** Аппаратная/системная кнопка «Назад» Telegram. */
export const BackButton = {
  _handler: null,
  show(handler) {
    this._handler = handler;
    if (!tg?.BackButton) return;
    try {
      tg.BackButton.onClick(handler);
      tg.BackButton.show();
    } catch { /* не критично */ }
  },
  hide() {
    if (!tg?.BackButton) return;
    try {
      if (this._handler) tg.BackButton.offClick(this._handler);
      tg.BackButton.hide();
    } catch { /* не критично */ }
    this._handler = null;
  },
};

export function openLink(url) {
  if (!url) return;
  try {
    if (/^https?:\/\/t\.me\//.test(url) && tg?.openTelegramLink) {
      tg.openTelegramLink(url);
    } else if (tg?.openLink) {
      tg.openLink(url, { try_instant_view: true });
    } else {
      window.open(url, '_blank', 'noopener');
    }
  } catch {
    window.open(url, '_blank', 'noopener');
  }
}

/** Подтверждение. Нативное окно появилось в 6.2, ниже — обычный confirm. */
export function confirmDialog(message) {
  return new Promise(resolve => {
    if (supports('6.2') && tg?.showConfirm) {
      try {
        tg.showConfirm(message, ok => resolve(ok));
        return;
      } catch { /* уходим в запасной вариант */ }
    }
    resolve(window.confirm(message));
  });
}

export function alertDialog(message) {
  if (supports('6.2') && tg?.showAlert) {
    try { tg.showAlert(message); return; } catch { /* ниже */ }
  }
  window.alert(message);
}

/** Данные пользователя Telegram, если приложение открыто внутри клиента. */
/**
 * Ярлык мини-приложения на рабочем столе телефона (Bot API 8.0).
 *
 * Telegram сам показывает системное окно «Добавить на главный экран» —
 * нам остаётся его вызвать. После этого приложение открывается одним
 * тапом по иконке, без чата с ботом. На компьютере и в старых клиентах
 * метода нет: там статус «unsupported», и предлагаем только инструкцию.
 */
export const canAddToHome = () => supports('8.0') && typeof tg?.addToHomeScreen === 'function';

export function addToHome() {
  if (!canAddToHome()) return false;
  try { tg.addToHomeScreen(); return true; } catch { return false; }
}

/** 'added' | 'missed' | 'unknown' | 'unsupported' — есть ли уже ярлык. */
export function homeStatus() {
  return new Promise(resolve => {
    if (!supports('8.0') || typeof tg?.checkHomeScreenStatus !== 'function') {
      resolve('unsupported');
      return;
    }
    // Клиент может не ответить вовсе — экран из-за этого ждать не должен.
    const timer = setTimeout(() => resolve('unknown'), 1500);
    try {
      tg.checkHomeScreenStatus(s => { clearTimeout(timer); resolve(s || 'unknown'); });
    } catch {
      clearTimeout(timer);
      resolve('unsupported');
    }
  });
}

export function onHomeAdded(fn) {
  try { tg?.onEvent?.('homeScreenAdded', fn); } catch { /* старый клиент */ }
}

export function tgUser() {
  return tg?.initDataUnsafe?.user || null;
}


// ─────────────── тап или всё-таки прокрутка ───────────────

// Палец, ведущий страницу вверх, обязан оставаться прокруткой, даже
// если начался на карточке. WebView Telegram думает иначе: небольшое
// смещение он прощает и всё равно шлёт click — а на главной под пальцем
// почти всегда карточка, и человека «само собой» выбрасывало в ленту.
//
// Поэтому смотрим, двигался ли палец между началом касания и щелчком.
// Двигался — гасим click на фазе захвата, до того как до него доберётся
// экран. Порог в десять пикселей: меньше — это дрожь руки, а не жест.
const SLIP = 10;

// Щелчок приходит следом за касанием; всё, что позже, — уже мышь или
// клавиатура, и запрещать им ничего нельзя.
const AFTER_TOUCH = 700;

let startX = 0;
let startY = 0;
let slipped = false;
let endedAt = 0;

export function guardTaps(target = document) {
  const opts = { passive: true, capture: true };

  target.addEventListener('touchstart', e => {
    const t = e.touches[0];
    if (!t) return;
    startX = t.clientX;
    startY = t.clientY;
    slipped = false;
  }, opts);

  target.addEventListener('touchmove', e => {
    const t = e.touches[0];
    if (!t) return;
    if (Math.abs(t.clientX - startX) > SLIP
      || Math.abs(t.clientY - startY) > SLIP) slipped = true;
  }, opts);

  target.addEventListener('touchend', () => { endedAt = Date.now(); }, opts);

  target.addEventListener('click', e => {
    if (!slipped || Date.now() - endedAt > AFTER_TOUCH) return;
    slipped = false;
    e.stopPropagation();
    e.preventDefault();
  }, true);
}
