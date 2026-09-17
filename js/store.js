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

// Справочные данные — новости, кружки, институты, кампус, список групп.
// Расписание сюда не входит: оно живое, прямо с miet.ru.
export const data = {
  university: null,
  news: [],
  institutes: [],
  clubs: [],
  campus: [],
  groups: [],
  meta: {},
  stale: false,     // показываем вчерашнюю копию
  missing: false,   // не показываем вовсе
};

// Копия справочника на случай, когда сеть подвела. Собранный файл
// меняется раз в несколько недель, так что вчерашняя копия — это те же
// данные, а не «что-то старое».
const DATA_KEY = 'miet-data-cache';

// Длинные тексты карточек: полные новости, описания кружков, рассказы
// про кампус и институты. Раньше они лежали в общем файле, и приложение
// ждало их все, прежде чем нарисовать первый экран, — 107 КБ ради
// содержимого, которое читают, только открыв конкретную карточку.
// Теперь они приезжают фоном, после первого экрана.
const texts = {};
let textsGoing = null;

/**
 * Грузит тексты один раз и отдаёт тот же промис всем, кто спросит.
 *
 * Зовётся дважды: фоном сразу после запуска — чтобы к моменту, когда
 * человек откроет карточку, всё уже лежало, — и самим экраном карточки,
 * который на всякий случай дожидается. Отказ не страшен: без текста
 * карточка покажет заголовок и ссылку на источник, а не белый экран.
 */
export function loadTexts() {
  if (textsGoing) return textsGoing;
  textsGoing = fetch('data/texts.json', { cache: 'no-cache' })
    .then(r => (r.ok ? r.json() : {}))
    .then(got => {
      Object.assign(texts, got || {});
      return texts;
    })
    .catch(err => {
      console.warn('тексты не загрузились:', err.message);
      // Обнуляем, чтобы следующая попытка была настоящей, а не
      // повторным отказом из закешированного промиса.
      textsGoing = null;
      return texts;
    });
  return textsGoing;
}

/**
 * Длинное поле записи. Сначала смотрим в самой записи — в запасном
 * `app.json` тексты лежат внутри, — и только потом в отдельном файле.
 */
export function textOf(kind, item, field = 'text') {
  if (!item) return '';
  if (item[field]) return item[field];
  const id = item.id ?? '';
  return texts[`${kind}:${id}:${field}`] || '';
}

/**
 * Тянет справочник.
 *
 * Раньше отказ этого запроса валил всё приложение: человек видел
 * «Данные не загрузились» вместо расписания — хотя расписание с
 * miet.ru к этому файлу отношения не имеет. А отказ бывает на ровном
 * месте: GitHub Pages пересобирается после выкладки и минуту отвечает
 * 404, метро проезжает тоннель, телефон переключается с Wi-Fi на LTE.
 *
 * Поэтому: не вышло — берём копию из хранилища, нет копии — работаем
 * без справочника. Приложение обязано открыться в любом случае.
 */
export async function loadData() {
  // core.json — тот же справочник без длинных текстов: с ним первый
  // экран открывается вчетверо меньшим весом. app.json остаётся
  // запасным путём: он старше, полнее и лежит там же, так что клиент,
  // которому core не отдали, откроется как раньше.
  for (const src of ['data/core.json', 'data/app.json']) {
    try {
      const res = await fetch(src, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`сервер ответил ${res.status}`);
      const fresh = await res.json();
      Object.assign(data, fresh, { stale: false, missing: false });
      try {
        localStorage.setItem(DATA_KEY, JSON.stringify(fresh));
      } catch { /* хранилище переполнено — переживём, просто без копии */ }
      return data;
    } catch (err) {
      console.warn(`${src} не загрузился:`, err.message);
    }
  }

  try {
    const saved = JSON.parse(localStorage.getItem(DATA_KEY) || 'null');
    if (saved) {
      Object.assign(data, saved, { stale: true, missing: false });
      return data;
    }
  } catch { /* копия побилась — считаем, что её нет */ }

  data.missing = true;
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
