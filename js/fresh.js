// Свежесть открытой страницы.
//
// Telegram кеширует мини-приложение по адресу и держит дольше, чем
// просит HTTP. Лечилось это меткой выкладки в адресе кнопки: другой
// адрес — другая страница. Но адрес есть не у всех входов: главное
// мини-приложение (то, что даёт кнопку «Открыть» в списке чатов)
// задаётся в BotFather один раз и метку не несёт, и человек может
// открыть им прошлую сборку.
//
// Поэтому страница проверяет себя сама: спрашивает у того, кто её
// раздал, какая выкладка считается текущей, и если своя старее —
// перезагружается на новую. Спрашиваем именно раздатчика, а не сервер
// API: у зеркала может быть своя, отставшая копия, и сравнивать надо с
// ней, иначе перезагрузка ничего не изменит.

import { BUILD } from './config.js';

// Какую метку мы уже пытались получить. Иначе страница, которая почему-
// то не обновилась (кеш посредника, отставшее зеркало), перезагружалась
// бы по кругу.
const TRIED = 'miet-fresh-tried';

/**
 * Адрес этой же страницы с новой меткой.
 *
 * Остальные параметры сохраняются: в них приходит группа и startapp, а
 * терять их из-за обновления нельзя.
 */
export function freshUrl(href, version) {
  const hashAt = href.indexOf('#');
  const hash = hashAt < 0 ? '' : href.slice(hashAt);
  const body = hashAt < 0 ? href : href.slice(0, hashAt);
  const askAt = body.indexOf('?');
  const base = askAt < 0 ? body : body.slice(0, askAt);
  const parts = (askAt < 0 ? '' : body.slice(askAt + 1))
    .split('&')
    .filter(p => p && p.slice(0, 2) !== 'v=');
  parts.push('v=' + encodeURIComponent(version));
  return base + '?' + parts.join('&') + hash;
}

function tried() {
  try {
    return sessionStorage.getItem(TRIED) || '';
  } catch {
    return '';
  }
}

function remember(version) {
  try {
    sessionStorage.setItem(TRIED, version);
  } catch { /* приватный режим — переживём */ }
}

/**
 * Проверяет и, если надо, перезагружает страницу. Молча: человеку не о
 * чем знать, а спрашивать «обновиться?» — значит предлагать выбор, в
 * котором один ответ правильный.
 */
export async function checkFresh() {
  if (!BUILD) return false;
  let live = '';
  try {
    const res = await fetch('webapp.version?t=' + Date.now(), { cache: 'no-store' });
    if (!res.ok) return false;
    live = (await res.text()).trim();
  } catch {
    return false;                      // сети нет — не наше дело
  }
  if (!live || live === BUILD || live.length > 40) return false;
  if (tried() === live) return false;
  remember(live);
  location.replace(freshUrl(location.href, live));
  return true;
}
