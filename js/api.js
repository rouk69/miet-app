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

async function request(path, { method = 'GET', body, timeout = 12000 } = {}) {
  if (!canTalk) throw new Error('Сервер недоступен');
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
    throw new Error(err.name === 'AbortError' ? 'Сервер не ответил' : err.message);
  } finally {
    clearTimeout(bell);
  }
  let data = null;
  try {
    data = await res.json();
  } catch { /* сервер ответил не JSON — разберёмся по коду */ }
  if (!res.ok) throw new Error(data?.error || `Сервер ответил ${res.status}`);
  return data;
}

export const get = path => request(path);
export const post = (path, body) => request(path, { method: 'POST', body });

/**
 * Спрашивает сервер, кто мы. Ошибку глотает: без сервера приложение обязано
 * работать — просто без админки и без переноса группы между устройствами.
 */
export async function loadMe() {
  if (!canTalk) return account;
  try {
    // На старте ждём сервер недолго: расписание и данные лежат в приложении,
    // и молчащий сервер не повод держать человека на экране загрузки.
    Object.assign(account, await request('/api/me', { timeout: 4000 }),
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
