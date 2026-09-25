// Копия приложения в телефоне — на случай, когда дорога к серверу рвётся.
//
// Зачем. У части людей в одной сети не открывается наш сервер (Amvera),
// а в другой — зеркало на Cloudflare: 25.09.2026 у владельца на мобильном
// интернете работал только Cloudflare, на Wi-Fi — только Amvera. Страница
// приезжает с одного адреса, и если он в этой сети закрыт, Telegram
// показывает «Не удалось загрузить, ERR_CONNECTION_CLOSED» — до нашего
// кода дело не доходит вовсе. Этот воркер держит копию страницы, стилей
// и скриптов: адрес не ответил — приложение открывается из копии, а
// данные само берёт другой дорогой (js/config.js, перебор дорог).
//
// Правила, чтобы копия не стала ловушкой:
// - СНАЧАЛА СЕТЬ. Пока сервер отвечает, всегда берётся свежее и копия
//   тут же обновляется; копия — только при обрыве или долгом молчании.
//   Поэтому выкладки доезжают как раньше.
// - Данные (/api/…) и картинки постов не трогаем: у них своя логика.
// - Аварийный выключатель: если с воркером что-то не так, вместо этого
//   файла выкладывается версия, которая удаляет себя (см. DEPLOY.md), —
//   браузер перепроверяет sw.js при каждом открытии.

const CACHE = 'miet-shell-v1';
// Сколько ждать сеть, прежде чем открыть копию. Обрыв приходит сразу,
// а вот «молчание» может тянуться десятки секунд.
const WAIT = 6000;
// Скрипт Telegram живёт на чужом домене, но без него приложение не
// узнает человека — его тоже держим в копии.
const TG_SDK = 'https://telegram.org/js/telegram-web-app.js';

// Сразу при установке забираем страницу и всё, на что она ссылается.
// Иначе в копию попадало бы только загруженное ПОСЛЕ установки, а сама
// страница первого открытия грузится раньше — и при закрытом адресе
// открывать было бы нечего (так и вышло на первой проверке).
const DATA = ['data/core.json', 'data/texts.json'];

async function precache() {
  const cache = await caches.open(CACHE);
  const page = await fetch('./', { cache: 'no-cache' });
  if (!page.ok) return;
  await cache.put('./', page.clone());
  const html = await page.text();
  const links = [...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map(m => m[1])
    .filter(u => !/^(https?:|data:|mailto:|tg:)/.test(u));
  // Шрифты подключаются из стилей — вытаскиваем и их.
  const fonts = [];
  for (const css of links.filter(u => u.includes('.css'))) {
    try {
      const text = await (await fetch(css)).text();
      for (const m of text.matchAll(/url\(['"]?\.\.\/([^'")]+)['"]?\)/g)) fonts.push(m[1]);
    } catch { /* без шрифтов обойдёмся системными */ }
  }
  const all = [...new Set([...links, ...fonts, ...DATA, TG_SDK])];
  await Promise.all(all.map(async u => {
    try {
      const req = u === TG_SDK ? new Request(u, { mode: 'no-cors' }) : new Request(u);
      const res = await fetch(req);
      if (res.ok || res.type === 'opaque') await cache.put(req, res);
    } catch { /* одного файла нет — остальное всё равно пригодится */ }
  }));
}

self.addEventListener('install', event => {
  event.waitUntil(precache().catch(() => {}).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key !== CACHE) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});

function mine(request) {
  if (request.method !== 'GET') return false;
  const url = new URL(request.url);
  if (url.href.startsWith(TG_SDK)) return true;
  if (url.origin !== self.location.origin) return false;
  // Данные и картинки постов — мимо: API само выбирает дорогу, а картинки
  // копить в телефоне незачем.
  return !url.pathname.includes('/api/') && !url.pathname.includes('/media/');
}

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout')), ms);
    promise.then(v => { clearTimeout(t); resolve(v); },
      e => { clearTimeout(t); reject(e); });
  });
}

async function fromCopy(request) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(request) || await cache.match(request, { ignoreSearch: true });
  if (hit) return hit;
  // Страницу открывают с разными метками (?v=…, ?group=…) — любая
  // сохранённая страница лучше ошибки.
  if (request.mode === 'navigate') {
    return await cache.match('./', { ignoreSearch: true })
      || await cache.match('index.html', { ignoreSearch: true });
  }
  return undefined;
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (!mine(request)) return;
  event.respondWith((async () => {
    try {
      const fresh = await withTimeout(fetch(request), WAIT);
      // Кладём только удачное (и «непрозрачный» ответ скрипта Telegram).
      if (fresh && (fresh.ok || fresh.type === 'opaque')) {
        const copy = fresh.clone();
        caches.open(CACHE).then(c => c.put(request, copy)).catch(() => {});
      }
      return fresh;
    } catch (err) {
      const saved = await fromCopy(request);
      if (saved) return saved;
      throw err;
    }
  })());
});
