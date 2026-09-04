// Состояние приложения. Настройки живут в localStorage — он у мини-аппа
// свой на каждый origin и переживает перезапуск клиента.

const KEY = 'miet-app-v1';

const DEFAULTS = {
  group: null,        // выбранная учебная группа
  theme: 'light',     // light | dark — выбирается вручную, за темой Telegram не следует
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

/** Применяет тему к <html>; компоненты про тему не знают — только про токены. */
export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme === 'dark' ? 'dark' : 'light';
}
