// Разговор с серверной частью: кто я и что тут происходит.
//
// Сервер узнаёт человека по initData — подписанной строке, которую Telegram
// кладёт в мини-приложение. Отправляем её заголовком на каждый запрос:
// своих токенов и кук нет, а подделать подпись без токена бота нельзя.
//
// Вне Telegram (обычный браузер, локальная отладка) initData пустая — тогда
// сеть не трогаем вовсе и приложение работает как раньше, без учёта.

import { API_BASE } from './config.js';
import { tg } from './tg.js';

const initData = tg?.initData || '';
export const canTalk = Boolean(API_BASE && initData);

/** Кто я по мнению сервера. Заполняется в loadMe(), до неё — пусто. */
export const account = {
  loaded: false,
  id: null,
  role: 'none',
  perms: [],
  sections: [],
  blocked: false,
  is_admin: false,
  can_stats: false,
  group: null,
};

async function once(path, { method, body, timeout }) {
  // Свой таймаут обязателен: браузер ждёт молчащий сервер десятками секунд,
  // а на старте приложения это означало бы экран загрузки всё это время.
  const stop = new AbortController();
  const bell = setTimeout(() => stop.abort(), timeout);
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers: {
        'X-Init-Data': initData,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: stop.signal,
    });
  } catch (err) {
    const e = new Error(err.name === 'AbortError' ? 'Сервер не ответил' : err.message);
    e.retriable = true;          // до сервера не дошли — пробовать можно
    throw e;
  } finally {
    clearTimeout(bell);
  }
  let data = null;
  try {
    data = await res.json();
  } catch { /* сервер ответил не JSON — разберёмся по коду */ }
  if (!res.ok) {
    const e = new Error(data?.error || `Сервер ответил ${res.status}`);
    // 502/503 — контейнер перезапускается после выкладки, это проходит
    // само за несколько секунд. Отказ по правам повторять бессмысленно.
    e.retriable = res.status >= 500;
    throw e;
  }
  return data;
}

/**
 * Запрос с одной повторной попыткой.
 *
 * Повторяем только то, что могло не дойти: обрыв, таймаут, 5xx. Отказ по
 * правам или неверные данные повторять незачем — ответ будет тот же.
 * Повтор безопасен и для POST: все наши записи идут «поставить такое
 * значение», а не «прибавить», и второй такой же запрос ничего не портит.
 */
async function request(path, { method = 'GET', body, timeout = 12000,
  retries = 1 } = {}) {
  if (!canTalk) throw new Error('Сервер недоступен');
  let last;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await once(path, { method, body, timeout });
    } catch (err) {
      last = err;
      if (!err.retriable || attempt === retries) break;
      // Небольшая пауза: если сервер поднимается, мгновенный повтор
      // застанет его в том же состоянии.
      await new Promise(r => setTimeout(r, 600));
    }
  }
  throw last;
}

export const get = (path, opts) => request(path, opts);
export const post = (path, body, opts) => request(path, { ...opts, method: 'POST', body });

/**
 * Спрашивает сервер, кто мы. Ошибку глотает: без сервера приложение обязано
 * работать — просто без админки и без переноса группы между устройствами.
 */
export async function loadMe() {
  if (!canTalk) return account;
  try {
    // На старте ждём сервер недолго и без повторов: расписание и данные
    // лежат в приложении, и молчащий сервер не повод держать человека на
    // экране загрузки. Права подтянутся при следующем открытии.
    Object.assign(account, await request('/api/me', { timeout: 4000, retries: 0 }),
      { loaded: true });
  } catch (err) {
    console.warn('сервер не ответил:', err.message);
  }
  return account;
}

// ─────────────── учёт ───────────────

const queue = [];
let timer = null;
let pendingGroup = null;

/**
 * Ставит событие в очередь. Отправляем пачками, а не по одному: переключение
 * вкладок — самое частое действие в приложении, и запрос на каждый тап
 * означал бы десятки запросов за минуту с телефона в метро.
 */
export function track(kind, name = '') {
  if (!canTalk || account.blocked) return;
  queue.push({ kind, name });
  if (timer) return;
  timer = setTimeout(flush, 1500);
}

/** Сообщает серверу выбранную группу — чтобы бот и приложение знали одну. */
export function syncGroup(group) {
  if (!canTalk || !group) return;
  pendingGroup = group;
  if (!timer) timer = setTimeout(flush, 300);
}

export function flush() {
  clearTimeout(timer);
  timer = null;
  if (!canTalk) return;
  const events = queue.splice(0, queue.length);
  const group = pendingGroup;
  pendingGroup = null;
  if (!events.length && !group) return;
  // keepalive: запрос переживает уход со страницы, иначе последний экран
  // перед закрытием мини-аппа терялся бы всегда.
  fetch(API_BASE + '/api/track', {
    method: 'POST',
    headers: { 'X-Init-Data': initData, 'Content-Type': 'application/json' },
    body: JSON.stringify({ events, group }),
    keepalive: true,
  }).catch(() => { /* учёт не должен мешать пользоваться приложением */ });
}

// Мини-апп закрывают, не выгружая страницу, — pagehide не всегда приходит,
// а visibilitychange приходит всегда.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') flush();
});
window.addEventListener('pagehide', flush);
