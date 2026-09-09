// Состояние приложения. Настройки живут в localStorage — он у мини-аппа
// свой на каждый origin и переживает перезапуск клиента.

const KEY = 'miet-app-v1';

const DEFAULTS = {
  group: null,        // выбранная учебная группа
  theme: 'auto',      // auto | light | dark — «авто» повторяет тему Telegram
  weekShift: 0,       // поправка к вычисленной неделе цикла, если разошлась с деканатом
  favorites: [],      // id избранных кружков
  seenNews: [],       // id прочитанных новостей
  hideEmptyDays: false,
};

function read() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') };
  } catch {
    return { ...DEFAULTS };
  }
}

export const settings = read();

// Бот открывает мини-приложение ссылкой вида /?group=ПИН-31 — подхватываем
// группу, чтобы не заставлять выбирать её второй раз.
try {
  const fromBot = new URLSearchParams(location.search).get('group');
  if (fromBot && fromBot !== settings.group) {
    settings.group = fromBot;
    localStorage.setItem(KEY, JSON.stringify(settings));
  }
} catch { /* приватный режим или странный URL — просто игнорируем */ }

export function save(patch = {}) {
  Object.assign(settings, patch);
  try {
    localStorage.setItem(KEY, JSON.stringify(settings));
  } catch { /* приватный режим — настройки просто не переживут перезапуск */ }
}

export function toggleFavorite(id) {
  const i = settings.favorites.indexOf(id);
  if (i >= 0) settings.favorites.splice(i, 1);
  else settings.favorites.push(id);
  save();
  return i < 0;
}

export const isFavorite = id => settings.favorites.includes(id);

export function markRead(id) {
  if (!settings.seenNews.includes(id)) {
    settings.seenNews.unshift(id);
    settings.seenNews = settings.seenNews.slice(0, 200);
    save();
  }
}

// ─────────────── данные ───────────────

export const data = {
  university: null,
  news: [],
  institutes: [],
  clubs: [],
  campus: [],
  groups: [],
  meta: {},
};

export async function loadData() {
  const res = await fetch('data/app.json', { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Не удалось загрузить данные (${res.status})`);
  Object.assign(data, await res.json());
  return data;
}

/**
 * Во что превращается выбор темы.
 *
 * «Авто» — это тема Telegram, а вне его системная: человек, у которого
 * весь мессенджер тёмный, не должен получать в лицо белый экран только
 * потому, что приложение открыто впервые. Выбранная руками тема
 * сильнее: её меняли осознанно.
 */
export function resolveTheme(theme = settings.theme) {
  if (theme === 'light' || theme === 'dark') return theme;
  const tg = window.Telegram?.WebApp?.colorScheme;
  if (tg === 'dark' || tg === 'light') return tg;
  try {
    return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

/** Применяет тему к <html>; компоненты про тему не знают — только про токены. */
export function applyTheme(theme = settings.theme) {
  document.documentElement.dataset.theme = resolveTheme(theme);
}
