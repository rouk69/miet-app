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

// В true-fullscreen контент уходит под статусбар и под собственную шапку
// Telegram, поэтому складываем системный отступ и safe-area в CSS-переменные.
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

export function initTelegram(theme = 'light') {
  if (!tg) return;
  try {
    tg.ready();
    tg.expand();
    // Вертикальные свайпы по умолчанию сворачивают мини-апп — это ломает
    // прокрутку длинных списков и шторок.
    tg.disableVerticalSwipes?.();
    syncChrome(theme);
    applySafeArea();
    tg.onEvent?.('safeAreaChanged', applySafeArea);
    tg.onEvent?.('contentSafeAreaChanged', applySafeArea);
    tg.onEvent?.('fullscreenChanged', applySafeArea);
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
export function tgUser() {
  return tg?.initDataUnsafe?.user || null;
}
