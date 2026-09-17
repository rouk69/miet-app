// Приложение рассказывает о своих поломках само.
//
// До этого сломанное у человека было видно ровно ему: белый экран,
// пустая лента, не нажимающаяся кнопка — он закрывал приложение и
// уходил. Узнавали мы об этом, только если он писал в поддержку, и
// каждый найденный так баг находился случайно. Браузера в среде
// разработки нет, посмотреть глазами нельзя — значит спросить можно
// только сам клиент.
//
// Правила здесь ровно об одном: отчёт об ошибке не должен стать второй
// ошибкой. Поэтому всё завёрнуто, ничего не ждёт ответа, и поток
// одинаковых сообщений придерживается на месте, а не отправляется
// сотней запросов подряд.

import { post, canTalk } from './api.js';
import { BUILD } from './config.js';
import { tg } from './tg.js';

// Что уже отправляли в эту сессию. Одна и та же поломка в цикле
// перерисовки способна выстрелить сотню раз за секунду, и слать это
// целиком значит устроить себе же отказ в обслуживании.
const sent = new Set();

// Сколько разных поломок отправляем за сессию. Если их больше десятка,
// приложение сломано целиком, и одиннадцатая ничего не добавит.
const MAX_KINDS = 10;

/** Короткий отпечаток: тот же принцип, что на сервере. */
const keyOf = (message, source, line) =>
  `${String(message).replace(/\d+/g, '#').slice(0, 120)}|${source}|${line}`;

/**
 * Наша ли это ошибка.
 *
 * В WebView Telegram в консоль падает чужое: расширения, вставленные
 * скрипты, ошибки самого клиента. Отправлять их — значит забить список
 * шумом, в котором своё уже не найти. Считаем своим то, у чего нет
 * источника (inline-код страницы) или источник — наш файл.
 */
export function isOurs(source) {
  const s = String(source || '');
  if (!s) return true;
  if (/^(chrome|moz|safari)-extension:/.test(s)) return false;
  return s.includes('/js/') || s.endsWith('.js') || s.startsWith(location.origin);
}

function send(payload) {
  const key = keyOf(payload.message, payload.source, payload.line);
  if (sent.has(key) || sent.size >= MAX_KINDS) return;
  sent.add(key);
  if (!canTalk) return;
  // Ответа не ждём и ошибку отправки глотаем: если сеть лежит, второй
  // раз она от нашего беспокойства не поднимется.
  post('/api/oops', payload).catch(() => {});
}

/**
 * Включает слежение. Зовётся один раз при запуске — до всего
 * остального, чтобы поймать и поломки самого запуска.
 */
export function watchErrors(screenOf = () => '') {
  const common = () => ({
    build: BUILD || '',
    screen: screenOf() || '',
    platform: tg?.platform || 'браузер',
    version: tg?.version || '',
  });

  window.addEventListener('error', e => {
    try {
      // Событие 'error' прилетает и от картинок, не только от скриптов:
      // у него нет message, зато есть target. Битая обложка новости —
      // не поломка приложения, и в список ей незачем.
      if (!e.message) return;
      if (!isOurs(e.filename)) return;
      send({
        message: e.message,
        source: e.filename || '',
        line: e.lineno || 0,
        stack: e.error?.stack || '',
        ...common(),
      });
    } catch { /* здесь падать нельзя тем более */ }
  });

  window.addEventListener('unhandledrejection', e => {
    try {
      const reason = e.reason;
      const message = reason?.message || String(reason || 'Обещание отклонено');
      // Отказы сети — это не поломка кода: сервер не ответил, человек в
      // метро. Их и так видно по счётчикам, а список они забьют.
      if (/Сервер не ответил|Failed to fetch|NetworkError|AbortError/i.test(message)) return;
      send({
        message,
        source: 'promise',
        line: 0,
        stack: reason?.stack || '',
        ...common(),
      });
    } catch { /* см. выше */ }
  });
}

/**
 * Сообщить о своей поломке руками — там, где ошибку мы поймали сами и
 * показали человеку что-то осмысленное, но знать о ней всё равно надо.
 */
export function reportOops(message, where = '') {
  send({
    message: String(message || '').slice(0, 300),
    source: where || 'сами',
    line: 0,
    stack: '',
    build: BUILD || '',
    screen: where || '',
    platform: tg?.platform || 'браузер',
    version: tg?.version || '',
  });
}
