/* Собрано tools/stamp.py из js/*.js — не правьте здесь.
   Версия 7df7c315. Исходники лежат рядом и остаются модулями. */
var __mod = {};
/* ==== js\config.js ==== */
__mod['js/config.js'] = (function () {
// Адрес серверной части. Мини-приложение лежит на GitHub Pages и статично,
// а события и статистику отдаёт бот на Amvera — это единственное место,
// где два куска проекта знают друг о друге.
//
// Пустая строка выключает всё серверное: приложение работает как раньше,
// просто без учёта заходов и без админки.
//
// Домен подставляется из логина и названия проекта на Amvera:
// git.amvera.ru/rouk/miet-bot → miet-bot-rouk.amvera.io. Чтобы он отвечал,
// в панели проекта должен быть включён внешний доступ на порт 80.
const DEFAULT_BASE = 'https://miet-bot-rouk.amvera.io';

// Локальная отладка: в консоли браузера
//   localStorage.setItem('miet-api', 'http://localhost:8080')
// Через параметр адреса (?api=…) переопределять НЕЛЬЗЯ намеренно: по
// присланной ссылке подписанная initData уехала бы на чужой сервер, а с ней
// и возможность действовать от имени человека.
function stored() {
  try {
    return localStorage.getItem('miet-api') || '';
  } catch {
    return '';
  }
}

const API_BASE = (stored() || DEFAULT_BASE).replace(/\/+$/, '');

// Метка выкладки. Значение подставляет tools/stamp.py — по нему видно,
// свежую ли страницу открыл человек: Telegram кеширует мини-приложения
// по своим правилам, и «у меня ничего не поменялось» разбирается
// сравнением этой строки, а не на слово.
const BUILD = '7df7c315';

return {'API_BASE': API_BASE, 'BUILD': BUILD};
})();

/* ==== js\icons.js ==== */
__mod['js/icons.js'] = (function () {
// Иконки в стиле Lucide: обводка 1.75, скруглённые концы, без заливки —
// как требует дизайн-кит. Эмодзи в интерфейсе не используются: они
// разъезжаются по платформам и ломают ровный вид списков.
// SF Symbols визуально подошли бы идеально, но их лицензия запрещает веб.

const P = {
  // ── навигация и служебные ──
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20a1 1 0 0 0 1 1h3.5v-5.5h5V21H18a1 1 0 0 0 1-1V9.5"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  news: '<path d="M4 5h13a1 1 0 0 1 1 1v12a2 2 0 0 0 2 2H5a1 1 0 0 1-1-1V5Z"/><path d="M18 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2"/><path d="M8 9h6M8 13h6M8 17h4"/>',
  sparkles: '<path d="M9 3.5 10.6 8 15 9.6 10.6 11.2 9 15.6 7.4 11.2 3 9.6 7.4 8 9 3.5Z"/><path d="M17.5 13.5 18.4 16l2.5.9-2.5.9-.9 2.5-.9-2.5-2.5-.9 2.5-.9.9-2.5Z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5a7.7 7.7 0 0 1 15 0"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 5.2a3.5 3.5 0 0 1 0 5.6M18 20a6.4 6.4 0 0 0-2-4.6"/>',
  chevronRight: '<path d="m9 5 7 7-7 7"/>',
  chevronLeft: '<path d="m15 5-7 7 7 7"/>',
  chevronDown: '<path d="m5 9 7 7 7-7"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  x: '<path d="M6 6 18 18M18 6 6 18"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-13.7-5.3L3 9"/><path d="M4 13a8 8 0 0 0 13.7 5.3L21 15"/><path d="M3 4v5h5M21 20v-5h-5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/><circle cx="12" cy="7.8" r="0.9" fill="currentColor" stroke="none"/>',
  filter: '<path d="M4 6h16M7 12h10M10 18h4"/>',
  sliders: '<path d="M5 21V14M5 10V3M12 21v-9M12 8V3M19 21v-5M19 12V3"/><path d="M2.5 14h5M9.5 8h5M16.5 16h5"/>',
  grid: '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
  moon: '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>',
  trash: '<path d="M4.5 6.5h15"/><path d="M9 6.5V5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 5v1.5"/><path d="M6.5 6.5 7.3 19a2 2 0 0 0 2 1.9h5.4a2 2 0 0 0 2-1.9l.8-12.5"/><path d="M10.5 10.5v6M13.5 10.5v6"/>',
  palette: '<path d="M12 3.5c-4.7 0-8.5 3.6-8.5 8s3.8 8 8.5 8c1.1 0 1.8-.7 1.8-1.6 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.2 0-.9.8-1.6 1.8-1.6h1.4c2.5 0 4.5-1.9 4.5-4.3 0-3.4-3.6-6.1-8.5-6.1Z"/><circle cx="8" cy="10" r="1.2" fill="currentColor" stroke="none"/><circle cx="12" cy="7.8" r="1.2" fill="currentColor" stroke="none"/><circle cx="16" cy="10" r="1.2" fill="currentColor" stroke="none"/>',

  // ── виды занятий: значок в плашке рядом с названием пары ──
  board: '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M12 17v4M8.5 21h7"/><path d="M7 8.5h7M7 12h4"/>',
  flask: '<path d="M9.5 3v6.2L4.8 17a2.5 2.5 0 0 0 2.1 3.8h10.2a2.5 2.5 0 0 0 2.1-3.8L14.5 9.2V3"/><path d="M8 3h8"/><path d="M7.4 14.5h9.2"/>',
  pencil: '<path d="M4 20.5h4L20 8.5a2.8 2.8 0 0 0-4-4L4 16.5v4Z"/><path d="m14.5 6 3.5 3.5"/>',

  // ── расписание ──
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.2l3.2 2"/>',
  eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
  teacher: '<circle cx="12" cy="7.5" r="3.5"/><path d="M5 20.5a7 7 0 0 1 14 0"/>',
  door: '<path d="M4 21h16"/><path d="M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17"/><circle cx="14.5" cy="12" r="1"/>',
  pin: '<path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z"/><circle cx="12" cy="10" r="2.6"/>',
  bell: '<path d="M6 9a6 6 0 1 1 12 0c0 4.5 1.5 6 1.5 6H4.5S6 13.5 6 9Z"/><path d="M10 19a2 2 0 0 0 4 0"/>',

  // ── связь и ссылки ──
  phone: '<path d="M6.5 3.5h3l1.5 4-2 1.5a12 12 0 0 0 6 6l1.5-2 4 1.5v3a2 2 0 0 1-2.2 2A17.5 17.5 0 0 1 4.5 5.7 2 2 0 0 1 6.5 3.5Z"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4 7.5 7.1 5a1.5 1.5 0 0 0 1.8 0L20 7.5"/>',
  external: '<path d="M14 4h6v6"/><path d="m20 4-9 9"/><path d="M18 14.5V19a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4.5"/>',
  link: '<path d="M10 13.5a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1.6 1.6"/><path d="M14 10.5a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.6-1.6"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3.2 9.5h17.6M3.2 14.5h17.6"/><path d="M12 3c-2.3 2.4-3.5 5.5-3.5 9s1.2 6.6 3.5 9c2.3-2.4 3.5-5.5 3.5-9S14.3 5.4 12 3Z"/>',
  messageCircle: '<path d="M20.5 11.6c0 4.2-3.8 7.6-8.5 7.6-1 0-2-.2-2.9-.5L4 20.5l1.4-4.2A7.2 7.2 0 0 1 3.5 11.6C3.5 7.4 7.3 4 12 4s8.5 3.4 8.5 7.6Z"/>',
  wave: '<path d="M11 12V5.5a1.5 1.5 0 0 1 3 0V12"/><path d="M14 11V4.5a1.5 1.5 0 0 1 3 0V12"/><path d="M17 11.5v-4a1.5 1.5 0 0 1 3 0V15a6 6 0 0 1-6 6h-1.5a6 6 0 0 1-5.2-3l-2.6-4.5a1.5 1.5 0 0 1 2.4-1.8L9.5 14"/><path d="M8 12V7.5a1.5 1.5 0 0 1 3 0V12"/>',

  // ── кампус ──
  book: '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H19v15H5.5A1.5 1.5 0 0 0 4 19.5v-15Z"/><path d="M4 19.5A1.5 1.5 0 0 1 5.5 18H19v3H5.5A1.5 1.5 0 0 1 4 19.5Z"/>',
  bookOpen: '<path d="M12 6.5C10.3 5.2 7.8 4.7 4 5v13c3.8-.3 6.3.2 8 1.5 1.7-1.3 4.2-1.8 8-1.5V5c-3.8-.3-6.3.2-8 1.5Z"/><path d="M12 6.5v13"/>',
  utensils: '<path d="M5 3v8a2 2 0 0 0 4 0V3"/><path d="M7 11v10"/><path d="M17 3c-1.6 1-2.5 3-2.5 5.5S15.4 13 17 13.6V21"/>',
  stethoscope: '<path d="M5 3v5a4 4 0 0 0 8 0V3"/><path d="M5 3H3.6M13 3h1.4"/><path d="M9 12v3a5 5 0 0 0 5 5 4 4 0 0 0 4-4v-1.2"/><circle cx="18" cy="13" r="2.2"/>',
  leaf: '<path d="M4 20c0-8 5-13 16-13 0 9-5 13-11 13-2.8 0-5-1.6-5-1.6Z"/><path d="M5 19c3-4 7-6.5 11.5-8"/>',
  briefcase: '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7"/><path d="M3 12.5h18"/>',
  wallet: '<path d="M3 8a2 2 0 0 1 2-2h13a1 1 0 0 1 1 1v2"/><path d="M3 8v9a2 2 0 0 0 2 2h13a2 2 0 0 0 2-2v-2"/><path d="M20 10.5h-3.5a2 2 0 0 0 0 4H20a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1Z"/>',
  lifebuoy: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.6"/><path d="m5.7 5.7 3.8 3.8M14.5 14.5l3.8 3.8M18.3 5.7l-3.8 3.8M9.5 14.5l-3.8 3.8"/>',
  stadium: '<path d="M3 8.5c0-1.9 4-3.4 9-3.4s9 1.5 9 3.4-4 3.4-9 3.4-9-1.5-9-3.4Z"/><path d="M3 8.5v7c0 1.9 4 3.4 9 3.4s9-1.5 9-3.4v-7"/>',
  drama: '<path d="M3 5.5c2.6-.7 5.4-.7 8 0v5.6c0 2.4-1.8 4.2-4 4.2s-4-1.8-4-4.2V5.5Z"/><path d="M5.4 9.4c.7.6 1.5.6 2.2 0"/><path d="M13 7.6c2.6-.7 5.4-.7 8 0v5.6c0 2.4-1.8 4.2-4 4.2s-4-1.8-4-4.2V7.6Z"/><path d="M15.4 13.3c.7-.6 1.5-.6 2.2 0"/>',
  building: '<path d="M4 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16"/><path d="M15 9h3a2 2 0 0 1 2 2v10"/><path d="M3 21h18"/><path d="M8 7h3M8 11h3M8 15h3"/>',
  homes: '<path d="m3 11 5.5-4.5L14 11"/><path d="M4.5 10v10h8V10"/><path d="M12.5 20h7V9.5L15.5 6l-2.4 2"/><path d="M7.5 20v-4h2v4"/>',
  landmark: '<path d="M3 21h18"/><path d="m12 3 8 5H4l8-5Z"/><path d="M6 10v8M10 10v8M14 10v8M18 10v8"/>',
  office: '<path d="M3.5 21h17"/><path d="M5 21V6.5l7-3.5 7 3.5V21"/><path d="M9.5 21v-4.5h5V21"/><path d="M9 9.5h1.5M13.5 9.5H15M9 13h1.5M13.5 13H15"/>',
  school: '<path d="m12 3 9 4.5-9 4.5-9-4.5L12 3Z"/><path d="M6.5 10v5.5c0 1.7 2.5 3 5.5 3s5.5-1.3 5.5-3V10"/><path d="M21 7.5V13"/>',
  graduate: '<path d="m12 3 10 5-10 5L2 8l10-5Z"/><path d="M6 10.5V16c0 1.7 2.7 3 6 3s6-1.3 6-3v-5.5"/>',

  // ── спорт ──
  bike: '<circle cx="5.5" cy="17" r="3.2"/><circle cx="18.5" cy="17" r="3.2"/><path d="M9 17h3l3.5-7.5"/><path d="M12.5 9.5H9m6.5 0h2.6l.9 4"/><circle cx="15.5" cy="4.5" r="1.2"/>',
  gamepad: '<rect x="2.5" y="7.5" width="19" height="10" rx="4"/><path d="M7 11v3M5.5 12.5h3"/><circle cx="16" cy="12" r="1"/><circle cx="18.5" cy="14" r="1"/>',
  megaphone: '<path d="M3 11v2a1 1 0 0 0 1 1h2l9 4V6L6 10H4a1 1 0 0 0-1 1Z"/><path d="M18.5 9a4 4 0 0 1 0 6"/><path d="M6 14v4.5a1 1 0 0 0 1 1h1.5a1 1 0 0 0 1-1V16"/>',
  yoga: '<circle cx="12" cy="4.5" r="2"/><path d="M12 8v5"/><path d="m12 13-4.5 3M12 13l4.5 3"/><path d="M4.5 10.5 12 12l7.5-1.5"/>',
  mountain: '<path d="m2.5 19 6.5-11 4 6.5 2.2-3.5L21.5 19H2.5Z"/><path d="m9 8 1.8 3"/>',
  waves: '<path d="M2.5 8.5c1.6-1.6 3.2-1.6 4.8 0s3.2 1.6 4.8 0 3.2-1.6 4.8 0 3.2 1.6 4.6 0"/><path d="M2.5 13.5c1.6-1.6 3.2-1.6 4.8 0s3.2 1.6 4.8 0 3.2-1.6 4.8 0 3.2 1.6 4.6 0"/><path d="M2.5 18.5c1.6-1.6 3.2-1.6 4.8 0s3.2 1.6 4.8 0 3.2-1.6 4.8 0 3.2 1.6 4.6 0"/>',
  ball: '<circle cx="12" cy="12" r="9"/><path d="m12 7.5 3.6 2.6-1.4 4.2H9.8L8.4 10.1 12 7.5Z"/><path d="M12 3v4.5M4.2 9.5l4.2.6M19.8 9.5l-4.2.6M7.5 20.2l2.3-5.9M16.5 20.2l-2.3-5.9"/>',
  medal: '<circle cx="12" cy="15" r="5"/><path d="m8.5 10.5-3-7h5l2 4.5M15.5 10.5l3-7h-5"/><path d="m12 13 .8 1.7 1.8.2-1.3 1.3.3 1.8-1.6-.9-1.6.9.3-1.8-1.3-1.3 1.8-.2L12 13Z"/>',
  award: '<circle cx="12" cy="9" r="5.5"/><path d="m8.5 13.5-1.3 7 4.8-2.6 4.8 2.6-1.3-7"/>',
  star: '<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1.1 5.9L12 17l-5.3 2.7 1.1-5.9L3.5 9.7l5.9-.8L12 3.5Z"/>',

  // ── творчество и медиа ──
  music: '<path d="M9 18V6l11-2v12"/><circle cx="6.5" cy="18" r="2.6"/><circle cx="17.5" cy="16" r="2.6"/>',
  mic: '<rect x="9" y="2.5" width="6" height="11" rx="3"/><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0"/><path d="M12 18v3M9 21h6"/>',
  dance: '<circle cx="13" cy="4" r="1.8"/><path d="M13 6.5 11 11l3 2 .5 4"/><path d="m11 11-3.5 1.5M14 13l3.5 1"/><path d="m11.5 17-2 4M14.5 17l1.5 4"/>',
  camera: '<path d="M4 8h2.6l1.5-2.4h7.8L17.4 8H20a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 20 20H4a1.5 1.5 0 0 1-1.5-1.5v-9A1.5 1.5 0 0 1 4 8Z"/><circle cx="12" cy="13.5" r="3.6"/>',
  video: '<rect x="2.5" y="6" width="13" height="12" rx="2.5"/><path d="m15.5 10.5 6-3v9l-6-3z"/>',
  microscope: '<path d="M7 18h10"/><path d="M4 21h16"/><path d="M9.5 18a5.5 5.5 0 0 0 5.5-5.5"/><path d="M11 4h2.5a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H11a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"/><path d="M8 6h2M8 10h2"/>',
  brain: '<path d="M12 5.5a3 3 0 0 0-5.6-1.4A2.8 2.8 0 0 0 4 8.6a3 3 0 0 0 .6 5.2A3 3 0 0 0 8 19a3 3 0 0 0 4-1.6"/><path d="M12 5.5A3 3 0 0 1 17.6 4a2.8 2.8 0 0 1 2.4 4.5 3 3 0 0 1-.6 5.3A3 3 0 0 1 16 19a3 3 0 0 1-4-1.6"/><path d="M12 5.5v11.9"/>',
  dice: '<rect x="3.5" y="3.5" width="17" height="17" rx="3.5"/><circle cx="8.5" cy="8.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="15.5" cy="15.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.1" fill="currentColor" stroke="none"/>',

  // ── добровольчество и объединения ──
  recycle: '<path d="m7.5 18.5-3-5 3.4-2"/><path d="M10.5 5.2 8 9.5 5 7.8l2.4-4a1.6 1.6 0 0 1 2.8 0l1.3 2.3"/><path d="m19.5 12.5 2.2 3.8a1.6 1.6 0 0 1-1.4 2.4H16"/><path d="m13.5 21 2.5-2.5-2.5-2.5"/><path d="M14.5 4.5 17 9l3-1.7"/><path d="M7.5 18.5H5"/>',
  tent: '<path d="m12 5-8.5 15h17L12 5Z"/><path d="M12 5v15"/><path d="m8 20 4-7 4 7"/>',
  handHeart: '<path d="M9.5 8.5a2.2 2.2 0 0 1 3.6-.8l.4.4.4-.4a2.2 2.2 0 1 1 3.1 3.1L13.5 15l-4-3.9a2.2 2.2 0 0 1 0-2.6Z"/><path d="M3 14.5v6"/><path d="M6 20.5h8.5a3 3 0 0 0 2-.8l4.2-3.9a1.5 1.5 0 0 0-2-2.2L15.5 16"/>',
  heart: '<path d="M12 20s-7.5-4.7-7.5-9.7A4.3 4.3 0 0 1 12 7.4a4.3 4.3 0 0 1 7.5 2.9c0 5-7.5 9.7-7.5 9.7Z"/>',
  droplet: '<path d="M12 3.5c3.5 4 6 6.8 6 9.8a6 6 0 0 1-12 0c0-3 2.5-5.8 6-9.8Z"/>',
  flag: '<path d="M5 21V4"/><path d="M5 5h10.5l-1.5 3.5L15.5 12H5"/>',
  shield: '<path d="M12 3 5 5.8v5.4c0 4.2 2.9 7.5 7 9.3 4.1-1.8 7-5.1 7-9.3V5.8L12 3Z"/>',
  handshake: '<path d="m11 8 2-1.6 5 4"/><path d="M13 6.4 10.6 4.6a2 2 0 0 0-2.3 0L4 8"/><path d="M4 8v4.5l3.5 3.5a1.6 1.6 0 0 0 2.3 0"/><path d="m9.8 16 1.7 1.7a1.6 1.6 0 0 0 2.3 0"/><path d="m13.8 17.7 1 1a1.6 1.6 0 0 0 2.3-2.3L18 12V8"/>',
  vote: '<path d="M3.5 14.5 6 8.5h12l2.5 6"/><path d="M3.5 14.5v3.4a1.6 1.6 0 0 0 1.6 1.6h13.8a1.6 1.6 0 0 0 1.6-1.6v-3.4Z"/><path d="M9 14.5h6"/><path d="m8.5 5.5 2 2 4-4"/>',

  // ── сервисы и документы ──
  chart: '<path d="M3.5 20.5h17"/><rect x="5" y="11" width="3.4" height="7" rx="1"/><rect x="10.3" y="6" width="3.4" height="12" rx="1"/><rect x="15.6" y="9" width="3.4" height="9" rx="1"/>',
  key: '<circle cx="8" cy="8" r="4.5"/><path d="m11.2 11.2 8.3 8.3"/><path d="m16.5 16.5 2-2M19 19l1.5-1.5"/>',
  database: '<ellipse cx="12" cy="6" rx="7.5" ry="3"/><path d="M4.5 6v12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"/><path d="M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"/>',
  fileText: '<path d="M13.5 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5L13.5 3Z"/><path d="M13.5 3v5.5H19"/><path d="M8.5 13h7M8.5 16.5h5"/>',
  clipboard: '<rect x="5" y="4.5" width="14" height="16" rx="2.5"/><path d="M9 4.5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 4.5v1H9v-1Z"/><path d="M9 11h6M9 15h4"/>',
  edit: '<path d="M12 20.5h8.5"/><path d="M16.5 4.2a2.1 2.1 0 0 1 3 3L8.5 18.2l-4 1 1-4L16.5 4.2Z"/>',
  shuffle: '<path d="M3.5 6.5h3.2c1.2 0 2.3.6 3 1.6l4.6 7c.7 1 1.8 1.6 3 1.6h3.2"/><path d="M3.5 17.5h3.2c1.2 0 2.3-.6 3-1.6l.9-1.4M14.5 9l.9-1.4c.7-1 1.8-1.6 3-1.6h3.2"/><path d="m18.5 3.5 3 3-3 3M18.5 14.5l3 3-3 3"/>',
  helpCircle: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.5a2.5 2.5 0 1 1 3.3 2.4c-.6.2-.9.8-.9 1.4v.4"/><circle cx="12" cy="16.8" r="0.9" fill="currentColor" stroke="none"/>',
  compass: '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5.2-5.2 2 2-5.2 5.2-2Z"/>',
  scroll: '<path d="M6 4h11a2 2 0 0 1 2 2v11.5a2.5 2.5 0 0 0 2.5 2.5H7.5A2.5 2.5 0 0 1 5 17.5V5"/><path d="M5 5a1.5 1.5 0 0 1 3 0v3H5"/><path d="M9.5 8.5h6M9.5 12.5h6"/>',
  target: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.8"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
  folder: '<path d="M3.5 7.5a2 2 0 0 1 2-2h3.2l2 2.5H18.5a2 2 0 0 1 2 2v7.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-10Z"/>',
  creditCard: '<rect x="2.5" y="5.5" width="19" height="13" rx="2.5"/><path d="M2.5 10h19"/><path d="M6 14.5h3"/>',
  inbox: '<path d="M3.5 13.5h4l1.5 3h6l1.5-3h4"/><path d="M5.6 5.6h12.8l2.1 7.9v4a2 2 0 0 1-2 2H5.5a2 2 0 0 1-2-2v-4l2.1-7.9Z"/>',
  backpack: '<path d="M6 8.5A4.5 4.5 0 0 1 10.5 4h3A4.5 4.5 0 0 1 18 8.5V21H6V8.5Z"/><path d="M9.5 4V3.2A1.2 1.2 0 0 1 10.7 2h2.6a1.2 1.2 0 0 1 1.2 1.2V4"/><path d="M9 12h6v4H9z"/>',
  zap: '<path d="M13.5 2.5 4.5 13.5h6l-.5 8 9-11h-6l.5-8Z"/>',

  // ── предметы: по значку объявление узнаётся раньше, чем прочитано ──
  atom: '<circle cx="12" cy="12" r="2"/>'
      + '<ellipse cx="12" cy="12" rx="9.5" ry="4" />'
      + '<ellipse cx="12" cy="12" rx="9.5" ry="4" transform="rotate(60 12 12)"/>'
      + '<ellipse cx="12" cy="12" rx="9.5" ry="4" transform="rotate(120 12 12)"/>',
  sigma: '<path d="M17.5 5H6.5l6 7-6 7h11"/>',
  code: '<path d="m8.5 8.5-4 3.5 4 3.5"/><path d="m15.5 8.5 4 3.5-4 3.5"/>'
      + '<path d="M13.5 5 10.5 19"/>',
  languages: '<path d="M3.5 6h8M7.5 6V4"/>'
      + '<path d="M9.8 6c-.4 3.9-2.7 7.2-6.3 8.5"/>'
      + '<path d="M5.5 10.5c1 2 2.8 3.4 5 4"/>'
      + '<path d="m13 20 4-9 4 9"/><path d="M14.3 17h5.4"/>',
  map: '<path d="m9 4 6 2.5L20.4 4a.6.6 0 0 1 .9.5v12.9a.6.6 0 0 1-.4.6L15 20l-6-2.5-5.4 2.5a.6.6 0 0 1-.9-.5V6.6a.6.6 0 0 1 .4-.6L9 4Z"/><path d="M9 4v13.5M15 6.5V20"/>',
};

/** Возвращает разметку иконки. size — в px, cls — дополнительный класс. */
function icon(name, size = 22, cls = '') {
  const body = P[name] || P.info;
  return `<svg class="${cls}" width="${size}" height="${size}" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="1.75"
    stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${body}</svg>`;
}

const hasIcon = name => Object.hasOwn(P, name);
const iconNames = Object.keys(P);

return {'icon': icon, 'hasIcon': hasIcon, 'iconNames': iconNames};
})();

/* ==== js\schedule.js ==== */
__mod['js/schedule.js'] = (function () {
// Расписание — живое, но добывается тремя путями подряд.
//
// Сначала своя копия в телефоне (сутки), потом сервер бота: у него есть
// кеш, он ближе к институту и отвечает мгновенно. Только если и он
// молчит — идём на miet.ru сами (он отдаёт Access-Control-Allow-Origin,
// поэтому запрос из браузера возможен), а совсем в конце достаём
// сохранённое, даже просроченное.
//
// Порядок именно такой, потому что сайт института отвечает не всем и не
// всегда: с части мобильных сетей он недоступен вовсе, и это выглядело
// как ошибка приложения.

var API_BASE = __mod['js/config.js']['API_BASE'];

const API = 'https://miet.ru/schedule/data';
const CACHE_KEY = g => `miet-sched:${g}`;
const TTL = 24 * 60 * 60 * 1000;

const DAY_NAMES = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
const DAY_SHORT = ['', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

/** Ставит дату на понедельник её недели (воскресенье относим к прошедшей). */
function mondayOf(date) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const shift = (d.getDay() + 6) % 7;   // Пн=0 … Вс=6
  d.setDate(d.getDate() - shift);
  return d;
}

/**
 * Начало семестра по строке вида «Осенний семестр 2026/2027».
 * Осенний считаем с 1 сентября, весенний — с 9 февраля.
 */
function semesterStart(semestr) {
  const m = /(\d{4})\s*\/\s*(\d{4})/.exec(semestr || '');
  const autumn = /осен/i.test(semestr || '');
  const now = new Date();
  if (!m) {
    return autumn || now.getMonth() >= 7
      ? new Date(now.getFullYear(), 8, 1)
      : new Date(now.getFullYear(), 1, 9);
  }
  return autumn
    ? new Date(+m[1], 8, 1)
    : new Date(+m[2], 1, 9);
}

/**
 * Номер недели в четырёхнедельном цикле МИЭТ (0..3).
 * Вычисляем от начала семестра; если у деканата счёт разошёлся,
 * пользователь поправляет сдвигом в профиле.
 */
function weekOfCycle(date, semestr, shift = 0) {
  const start = mondayOf(semesterStart(semestr));
  const cur = mondayOf(date);
  const weeks = Math.round((cur - start) / (7 * 86400000));
  return (((weeks + shift) % 4) + 4) % 4;
}

/** Разбирает «[ФТД] [ДСТ] Быстрые алгоритмы [Лек]» на части. */
function parseSubject(raw) {
  let name = String(raw || '').trim();
  const flags = [];
  let kind = '';
  name = name.replace(/\[(ФТД|ДСТ|ФАК)\]/gi, (_, f) => { flags.push(f.toUpperCase()); return ''; });
  name = name.replace(/\[([^\]]+)\]\s*$/, (_, k) => { kind = k.trim(); return ''; });
  name = name.replace(/\s{2,}/g, ' ').trim();
  const low = kind.toLowerCase();
  const cls = low.startsWith('лек') ? 'lek'
    : low.startsWith('пр') ? 'pr'
      : low.startsWith('лаб') ? 'lab' : 'oth';
  const full = { lek: 'Лекция', pr: 'Практика', lab: 'Лабораторная' }[cls] || kind;
  return { name, kind: full, cls, flags };
}

const hhmm = iso => (String(iso || '').match(/T(\d{2}:\d{2})/) || [, ''])[1];

/** «Осенний семестр 2026/2027» → «осень 2026/27» — чтобы влезало в подзаголовок. */
function shortSemestr(s) {
  const m = /(\d{4})\s*\/\s*(\d{4})/.exec(s || '');
  const season = /осен/i.test(s || '') ? 'осень' : /весен/i.test(s || '') ? 'весна' : '';
  if (!m) return season || s || '';
  return `${season} ${m[1]}/${m[2].slice(2)}`.trim();
}

/** Приводит ответ API к плоскому виду, удобному для экрана. */
function normalize(json) {
  const times = (json.Times || []).map(t => ({
    code: t.Code,
    label: t.Time,
    from: hhmm(t.TimeFrom),
    to: hhmm(t.TimeTo),
  }));
  const lessons = (json.Data || []).map(d => {
    const s = parseSubject(d.Class?.Name);
    return {
      day: d.Day,                 // 1..6 — Пн..Сб
      week: d.DayNumber,          // 0..3 — неделя цикла
      pair: d.Time?.Code,
      from: hhmm(d.Time?.TimeFrom),
      to: hhmm(d.Time?.TimeTo),
      subject: s.name,
      kind: s.kind,
      kindCls: s.cls,
      flags: s.flags,
      teacher: d.Class?.TeacherFull || d.Class?.Teacher || '',
      teacherShort: d.Class?.Teacher || '',
      room: d.Room?.Name || '',
      group: d.Group?.Name || '',
    };
  });
  lessons.sort((a, b) => a.day - b.day || a.pair - b.pair);
  return { semestr: json.Semestr || '', times, lessons };
}

/** Сохранённая копия расписания: {at, data} или null. */
function saved(group) {
  try {
    const hit = JSON.parse(localStorage.getItem(CACHE_KEY(group)) || 'null');
    return hit && hit.data ? hit : null;
  } catch {
    return null;                       // копия побилась — считаем, что её нет
  }
}

/**
 * Расписание с сервера бота: у него есть кеш и он ближе к институту.
 *
 * Пустая строка вместо адреса означает, что серверная часть выключена
 * (обычный браузер вне Telegram) — тогда этот путь просто пропускается.
 */
async function fromBot(group) {
  if (!API_BASE) return null;
  const stop = new AbortController();
  const bell = setTimeout(() => stop.abort(), 8000);
  try {
    const res = await fetch(
      `${API_BASE}/api/schedule?group=${encodeURIComponent(group)}`,
      { signal: stop.signal, headers: initDataHeader() });
    if (!res.ok) return null;
    const data = await res.json();
    return data && data.ready && Array.isArray(data.lessons) ? data : null;
  } catch {
    return null;                        // молчит — пойдём на miet.ru сами
  } finally {
    clearTimeout(bell);
  }
}

/** Заголовок с подписью Telegram, если мы внутри него. */
function initDataHeader() {
  const raw = window.Telegram?.WebApp?.initData || '';
  return raw ? { 'X-Init-Data': raw } : {};
}

/** Расписание прямо с miet.ru — как ходило приложение до сих пор. */
async function fromSite(group) {
  const res = await fetch(`${API}?group=${encodeURIComponent(group)}`,
    { cache: 'no-cache' });
  if (!res.ok) throw new Error(`miet.ru ответил ${res.status}`);
  return normalize(await res.json());
}

/**
 * Загружает расписание группы. force=true обходит свежую копию.
 *
 * Порядок такой: свежая копия в телефоне → сервер бота (у него кеш и он
 * отвечает мгновенно) → miet.ru напрямую → любая копия, даже
 * просроченная. Сайт института отвечает не всем и не всегда: с части
 * мобильных сетей он недоступен вовсе, и раньше это означало ошибку
 * вместо расписания.
 */
async function fetchSchedule(group, { force = false } = {}) {
  const key = CACHE_KEY(group);
  const copy = saved(group);
  if (!force && copy && Date.now() - copy.at < TTL) {
    return { ...copy.data, cached: true };
  }

  let data = await fromBot(group);
  let err = null;
  if (!data) {
    try {
      data = await fromSite(group);
    } catch (e) {
      err = e;
    }
  }

  if (data) {
    try {
      localStorage.setItem(key, JSON.stringify({ at: Date.now(), data }));
    } catch { /* переполнение хранилища — работаем без копии */ }
    return { ...data, cached: false };
  }

  if (copy) {
    console.warn('расписание не обновилось, показываю сохранённое:',
      err && err.message);
    return { ...copy.data, cached: true, stale: true, why: err && err.message };
  }

  // Показывать нечего. Сообщение делаем человеческим: «Failed to fetch»
  // ничего не объясняет тому, кто просто открыл приложение.
  throw new Error(navigator.onLine === false
    ? 'Нет сети — расписание берётся с miet.ru'
    : `Расписание не пришло (${(err && err.message) || 'сервер молчит'})`);
}

/** Все записи расписания на конкретный день конкретной недели цикла. */
const lessonsOf = (sched, week, day) =>
  (sched?.lessons || []).filter(l => l.week === week && l.day === day);

/**
 * Пары дня — по одной на слот звонков.
 *
 * В одном слоте у группы может стоять несколько занятий: язык и
 * физкультура делятся на подгруппы, и МИЭТ отдаёт их отдельными записями
 * с одинаковым временем. Без сборки они выглядели бы как две пары подряд
 * с одним и тем же временем, а счётчик показывал бы на одну больше.
 */
function slotsOf(sched, week, day) {
  const byPair = new Map();
  for (const l of lessonsOf(sched, week, day)) {
    if (!byPair.has(l.pair)) {
      byPair.set(l.pair, { pair: l.pair, from: l.from, to: l.to, entries: [] });
    }
    byPair.get(l.pair).entries.push(l);
  }
  return [...byPair.values()]
    .sort((a, b) => (a.pair || 0) - (b.pair || 0))
    .map(s => {
      const first = s.entries[0];
      // Обычно подгруппы — один предмет у разных преподавателей. Если
      // предметы разные, общего названия у слота быть не может.
      const sameSubject = new Set(s.entries.map(e => e.subject)).size === 1;
      return {
        ...s,
        sameSubject,
        split: s.entries.length > 1,
        subject: sameSubject ? first.subject : '',
        kind: sameSubject ? first.kind : '',
        kindCls: sameSubject ? first.kindCls : 'oth',
        flags: sameSubject ? first.flags : [],
      };
    });
}

/**
 * Окна между парами: где в дне пропущен слот звонков.
 *
 * Студент планирует день не парами, а промежутками: «после второй окно
 * до четвёртой» — это полтора часа, за которые успеваешь доехать,
 * поесть или доделать лабу. В расписании окно видно только дыркой в
 * номерах пар, и её приходилось замечать самому, сверяя время конца
 * одной строки с началом следующей.
 *
 * Тот же расчёт есть у бота (`schedule_api.gaps_of`) — они порты друг
 * друга, и меняться должны вместе.
 */
function gapsOf(slots) {
  const out = [];
  for (let i = 0; i + 1 < slots.length; i++) {
    const before = slots[i];
    const after = slots[i + 1];
    const missed = (after.pair || 0) - (before.pair || 0) - 1;
    if (missed <= 0) continue;
    out.push({
      after: before.pair,
      before: after.pair,
      pairs: missed,
      from: before.to || '',
      to: after.from || '',
      minutes: minutesBetween(before.to, after.from),
    });
  }
  return out;
}

function minutesBetween(start, end) {
  const mins = t => {
    const m = /^(\d{1,2}):(\d{2})$/.exec(String(t || ''));
    return m ? +m[1] * 60 + +m[2] : null;
  };
  const a = mins(start);
  const b = mins(end);
  return a !== null && b !== null && b > a ? b - a : 0;
}

/** «100» → «1 ч 40 мин»: человек считает окно часами, а не минутами. */
function humanGap(minutes) {
  const m = Math.max(0, Math.round(minutes || 0));
  if (!m) return '';
  const h = Math.floor(m / 60);
  const rest = m % 60;
  if (!h) return `${rest} мин`;
  return rest ? `${h} ч ${rest} мин` : `${h} ч`;
}

/** Сколько пар в каждый день выбранной недели — для точек под датами. */
function dayCounts(sched, week) {
  const seen = [0, 1, 2, 3, 4, 5, 6].map(() => new Set());
  for (const l of sched?.lessons || []) {
    if (l.week === week && l.day >= 1 && l.day <= 6) seen[l.day].add(l.pair);
  }
  return seen.map(s => s.size);
}

const minutes = t => {
  const [h, m] = String(t || '0:0').split(':').map(Number);
  return h * 60 + m;
};

/**
 * Текущая и следующая пара на сегодня. Возвращает { current, next, progress }.
 * progress — доля прошедшего времени текущей пары (0..1).
 */
function nowState(sched, week, now = new Date()) {
  const day = ((now.getDay() + 6) % 7) + 1;      // 1..7, где 7 — воскресенье
  if (day > 6) return { current: null, next: null, progress: 0, day };
  const today = lessonsOf(sched, week, day);
  const mins = now.getHours() * 60 + now.getMinutes();
  let current = null, next = null, progress = 0;
  for (const l of today) {
    const a = minutes(l.from), b = minutes(l.to);
    if (mins >= a && mins < b) {
      current = l;
      progress = (mins - a) / (b - a);
    } else if (mins < a && !next) {
      next = l;
    }
  }
  return { current, next, progress, day, today };
}

/** Дата понедельника текущей недели + смещение дня (для полосы дат). */
function weekDates(base = new Date()) {
  const mon = mondayOf(base);
  return Array.from({ length: 6 }, (_, i) => {
    const d = new Date(mon);
    d.setDate(mon.getDate() + i);
    return d;
  });
}

return {'DAY_NAMES': DAY_NAMES, 'DAY_SHORT': DAY_SHORT, 'mondayOf': mondayOf, 'semesterStart': semesterStart, 'weekOfCycle': weekOfCycle, 'parseSubject': parseSubject, 'shortSemestr': shortSemestr, 'fetchSchedule': fetchSchedule, 'lessonsOf': lessonsOf, 'slotsOf': slotsOf, 'gapsOf': gapsOf, 'humanGap': humanGap, 'dayCounts': dayCounts, 'nowState': nowState, 'weekDates': weekDates};
})();

/* ==== js\store.js ==== */
__mod['js/store.js'] = (function () {
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

const settings = read();

// Бот открывает мини-приложение ссылкой вида /?group=ПИН-31 — подхватываем
// группу, чтобы не заставлять выбирать её второй раз.
try {
  const fromBot = new URLSearchParams(location.search).get('group');
  if (fromBot && fromBot !== settings.group) {
    settings.group = fromBot;
    localStorage.setItem(KEY, JSON.stringify(settings));
  }
} catch { /* приватный режим или странный URL — просто игнорируем */ }

function save(patch = {}) {
  Object.assign(settings, patch);
  try {
    localStorage.setItem(KEY, JSON.stringify(settings));
  } catch { /* приватный режим — настройки просто не переживут перезапуск */ }
}

function toggleFavorite(id) {
  const i = settings.favorites.indexOf(id);
  if (i >= 0) settings.favorites.splice(i, 1);
  else settings.favorites.push(id);
  save();
  return i < 0;
}

const isFavorite = id => settings.favorites.includes(id);

function markRead(id) {
  if (!settings.seenNews.includes(id)) {
    settings.seenNews.unshift(id);
    settings.seenNews = settings.seenNews.slice(0, 200);
    save();
  }
}

// ─────────────── данные ───────────────

// Справочные данные — новости, кружки, институты, кампус, список групп.
// Расписание сюда не входит: оно живое, прямо с miet.ru.
const data = {
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

/**
 * Тянет `data/app.json`.
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
async function loadData() {
  try {
    const res = await fetch('data/app.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(`сервер ответил ${res.status}`);
    const fresh = await res.json();
    Object.assign(data, fresh, { stale: false, missing: false });
    try {
      localStorage.setItem(DATA_KEY, JSON.stringify(fresh));
    } catch { /* хранилище переполнено — переживём, просто без копии */ }
    return data;
  } catch (err) {
    console.warn('справочные данные не загрузились:', err.message);
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
function resolveTheme(theme = settings.theme) {
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
function applyTheme(theme = settings.theme) {
  document.documentElement.dataset.theme = resolveTheme(theme);
}

return {'settings': settings, 'save': save, 'toggleFavorite': toggleFavorite, 'isFavorite': isFavorite, 'markRead': markRead, 'data': data, 'loadData': loadData, 'resolveTheme': resolveTheme, 'applyTheme': applyTheme};
})();

/* ==== js\tg.js ==== */
__mod['js/tg.js'] = (function () {
// Интеграция с Telegram Mini Apps. Портировано с tg.ts из дизайн-кита:
// safe-area, тактильная отдача, кнопка «Назад», цвет шапки.
// Вне Telegram (обычный браузер) всё молча деградирует — приложение работает.

const tg = window.Telegram?.WebApp || null;
const inTelegram = Boolean(tg?.initData !== undefined && tg?.platform !== 'unknown');

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

function syncChrome(theme) {
  const color = theme === 'dark' ? '#0F1014' : '#EEF0F5';
  try {
    tg?.setHeaderColor?.(color);
    tg?.setBackgroundColor?.(color);
  } catch { /* старый клиент — не критично */ }
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', color);
}

function initTelegram(theme = 'light', onThemeChange = null) {
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
    // Человек может переключить тему Telegram, не закрывая мини-апп.
    // Кто на это откликается, решает вызывающий: у него настройки.
    if (onThemeChange) tg.onEvent?.('themeChanged', onThemeChange);
  } catch { /* вне Telegram просто нет WebApp API */ }
}

// Тактильная отдача появилась в 6.1 — без проверки старый клиент сыпал
// предупреждениями в консоль на каждое нажатие.
function haptic(style = 'light') {
  if (!supports('6.1')) return;
  try { tg?.HapticFeedback?.impactOccurred?.(style); } catch { /* не критично */ }
}

function hapticNotify(type) {
  if (!supports('6.1')) return;
  try { tg?.HapticFeedback?.notificationOccurred?.(type); } catch { /* не критично */ }
}

function hapticSelect() {
  if (!supports('6.1')) return;
  try { tg?.HapticFeedback?.selectionChanged?.(); } catch { /* не критично */ }
}

/** Аппаратная/системная кнопка «Назад» Telegram. */
const BackButton = {
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

function openLink(url) {
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
function confirmDialog(message) {
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

function alertDialog(message) {
  if (supports('6.2') && tg?.showAlert) {
    try { tg.showAlert(message); return; } catch { /* ниже */ }
  }
  window.alert(message);
}

/** Данные пользователя Telegram, если приложение открыто внутри клиента. */
function tgUser() {
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

function guardTaps(target = document) {
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

return {'tg': tg, 'inTelegram': inTelegram, 'syncChrome': syncChrome, 'initTelegram': initTelegram, 'haptic': haptic, 'hapticNotify': hapticNotify, 'hapticSelect': hapticSelect, 'BackButton': BackButton, 'openLink': openLink, 'confirmDialog': confirmDialog, 'alertDialog': alertDialog, 'tgUser': tgUser, 'guardTaps': guardTaps};
})();

/* ==== js\ui.js ==== */
__mod['js/ui.js'] = (function () {
// Мелкие компоненты по образцу дизайн-кита: списки-карточки, пилюли,
// сегмент-контрол, шторка снизу, пустое состояние.

var icon = __mod['js/icons.js']['icon'];
var haptic = __mod['js/tg.js']['haptic'];
var hapticSelect = __mod['js/tg.js']['hapticSelect'];

const esc = s => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

/** Строит DOM-узел из HTML-строки. */
function el(html) {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

/** Делегирование: клик по любому потомку, подходящему под селектор. */
function on(root, selector, handler, event = 'click') {
  root.addEventListener(event, e => {
    const target = e.target.closest(selector);
    if (target && root.contains(target)) handler(e, target);
  });
}

// ─────────────── строки списка ───────────────

/** Круглая плитка с SVG-иконкой — единый левый элемент всех строк списка. */
const iconTile = (name, size = 34) =>
  `<div class="icon-tile" style="width:${size}px;height:${size}px">
     ${icon(name, Math.round(size * 0.56))}
   </div>`;

function listRow({ ico, emoji, title, sub, value, chevron = false, id = '', cls = '' }) {
  // ico важнее emoji: эмодзи остались только там, где иконки ещё нет.
  const left = ico ? iconTile(ico)
    : emoji ? `<div class="icon-tile">${emoji}</div>` : '';
  return `
    <div class="list-row ${cls}" ${id ? `data-id="${esc(id)}"` : ''}>
      ${left}
      <div class="list-row-body">
        <div class="row-title">${esc(title)}</div>
        ${sub ? `<div class="row-subtitle">${esc(sub)}</div>` : ''}
      </div>
      ${value ? `<div class="list-row-value">${esc(value)}</div>` : ''}
      ${chevron ? `<span class="chevron">${icon('chevronRight', 18)}</span>` : ''}
    </div>`;
}

const listCard = rows => `<div class="list-card">${rows.join('')}</div>`;

// ─────────────── пилюли и сегменты ───────────────

/** items: [{id, label}] — горизонтальный скроллящийся ряд. */
function pillRow(items, activeId, name = 'pill') {
  return `<div class="pill-row" data-pills="${name}">${items.map(i => `
    <button class="pill ${i.id === activeId ? 'active' : ''}" data-pill="${esc(i.id)}">
      ${i.emoji ? `${i.emoji} ` : ''}${esc(i.label)}
    </button>`).join('')}</div>`;
}

function segmented(items, activeId, name = 'seg') {
  return `<div class="segmented" data-seg="${name}">${items.map(i => `
    <button class="segmented-item ${i.id === activeId ? 'active' : ''}" data-segitem="${esc(i.id)}">
      ${esc(i.label)}
    </button>`).join('')}</div>`;
}

/** Вешает обработчик выбора на ряд пилюль или сегмент-контрол. */
function bindChoice(root, name, onChange, kind = 'pill') {
  const attr = kind === 'pill' ? 'pill' : 'segitem';
  const container = root.querySelector(`[data-${kind === 'pill' ? 'pills' : 'seg'}="${name}"]`);
  if (!container) return;
  container.addEventListener('click', e => {
    const btn = e.target.closest(`[data-${attr}]`);
    if (!btn) return;
    const active = kind === 'pill' ? 'pill' : 'segmented-item';
    container.querySelectorAll(`.${active}`).forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    hapticSelect();
    onChange(btn.dataset[attr]);
  });
}

// ─────────────── прочее ───────────────

const emptyState = (text, ico = 'folder') => `
  <div class="empty-state">
    <div class="empty-icon">${icon(ico, 30)}</div>
    <div>${esc(text)}</div>
  </div>`;

const toggle = (on, id = '') =>
  `<div class="toggle ${on ? 'on' : ''}" ${id ? `data-toggle="${esc(id)}"` : ''}>
     <div class="toggle-knob"></div>
   </div>`;

const kpi = (number, label) =>
  `<div class="kpi-tile"><div class="kpi-number">${esc(number)}</div>
   <div class="kpi-label">${esc(label)}</div></div>`;

const skeleton = (h = 74) =>
  `<div class="skeleton" style="height:${h}px"></div>`;

// ─────────────── шторка снизу ───────────────

const layer = () => document.getElementById('layer');

/**
 * Шторка снизу. Возвращает объект с close(). Контент передаётся строкой,
 * onMount получает корневой узел тела — там можно навесить обработчики.
 */
function sheet({ title, body, onMount, cancel = 'Отмена', height }) {
  const backdrop = el('<div class="sheet-backdrop"></div>');
  const node = el(`
    <div class="sheet">
      <div class="sheet-handle"></div>
      <div class="sheet-header">
        <button class="sheet-cancel">${esc(cancel)}</button>
        <div class="sheet-title">${esc(title)}</div>
      </div>
      <div class="sheet-body" ${height ? `style="max-height:${height}"` : ''}>${body}</div>
    </div>`);

  let closed = false;
  function close() {
    if (closed) return;
    closed = true;
    node.style.transition = 'transform .2s ease';
    node.style.transform = 'translate(-50%, 100%)';
    backdrop.style.transition = 'opacity .2s ease';
    backdrop.style.opacity = '0';
    setTimeout(() => { backdrop.remove(); node.remove(); }, 200);
    document.body.style.overflow = '';
  }

  backdrop.addEventListener('click', close);
  node.querySelector('.sheet-cancel').addEventListener('click', () => { haptic(); close(); });

  layer().append(backdrop, node);
  document.body.style.overflow = 'hidden';
  onMount?.(node.querySelector('.sheet-body'), close);
  return { close, node };
}

/** Короткое всплывающее сообщение по центру снизу. */
function toast(message) {
  const t = el(`<div style="
    position:fixed; left:50%; bottom:calc(100px + var(--safe-bottom));
    transform:translateX(-50%); z-index:200; max-width:80%;
    background:rgba(21,23,28,.9); color:#fff; font-size:14px; font-weight:600;
    padding:11px 18px; border-radius:999px; text-align:center;
    opacity:0; transition:opacity .2s ease;">${esc(message)}</div>`);
  layer().append(t);
  requestAnimationFrame(() => { t.style.opacity = '1'; });
  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 250);
  }, 1900);
}

/** Полноэкранный просмотр фото по тапу. */
function lightbox(src) {
  const b = el(`<div style="
    position:fixed; inset:0; z-index:150; background:rgba(0,0,0,.92);
    display:flex; align-items:center; justify-content:center; padding:20px;">
    <img src="${esc(src)}" style="max-width:100%; max-height:100%;
      border-radius:14px; object-fit:contain" decoding="async">
  </div>`);
  b.addEventListener('click', () => b.remove());
  layer().append(b);
}

/** Ряд контактов: телефон, почта, аудитория — каждый кликабелен. */
function contactRows({ lead, phone, inner, email, room, address, site }) {
  const rows = [];
  if (lead) rows.push(listRow({ ico: 'teacher', title: lead, sub: 'Руководитель' }));
  if (phone) rows.push(`<a class="list-row tap" href="tel:${esc(phone.replace(/[^\d+]/g, ''))}">
      <div class="list-row-icon" style="background:var(--primary-dim);color:var(--primary)">${icon('phone', 18)}</div>
      <div class="list-row-body"><div class="row-title">${esc(phone)}</div>
      <div class="row-subtitle">${inner ? `Внутренний ${esc(inner)}` : 'Телефон'}</div></div>
    </a>`);
  if (email) rows.push(`<a class="list-row tap" href="mailto:${esc(email)}">
      <div class="list-row-icon" style="background:var(--primary-dim);color:var(--primary)">${icon('mail', 18)}</div>
      <div class="list-row-body"><div class="row-title">${esc(email)}</div>
      <div class="row-subtitle">Почта</div></div>
    </a>`);
  if (room) rows.push(listRow({ ico: 'door', title: `Аудитория ${room}`, sub: 'Где найти' }));
  if (address) rows.push(listRow({ ico: 'pin', title: address, sub: 'Адрес' }));
  if (site) rows.push(listRow({ ico: 'external', title: site, sub: 'Сайт' }));
  return rows.length ? listCard(rows) : '';
}

return {'esc': esc, 'el': el, '$': $, '$$': $$, 'on': on, 'iconTile': iconTile, 'listRow': listRow, 'listCard': listCard, 'pillRow': pillRow, 'segmented': segmented, 'bindChoice': bindChoice, 'emptyState': emptyState, 'toggle': toggle, 'kpi': kpi, 'skeleton': skeleton, 'sheet': sheet, 'toast': toast, 'lightbox': lightbox, 'contactRows': contactRows};
})();

/* ==== js\api.js ==== */
__mod['js/api.js'] = (function () {
// Разговор с серверной частью: кто я и что тут происходит.
//
// Сервер узнаёт человека по initData — подписанной строке, которую Telegram
// кладёт в мини-приложение. Отправляем её заголовком на каждый запрос:
// своих токенов и кук нет, а подделать подпись без токена бота нельзя.
//
// Вне Telegram (обычный браузер, локальная отладка) initData пустая — тогда
// сеть не трогаем вовсе и приложение работает как раньше, без учёта.

var API_BASE = __mod['js/config.js']['API_BASE'];
var tg = __mod['js/tg.js']['tg'];

const initData = tg?.initData || '';
const canTalk = Boolean(API_BASE && initData);

/** Кто я по мнению сервера. Заполняется в loadMe(), до неё — пусто. */
const account = {
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

const get = (path, opts) => request(path, opts);
const post = (path, body, opts) => request(path, { ...opts, method: 'POST', body });

/**
 * Спрашивает сервер, кто мы. Ошибку глотает: без сервера приложение обязано
 * работать — просто без админки и без переноса группы между устройствами.
 */
async function loadMe() {
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
function track(kind, name = '') {
  if (!canTalk || account.blocked) return;
  queue.push({ kind, name });
  if (timer) return;
  timer = setTimeout(flush, 1500);
}

/** Сообщает серверу выбранную группу — чтобы бот и приложение знали одну. */
function syncGroup(group) {
  if (!canTalk || !group) return;
  pendingGroup = group;
  if (!timer) timer = setTimeout(flush, 300);
}

function flush() {
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

return {'canTalk': canTalk, 'account': account, 'get': get, 'post': post, 'loadMe': loadMe, 'track': track, 'syncGroup': syncGroup, 'flush': flush};
})();

/* ==== js\art.js ==== */
__mod['js/art.js'] = (function () {
// Иллюстрации — там, где иконки мало.
//
// Иконка размером с букву объясняет строку списка, но пустой экран ею не
// вылечишь: «пар нет» с серым кружком посередине читается как поломка, а
// не как свободный вечер. Здесь сцены — крупные, рисованные теми же
// линиями, что и иконки (обводка 1.75, скруглённые концы), поэтому они
// не спорят с интерфейсом и не выглядят наклейками из другого набора.
//
// Цвет берётся из темы: обводка — currentColor, заливки — токены. Значит
// одна и та же картинка живёт и в светлой теме, и в тёмной, и меняется
// вместе с ними — растровые пришлось бы держать в двух копиях.
//
// Своего файла им хватает: разрастётся набор — не утянет за собой
// icons.js, который импортирует каждый экран.

var esc = __mod['js/ui.js']['esc'];

const S = {
  // ── свободное время ──

  // Кружка и пар над ней: день кончился, можно выдохнуть.
  free: `
    <path d="M28 46h34v20a14 14 0 0 1-14 14h-6a14 14 0 0 1-14-14V46Z" fill="var(--tone-soft)"/>
    <path d="M28 46h34v20a14 14 0 0 1-14 14h-6a14 14 0 0 1-14-14V46Z"/>
    <path d="M62 52h6a8 8 0 0 1 0 16h-6"/>
    <path d="M22 86h46"/>
    <path d="M38 34c0-4 4-4 4-8s-4-4-4-8M50 34c0-4 4-4 4-8s-4-4-4-8"
          opacity="0.55"/>`,

  // Календарь с галочкой: на сегодня всё.
  done: `
    <rect x="16" y="24" width="68" height="60" rx="10" fill="var(--tone-soft)"/>
    <rect x="16" y="24" width="68" height="60" rx="10"/>
    <path d="M16 42h68M34 16v14M66 16v14"/>
    <path d="m38 60 8 8 16-16" stroke="var(--tone-ink)"/>`,

  // Луна и звёзды: выходной или поздний вечер.
  rest: `
    <path d="M64 30a26 26 0 1 1-26 26 20 20 0 0 0 26-26Z" fill="var(--tone-soft)"/>
    <path d="M64 30a26 26 0 1 1-26 26 20 20 0 0 0 26-26Z"/>
    <path d="M22 26h6M25 23v6M76 62h6M79 59v6" opacity="0.6"/>`,

  // ── когда чего-то не хватает ──

  // Карточка группы: расписание есть, а чьё — ещё не выбрано.
  group: `
    <rect x="14" y="26" width="72" height="52" rx="10" fill="var(--tone-soft)"/>
    <rect x="14" y="26" width="72" height="52" rx="10"/>
    <circle cx="36" cy="46" r="8"/>
    <path d="M24 66a12 12 0 0 1 24 0"/>
    <path d="M58 42h18M58 52h18M58 62h12" opacity="0.75"/>`,

  // Облако с антенной: сеть подвела, данные не приехали.
  offline: `
    <path d="M32 68a14 14 0 0 1 1.6-27.9A20 20 0 0 1 71 46a12 12 0 0 1-1 22Z"
          fill="var(--tone-soft)"/>
    <path d="M32 68a14 14 0 0 1 1.6-27.9A20 20 0 0 1 71 46a12 12 0 0 1-1 22Z"/>
    <path d="m40 78 20-20M40 58l20 20" stroke="var(--tone-ink)" opacity="0.8"/>`,

  // Стопка книг: раздел пока пуст, но место под него есть.
  empty: `
    <rect x="20" y="58" width="60" height="14" rx="4" fill="var(--tone-soft)"/>
    <rect x="20" y="58" width="60" height="14" rx="4"/>
    <rect x="26" y="44" width="48" height="14" rx="4"/>
    <rect x="32" y="30" width="36" height="14" rx="4" fill="var(--tone-soft)"/>
    <rect x="32" y="30" width="36" height="14" rx="4"/>
    <path d="M20 80h60" opacity="0.5"/>`,
};

/**
 * Иллюстрация по имени.
 *
 * Размер задаётся высотой: сцены рисованы в квадрате 100×100 и тянутся
 * пропорционально, поэтому в карточке и на пустом экране это одна и та
 * же картинка, а не две подогнанные.
 */
function art(name, size = 96, cls = '') {
  const body = S[name] || S.empty;
  return `<svg class="art ${cls}" width="${size}" height="${size}"
    viewBox="0 0 100 100" fill="none" stroke="currentColor"
    stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${body}</svg>`;
}

const hasArt = name => Object.hasOwn(S, name);
const artNames = Object.keys(S);

/** Пустое состояние с иллюстрацией — для экранов, а не для строк списка. */
const artState = (name, title, note = '') => `
  <div class="art-state">
    ${art(name, 104)}
    <div class="art-title">${esc(title)}</div>
    ${note ? `<div class="art-note">${esc(note)}</div>` : ''}
  </div>`;

return {'art': art, 'hasArt': hasArt, 'artNames': artNames, 'artState': artState};
})();

/* ==== js\router.js ==== */
__mod['js/router.js'] = (function () {
// Роутер: стек экранов + нижняя навигация. Системная кнопка «Назад»
// Telegram показывается только когда есть куда возвращаться.

var icon = __mod['js/icons.js']['icon'];
var BackButton = __mod['js/tg.js']['BackButton'];
var haptic = __mod['js/tg.js']['haptic'];
var hapticSelect = __mod['js/tg.js']['hapticSelect'];
var inTelegram = __mod['js/tg.js']['inTelegram'];
var track = __mod['js/api.js']['track'];

const routes = new Map();
const stack = [];
let appEl, navEl;

// Четыре вкладки — предел, после которого подписи начинают жаться, а
// нижняя панель превращается в свалку. Кружки и профиль переехали внутрь
// «Полезного»: туда заходят по делу, а не постоянно.
const TABS = [
  { id: 'home', label: 'Главная', ico: 'home' },
  { id: 'schedule', label: 'Расписание', ico: 'calendar' },
  { id: 'news', label: 'Лента', ico: 'news' },
  { id: 'useful', label: 'Полезное', ico: 'grid' },
];

const isTab = name => TABS.some(t => t.id === name);

function register(name, renderFn) {
  routes.set(name, renderFn);
}

function init(appNode, navNode) {
  appEl = appNode;
  navEl = navNode;
  navEl.innerHTML = TABS.map(t => `
    <button class="bottom-nav-item" data-tab="${t.id}">
      ${icon(t.ico, 22)}
      <span class="bottom-nav-label">${t.label}</span>
    </button>`).join('');
  navEl.addEventListener('click', e => {
    const b = e.target.closest('[data-tab]');
    if (!b) return;
    hapticSelect();
    switchTab(b.dataset.tab);
  });
  navEl.hidden = false;
}

function syncNav() {
  const cur = stack[stack.length - 1];
  const tabName = stack[0]?.name;
  navEl.hidden = false;
  navEl.querySelectorAll('[data-tab]').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabName);
  });
  if (stack.length > 1) BackButton.show(back);
  else BackButton.hide();
  void cur;
}

async function paint() {
  const entry = stack[stack.length - 1];
  const fn = routes.get(entry.name);
  if (!fn) {
    appEl.innerHTML = `<div class="screen"><div class="empty-state">Экран «${entry.name}» не найден</div></div>`;
    return;
  }
  appEl.innerHTML = `<div class="screen"><div class="stack">
      <div class="skeleton" style="height:34px;width:60%"></div>
      <div class="skeleton" style="height:120px"></div>
      <div class="skeleton" style="height:84px"></div>
      <div class="skeleton" style="height:84px"></div>
    </div></div>`;
  let node;
  try {
    node = await fn(entry.params || {});
  } catch (err) {
    console.error(err);
    node = document.createElement('div');
    node.className = 'screen';
    node.innerHTML = `<div class="empty-state">
        <div style="font-size:34px">⚠️</div>
        <div>${err.message || 'Что-то пошло не так'}</div>
      </div>`;
  }
  appEl.innerHTML = '';
  appEl.append(node);

  // Вне Telegram системной кнопки «Назад» нет — рисуем свою поверх экрана.
  if (!inTelegram && stack.length > 1) {
    const btn = document.createElement('button');
    btn.className = 'icon-btn back-fab';
    btn.innerHTML = icon('chevronLeft', 20);
    btn.addEventListener('click', back);
    appEl.append(btn);
    // Над обложкой кнопка висит поверх картинки и ничему не мешает,
    // а вот на заголовок экрана она бы налезла — освобождаем место.
    node.classList.add('with-back');
  }

  window.scrollTo(0, entry.scrollTop || 0);
  syncNav();
}

function go(name, params = {}) {
  const cur = stack[stack.length - 1];
  if (cur) cur.scrollTop = window.scrollY;
  stack.push({ name, params, scrollTop: 0 });
  // В учёт идёт только имя экрана. Параметры (какая новость, какой кружок)
  // не пишем: это уже слежка за человеком, а не за тем, чем пользуются.
  track('screen', name);
  // Своя запись в истории — чтобы аппаратная «Назад» на Android и кнопка
  // браузера вели по стеку экранов, а не закрывали приложение.
  try { history.pushState({ depth: stack.length }, ''); } catch { /* не критично */ }
  haptic('light');
  paint();
}

/** Пятится на экран назад. Саму работу делает обработчик popstate. */
function back() {
  if (stack.length <= 1) return;
  haptic('light');
  try { history.back(); } catch { popScreen(); }
}

function popScreen() {
  if (stack.length <= 1) return;
  stack.pop();
  paint();
}

window.addEventListener('popstate', popScreen);

function switchTab(name) {
  if (stack.length === 1 && stack[0].name === name) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }
  track('tab', name);
  stack.length = 0;
  stack.push({ name, params: {}, scrollTop: 0 });
  paint();
}

/** Перерисовать текущий экран, сохранив позицию прокрутки. */
function refresh() {
  const cur = stack[stack.length - 1];
  if (cur) cur.scrollTop = window.scrollY;
  paint();
}

const current = () => stack[stack.length - 1];
const depth = () => stack.length;


return {'TABS': TABS, 'register': register, 'init': init, 'go': go, 'back': back, 'switchTab': switchTab, 'refresh': refresh, 'current': current, 'depth': depth, 'isTab': isTab};
})();

/* ==== js\screens\common.js ==== */
__mod['js/screens/common.js'] = (function () {
// Общие куски экранов: шапка, выбор группы, карточка новости.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var el = __mod['js/ui.js']['el'];
var sheet = __mod['js/ui.js']['sheet'];
var listRow = __mod['js/ui.js']['listRow'];
var listCard = __mod['js/ui.js']['listCard'];
var emptyState = __mod['js/ui.js']['emptyState'];
var artState = __mod['js/art.js']['artState'];
var data = __mod['js/store.js']['data'];
var settings = __mod['js/store.js']['settings'];
var save = __mod['js/store.js']['save'];
var haptic = __mod['js/tg.js']['haptic'];
var syncGroup = __mod['js/api.js']['syncGroup'];

/** Экран-контейнер с заголовком и подзаголовком. */
function screen({ title, subtitle, actions = '', body, small = false }) {
  const node = el(`<div class="screen"></div>`);
  node.innerHTML = `
    ${title ? `<div class="screen-top">
      <div>
        <h1 class="h1-page ${small ? 'small' : ''}">${esc(title)}</h1>
        ${subtitle ? `<p class="subtitle-page">${esc(subtitle)}</p>` : ''}
      </div>
      ${actions ? `<div class="header-actions">${actions}</div>` : ''}
    </div>` : ''}
    ${body}`;
  return node;
}

const iconBtn = (name, action) =>
  `<button class="icon-btn" data-action="${esc(action)}">${icon(name, 19)}</button>`;

/**
 * Шторка выбора учебной группы: поиск по 346 группам с моментальной
 * фильтрацией. onPick получает название группы.
 */
function pickGroup(onPick) {
  const groups = data.groups || [];
  const body = `
    <div class="search-box" style="margin-bottom:12px">
      ${icon('search', 19, 'muted')}
      <input id="gq" type="search" placeholder="Например, ПИН-31" autocomplete="off"
             enterkeyhint="search" spellcheck="false">
    </div>
    <div class="sheet-list" id="glist"></div>`;

  sheet({
    title: 'Выбор группы',
    body,
    onMount(root, close) {
      const input = root.querySelector('#gq');
      const list = root.querySelector('#glist');

      const draw = q => {
        const needle = q.trim().toLowerCase().replace(/\s+/g, '');
        const found = needle
          ? groups.filter(g => g.toLowerCase().replace(/\s+/g, '').includes(needle))
          : groups;
        if (!found.length) {
          // Пустой список без запроса — это не «нет такой группы», а
          // «справочник не приехал»: 346 групп лежат в data/app.json, и
          // без него искать просто негде.
          list.innerHTML = groups.length
            ? emptyState('Такой группы нет', 'search')
            : artState('offline', 'Список групп не загрузился',
              'Закрой и открой приложение — он лежит рядом с ним и обычно приезжает сразу');
          return;
        }
        list.innerHTML = listCard(found.slice(0, 120).map(g => listRow({
          title: g,
          id: g,
          cls: 'tap',
          value: g === settings.group ? '✓' : '',
        })));
      };

      draw('');
      input.addEventListener('input', () => draw(input.value));
      list.addEventListener('click', e => {
        const row = e.target.closest('[data-id]');
        if (!row) return;
        haptic('medium');
        save({ group: row.dataset.id });
        // Единственное место, где группу выбирают руками, — отсюда и
        // сообщаем её боту, чтобы в личке было то же расписание.
        syncGroup(row.dataset.id);
        close();
        onPick?.(row.dataset.id);
      });
      setTimeout(() => input.focus({ preventScroll: true }), 120);
    },
  });
}

/** Большая карточка новости с обложкой. */
const newsCard = n => `
  <div class="news-card" data-news="${esc(n.id)}">
    ${n.cover ? `<img class="news-cover" src="img/${esc(n.cover)}" alt="" loading="lazy" decoding="async">` : ''}
    <div class="news-body">
      <div class="news-title">${esc(n.title)}</div>
      <div class="news-date">${esc(n.date)}</div>
    </div>
  </div>`;

/** Компактная строка новости для главной. */
const newsRow = n => `
  <div class="news-row" data-news="${esc(n.id)}">
    ${n.cover
      ? `<img src="img/${esc(n.cover)}" alt="" loading="lazy" decoding="async">`
      : `<div class="news-row-stub">${icon('news', 24)}</div>`}
    <div style="flex:1;min-width:0">
      <div class="news-row-title">${esc(n.title)}</div>
      <div class="news-date" style="margin-top:5px">${esc(n.date)}</div>
    </div>
  </div>`;

const MONTHS_GEN = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
const WEEKDAYS = ['воскресенье', 'понедельник', 'вторник', 'среда',
  'четверг', 'пятница', 'суббота'];

const humanDate = (d = new Date()) =>
  `${WEEKDAYS[d.getDay()]}, ${d.getDate()} ${MONTHS_GEN[d.getMonth()]}`;

const shortDate = (d = new Date()) =>
  `${d.getDate()} ${MONTHS_GEN[d.getMonth()]}`;

return {'screen': screen, 'iconBtn': iconBtn, 'pickGroup': pickGroup, 'newsCard': newsCard, 'newsRow': newsRow, 'humanDate': humanDate, 'shortDate': shortDate};
})();

/* ==== js\screens\community.js ==== */
__mod['js/screens/community.js'] = (function () {
// Чаты, сообщества и кураторы.
//
// Все ссылки здесь проверены вручную: открыты, подтверждены как
// официальные (по описанию канала) и записаны с указанием, откуда взяты.
// Выдуманная ссылка в таком разделе хуже, чем его отсутствие: человек
// уйдёт по ней в чужой чат и решит, что это университетский.
//
// Сообщества конкретных кружков не дублируются: они уже лежат в карточке
// каждого кружка вместе с контактами руководителя.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var data = __mod['js/store.js']['data'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

// Проверено 7 сентября 2026: каждая ссылка открывается, у телеграм-каналов
// сверено описание — оба заявляют себя официальными.
const OFFICIAL = [
  { title: 'НИУ МИЭТ', sub: 'Официальный канал университета · 7,4 тыс. подписчиков',
    url: 'https://t.me/UniversitetMIET', ico: 'messageCircle', tag: 'Telegram' },
  { title: 'МИЭТ ВКонтакте', sub: 'Новости, анонсы, фотоотчёты',
    url: 'https://vk.com/miet.university', ico: 'users', tag: 'ВКонтакте' },
  { title: 'МИЭТ на RuTube', sub: 'Видео с мероприятий и лекции',
    url: 'https://rutube.ru/channel/23788890/', ico: 'video', tag: 'RuTube' },
  { title: 'MIET University', sub: 'Архив видео университета',
    url: 'https://www.youtube.com/MIETuniversity', ico: 'video', tag: 'YouTube' },
];

const STUDENT = [
  { title: 'Студсовет МИЭТ', sub: 'Канал студенческого актива · 1,4 тыс. подписчиков',
    url: 'https://t.me/miet_one', ico: 'megaphone', tag: 'Telegram' },
  { title: 'Студсовет ВКонтакте', sub: 'Мероприятия, наборы, проекты',
    url: 'https://vk.com/miet_one', ico: 'users', tag: 'ВКонтакте' },
  { title: 'Профком студентов', sub: 'Матпомощь, путёвки, защита прав',
    url: 'https://vk.com/profcommiet', ico: 'handshake', tag: 'ВКонтакте' },
  { title: 'Привет, МИЭТ!', sub: 'Справочник первокурсника от внеучебного управления',
    url: 'https://privet-miet.ru', ico: 'compass', tag: 'Сайт' },
];

const linkRow = l => `
  <div class="list-row tap" data-url="${esc(l.url)}">
    <div class="icon-tile">${icon(l.ico, 19)}</div>
    <div class="list-row-body">
      <div class="row-title">${esc(l.title)}</div>
      <div class="row-subtitle">${esc(l.sub)}</div>
    </div>
    <span class="chip">${esc(l.tag)}</span>
  </div>`;

async function chatsScreen() {
  const withSocial = (data.clubs || []).filter(c => (c.social || []).length);

  const node = screen({
    title: 'Чаты и сообщества',
    subtitle: 'Куда подписаться, чтобы быть в курсе',
    body: `
      <div class="section-head" style="margin-top:0">
        <div class="section-title">Официальные</div>
      </div>
      <p class="section-note">Каналы самого университета.</p>
      <div class="list-card">${OFFICIAL.map(linkRow).join('')}</div>

      <div class="section-head"><div class="section-title">Студенческие</div></div>
      <p class="section-note">Те, кто занимается жизнью вне пар.</p>
      <div class="list-card">${STUDENT.map(linkRow).join('')}</div>

      <div class="section-head"><div class="section-title">Сообщества кружков</div></div>
      <p class="section-note">
        У ${withSocial.length} из ${(data.clubs || []).length} объединений есть
        свои группы — они лежат в карточке каждого кружка вместе с контактами
        руководителя.
      </p>
      <button class="btn-secondary" id="clubs">Открыть кружки</button>

      <div class="fab-note">
        Ссылки проверены вручную. Если какая-то перестала открываться или
        появился новый официальный чат — напиши в поддержку, добавлю.
      </div>`,
  });

  node.querySelector('#clubs').addEventListener('click', () => go('clubs'));
  node.addEventListener('click', e => {
    const row = e.target.closest('[data-url]');
    if (row) openLink(row.dataset.url);
  });
  return node;
}

// ─────────────── кураторы ───────────────

// Собрано со справочника первокурсника privet-miet.ru/active и страницы
// студсовета miet.ru/page/105283. Ничего не додумано: то, чего на этих
// страницах нет — например, личных контактов кураторов, — здесь нет тоже.
const CURATOR_HELP = [
  ['Первые недели', 'Электронный пропуск, банковская карта, учебники в '
    + 'библиотеке, медосмотр — куратор показывает, где это получают.'],
  ['Внутри группы', 'Выборы старосты и профорга, знакомство друг с другом, '
    + 'дни группы.'],
  ['Мероприятия', 'Квесты, посвящение в студенты, Кубок первокурсника, '
    + 'научные события и дни карьеры.'],
  ['Вопросы про быт', 'Как устроено общежитие, куда идти с проблемой, '
    + 'что делать с долгами и справками.'],
];

async function curatorsScreen() {
  const node = screen({
    title: 'Кураторы',
    subtitle: 'Старшекурсники, которые ведут первый курс',
    body: `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:6px">Кто это</div>
        <div class="row-subtitle" style="line-height:1.55">
          Студенты второго курса и старше, которые помогают первокурсникам
          освоиться. Кураторы встречают группу в первый день занятий и
          остаются на связи весь первый семестр.
        </div>
      </div>

      <div class="section-head"><div class="section-title">С чем помогают</div></div>
      <div class="stack">
        ${CURATOR_HELP.map(([t, s]) => `
          <div class="card" style="padding:14px 16px">
            <div class="row-title" style="margin-bottom:4px">${esc(t)}</div>
            <div class="row-subtitle" style="line-height:1.5">${esc(s)}</div>
          </div>`).join('')}
      </div>

      <div class="section-head"><div class="section-title">Как найти своего</div></div>
      <p class="section-note">
        Куратора назначают группе — если связь потерялась, спрашивай в
        отделе по работе с первокурсниками студсовета.
      </p>
      <div class="list-card">
        <div class="list-row">
          <div class="icon-tile">${icon('door', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">Студенческий совет</div>
            <div class="row-subtitle">Аудитория 3352</div>
          </div>
        </div>
        <a class="list-row tap" href="tel:+74997208522">
          <div class="icon-tile">${icon('phone', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">+7 499 720-85-22</div>
            <div class="row-subtitle">Студенческий офис</div>
          </div>
        </a>
        <div class="list-row tap" data-url="https://t.me/miet_one">
          <div class="icon-tile">${icon('messageCircle', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">Канал студсовета</div>
            <div class="row-subtitle">Наборы, мероприятия, объявления</div>
          </div>
          <span class="chip">Telegram</span>
        </div>
      </div>

      <div class="section-head"><div class="section-title">Стать куратором</div></div>
      <div class="card" style="padding:16px">
        <div class="row-subtitle" style="line-height:1.55">
          Со второго курса можно пройти Школу кураторов — её проводит
          студсовет. После обучения выдают синий галстук: это знак системы
          кураторства в МИЭТ. Наборы объявляют в канале студсовета.
        </div>
      </div>

      <button class="btn-secondary" id="privet" style="margin-top:14px">
        ${icon('external', 17)} Справочник первокурсника
      </button>

      <div class="fab-note">
        По материалам privet-miet.ru и страницы студсовета на miet.ru.
      </div>`,
  });

  node.querySelector('#privet').addEventListener('click',
    () => openLink('https://privet-miet.ru/active'));
  node.addEventListener('click', e => {
    const row = e.target.closest('[data-url]');
    if (row) openLink(row.dataset.url);
  });
  return node;
}

return {'chatsScreen': chatsScreen, 'curatorsScreen': curatorsScreen};
})();

/* ==== js\screens\feed.js ==== */
__mod['js/screens/feed.js'] = (function () {
// Лента: посты, написанные людьми, и свежие новости с miet.ru.
//
// Экран целиком серверный. Архив новостей, собранный в data/app.json,
// показывается отдельным экраном — он статичен и живёт своей жизнью.
//
// Без сервера (обычный браузер, отладка) лента просто не показывается:
// приложение остаётся рабочим, как и всё остальное здесь.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var el = __mod['js/ui.js']['el'];
var emptyState = __mod['js/ui.js']['emptyState'];
var toast = __mod['js/ui.js']['toast'];
var sheet = __mod['js/ui.js']['sheet'];
var lightbox = __mod['js/ui.js']['lightbox'];
var get = __mod['js/api.js']['get'];
var post = __mod['js/api.js']['post'];
var account = __mod['js/api.js']['account'];
var canTalk = __mod['js/api.js']['canTalk'];
var API_BASE = __mod['js/config.js']['API_BASE'];
var data = __mod['js/store.js']['data'];
var settings = __mod['js/store.js']['settings'];
var go = __mod['js/router.js']['go'];
var refresh = __mod['js/router.js']['refresh'];
var haptic = __mod['js/tg.js']['haptic'];
var hapticNotify = __mod['js/tg.js']['hapticNotify'];
var confirmDialog = __mod['js/tg.js']['confirmDialog'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];
var pickGroup = __mod['js/screens/common.js']['pickGroup'];

const mediaUrl = name => `${API_BASE}/media/${encodeURIComponent(name)}`;

/**
 * Размеры картинки — из её же имени: сервер дописывает их при
 * сохранении («<хеш>-1200x800.jpg»). Старые файлы без хвоста
 * возвращают null, и тогда место под картинку занять нечем.
 */
function mediaSize(name) {
  const m = /-(\d{1,5})x(\d{1,5})\.[a-z]+$/i.exec(String(name || ''));
  if (!m) return null;
  const w = +m[1];
  const h = +m[2];
  return w > 0 && h > 0 ? { w, h } : null;
}

/**
 * Картинка поста своими пропорциями.
 *
 * Единое соотношение для всех резало скриншоты расписания пополам, а
 * их в студенческой ленте больше, чем фотографий. Поэтому место
 * занимается по настоящим сторонам картинки — лента не прыгает и не
 * обрезает.
 *
 * Исключение — очень высокие: снимок экрана телефона занял бы собой всю
 * ленту. Им отводится место высотой в четыре пятых ширины, а сама
 * картинка вписывается целиком, с полями по бокам: лучше поля, чем
 * срезанная половина расписания.
 */
function mediaTag(name, cls = 'post-media', full = true) {
  const url = mediaUrl(name);
  const size = mediaSize(name);
  const tall = size && size.h / size.w > 1.25;
  const ratio = !size ? '' : tall
    ? 'style="aspect-ratio:4/5"'
    : `style="aspect-ratio:${size.w}/${size.h}"`;
  return `<img class="${cls}${tall ? ' tall' : ''}${size ? '' : ' unsized'}"
    src="${url}" alt="" ${ratio}
    ${full ? `data-full="${url}"` : ''} loading="lazy" decoding="async">`;
}

// Последняя удачно полученная лента. Нужна ровно на случай, когда сервер
// не ответил: пустой экран выглядит как поломка приложения, а вчерашние
// записи — как то, чем они и являются.
const CACHE_KEY = 'miet-feed-cache';

function remember(feed) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), feed }));
  } catch { /* приватный режим — обойдёмся без запаса */ }
}

function cached() {
  try {
    const saved = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
    // Неделя — предел, после которого показывать старое уже вредно.
    if (saved && Date.now() - saved.at < 7 * 24 * 3600 * 1000) return saved.feed;
  } catch { /* испорченный кеш — как будто его нет */ }
  return null;
}

/** Время с сервера приходит в UTC — без Z браузер прочтёт его как местное. */
const parseTs = ts => new Date(String(ts || '').replace(' ', 'T') + 'Z');

function ago(ts) {
  const min = Math.floor((Date.now() - parseTs(ts).getTime()) / 60000);
  if (min < 1) return 'только что';
  if (min < 60) return `${min} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const d = Math.floor(h / 24);
  if (d === 1) return 'вчера';
  if (d < 7) return `${d} дн назад`;
  return parseTs(ts).toLocaleDateString('ru-RU');
}

/** Абзацы поста. Текст пользовательский, поэтому экранируется весь. */
const paragraphs = text => (text || '')
  .split(/\n{2,}/).map(p => p.trim()).filter(Boolean)
  .map(p => `<p>${esc(p)}</p>`).join('');

// Длина, после которой текст в ленте сворачивается. Новости с сайта — это
// несколько тысяч знаков; развёрнутыми они превращают ленту в простыню, и
// до второй записи никто не долистывает.
const LONG = 240;

/** Первая фраза — она же превью в свёрнутом виде и строка на главной. */
function excerpt(text, limit = 130) {
  const flat = String(text || '').replace(/\s+/g, ' ').trim();
  if (flat.length <= limit) return flat;
  const cut = flat.slice(0, limit);
  // Режем по границе слова: обрывок посреди слова выглядит поломкой.
  const space = cut.lastIndexOf(' ');
  return (space > limit * 0.6 ? cut.slice(0, space) : cut).trimEnd() + '…';
}

// ─────────────── карточка ───────────────

function pollBlock(p) {
  if (!p.poll) return '';
  const voted = p.poll.my_option != null;
  return `
    <div class="poll">
      ${p.poll.options.map(o => `
        <button class="poll-option ${o.id === p.poll.my_option ? 'mine' : ''}"
                data-vote="${o.id}" ${voted ? 'data-voted="1"' : ''}>
          <span class="poll-fill" style="width:${voted ? o.share : 0}%"></span>
          <span class="poll-text">${esc(o.text)}</span>
          <span class="poll-share">${voted ? o.share + '%' : ''}</span>
        </button>`).join('')}
      <div class="poll-total">
        ${p.poll.total ? `${p.poll.total} ${plural(p.poll.total, 'голос', 'голоса', 'голосов')}`
    : 'Голосов пока нет'}
      </div>
    </div>`;
}

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

function reactionsBlock(p, all) {
  return `
    <div class="reaction-row">
      ${all.map(e => {
    const found = p.reactions.find(r => r.emoji === e);
    const mine = p.my_reaction === e;
    return `<button class="reaction ${mine ? 'mine' : ''}" data-react="${esc(e)}">
              <span>${e}</span>${found ? `<b>${found.count}</b>` : ''}
            </button>`;
  }).join('')}
    </div>`;
}

function postCard(p, reactions, expanded = false) {
  const closed = p.audience === 'groups';
  const long = (p.text || '').length > LONG;
  const folded = long && !expanded;
  return `
    <article class="card post" data-post="${p.id}">
      ${p.pinned ? `<div class="post-flag">${icon('flag', 14)} Закреплено</div>` : ''}
      ${p.media ? mediaTag(p.media) : ''}
      <div class="post-body">
        ${p.title ? `<div class="post-title">${esc(p.title)}</div>` : ''}
        <div class="post-text ${folded ? 'folded' : ''}">${paragraphs(p.text)}</div>
        ${long ? `<button class="post-more" data-more="${p.id}">
          ${folded ? 'Подробнее' : 'Свернуть'}
        </button>` : ''}
        ${closed ? `<div class="post-audience">${icon('users', 14)}
          Только для: ${p.groups.map(esc).join(', ')}</div>` : ''}
        ${pollBlock(p)}
        ${reactionsBlock(p, reactions)}
        <div class="post-foot">
          <span class="post-author">${esc(p.author_label || 'МИЭТ')}</span>
          ${p.anon && p.author_id
      ? `<span class="post-unmask" title="Видно только модерации">id ${p.author_id}</span>`
      : ''}
          <span>·</span>
          <span>${esc(ago(p.published_at))}</span>
          <button class="post-talk" data-talk="${p.id}">
            ${icon('messageCircle', 14)} ${p.comments}
          </button>
          <span class="post-reads">${icon('eye', 14)} ${p.reads}</span>
          ${p.kind === 'news' && p.url
      ? `<button class="post-link" data-open="${esc(p.url)}">на miet.ru</button>` : ''}
          ${(p.mine || account.can_delete || account.can_pin)
      ? `<button class="post-menu" data-menu="${p.id}">${icon('sliders', 16)}</button>` : ''}
        </div>
      </div>
    </article>`;
}

/**
 * Компактная строка для главной: обложка, заголовок или начало текста,
 * когда это было. Целиком запись читается в ленте — здесь только повод
 * туда заглянуть.
 */
const feedRow = p => `
  <div class="feed-row" data-feed="${p.id}">
    ${p.media
    ? `<img src="${mediaUrl(p.media)}" alt="" loading="lazy" decoding="async">`
    : `<div class="icon-tile" style="width:56px;height:56px;border-radius:14px">
         ${icon(p.kind === 'news' ? 'news' : 'megaphone', 22)}</div>`}
    <div style="flex:1;min-width:0">
      <div class="feed-row-title">${esc(p.title || excerpt(p.text, 90))}</div>
      <div class="feed-row-meta">
        ${esc(p.author_label || 'МИЭТ')} · ${esc(ago(p.published_at))}
        ${p.reads ? ` · ${p.reads} ${plural(p.reads, 'просмотр', 'просмотра', 'просмотров')}` : ''}
      </div>
    </div>
  </div>`;

// ─────────────── экран ───────────────

async function feedScreen() {
  if (!canTalk) {
    return screen({
      title: 'Лента',
      body: emptyState('Лента работает внутри Telegram', 'inbox'),
    });
  }

  let feed = null;
  let failure = null;
  try {
    feed = await get('/api/feed?limit=30', { timeout: 15000 });
    remember(feed);
  } catch (err) {
    failure = err;
    // Показать вчерашнюю ленту честнее, чем пустой экран: человек хотя бы
    // видит, что было, и понимает, что не загрузилось именно свежее.
    feed = cached();
  }

  if (!feed) {
    const node = screen({
      title: 'Лента',
      body: `<div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:6px">Лента не загрузилась</div>
        <div class="row-subtitle" style="margin-bottom:14px">${esc(failure.message)}</div>
        <button class="btn-primary" id="retry">Повторить</button>
      </div>`,
    });
    node.querySelector('#retry').addEventListener('click', () => refresh());
    return node;
  }

  const archive = (data.news || []).length;
  const node = screen({
    title: 'Лента',
    subtitle: 'Новости университета и объявления',
    body: `
      ${account.can_write ? `
        <button class="btn-primary compose-btn" id="write">
          ${icon('edit', 18)} Написать
        </button>` : ''}
      ${account.can_moderate ? `
        <button class="btn-secondary" id="moderation" style="margin-top:10px">
          Модерация постов
        </button>` : ''}
      ${failure ? `
        <div class="stale-note">
          Свежее не загрузилось (${esc(failure.message)}) — показываю последнее.
          <button class="stale-retry" id="retry">Обновить</button>
        </div>` : ''}
      <div class="stack" id="list" style="margin-top:14px">
        ${feed.posts.length
    ? feed.posts.map(p => postCard(p, feed.reactions)).join('')
    : emptyState('Пока пусто. Здесь появятся объявления и новости', 'inbox')}
      </div>
      ${archive ? `
        <button class="btn-secondary" id="archive" style="margin-top:14px">
          Архив новостей miet.ru · ${archive}
        </button>` : ''}`,
  });

  const known = new Map(feed.posts.map(p => [p.id, p]));

  node.querySelector('#write')?.addEventListener('click', () => composer());
  node.querySelector('#moderation')?.addEventListener('click', () => go('moderation'));
  node.querySelector('#archive')?.addEventListener('click', () => go('newsArchive'));
  node.querySelector('#retry')?.addEventListener('click', () => refresh());

  // Какие посты человек развернул. Держим отдельно от данных: перерисовка
  // карточки после реакции или голоса не должна её схлопывать.
  const opened = new Set();

  node.addEventListener('click', async e => {
    const card = e.target.closest('[data-post]');
    const id = card && +card.dataset.post;

    const more = e.target.closest('[data-more]');
    if (more) {
      opened.has(id) ? opened.delete(id) : opened.add(id);
      haptic('light');
      card.outerHTML = postCard(known.get(id), feed.reactions, opened.has(id));
      return;
    }

    const img = e.target.closest('[data-full]');
    if (img) return lightbox(img.dataset.full);

    const link = e.target.closest('[data-open]');
    if (link) return openLink(link.dataset.open);

    const vote = e.target.closest('[data-vote]');
    if (vote) {
      haptic('light');
      try {
        const r = await post(`/api/posts/${id}/vote`, { option: +vote.dataset.vote });
        known.set(id, r.post);
        card.outerHTML = postCard(r.post, feed.reactions, opened.has(id));
      } catch (err) { toast(err.message); }
      return;
    }

    const react = e.target.closest('[data-react]');
    if (react) {
      haptic('light');
      try {
        const r = await post(`/api/posts/${id}/react`, { emoji: react.dataset.react });
        known.set(id, r.post);
        card.outerHTML = postCard(r.post, feed.reactions, opened.has(id));
      } catch (err) { toast(err.message); }
      return;
    }

    const talk = e.target.closest('[data-talk]');
    if (talk) {
      return comments(id, updated => {
        // Счётчик под постом должен сойтись с тем, что человек только что
        // видел в шторке, — иначе выглядит, будто комментарий пропал.
        const p = { ...known.get(id), comments: updated };
        known.set(id, p);
        node.querySelector(`[data-post="${id}"]`)?.replaceWith(
          el(postCard(p, feed.reactions, opened.has(id))));
      });
    }

    const menu = e.target.closest('[data-menu]');
    if (menu) return cardMenu(known.get(id));
  });

  // Прочтение отмечается, когда карточка действительно побывала на экране:
  // «прочитал» — это увидел, а не «лента загрузилась в фоне».
  watchReads(node, known);
  return node;
}

function watchReads(node, known) {
  if (!('IntersectionObserver' in window)) return;
  const seen = new Set();
  const io = new IntersectionObserver(entries => {
    for (const en of entries) {
      const id = +en.target.dataset.post;
      if (!en.isIntersecting || seen.has(id)) continue;
      const p = known.get(id);
      seen.add(id);
      io.unobserve(en.target);
      if (p && !p.read) post(`/api/posts/${id}/read`, {}).catch(() => { });
    }
  }, { threshold: 0.6 });
  node.querySelectorAll('[data-post]').forEach(el => io.observe(el));
}

async function cardMenu(p) {
  if (!p) return;
  const rows = [];
  if (account.can_pin) rows.push(p.pinned ? 'unpin' : 'pin');
  if (p.mine || account.can_delete) rows.push('delete');
  if (!rows.length) return;

  sheet({
    title: 'Что сделать с постом',
    body: `
      <div class="stack">
        ${rows.includes('pin') ? '<button class="btn-secondary" data-do="pin">Закрепить сверху</button>' : ''}
        ${rows.includes('unpin') ? '<button class="btn-secondary" data-do="unpin">Открепить</button>' : ''}
        ${rows.includes('delete') ? '<button class="btn-secondary danger-btn" data-do="delete">Удалить</button>' : ''}
      </div>`,
    onMount(root, close) {
      root.addEventListener('click', async e => {
        const b = e.target.closest('[data-do]');
        if (!b) return;
        try {
          if (b.dataset.do === 'delete') {
            if (!await confirmDialog('Удалить пост? Это навсегда.')) return;
            await post(`/api/posts/${p.id}/delete`, {});
          } else {
            await post(`/api/posts/${p.id}/pin`, { pinned: b.dataset.do === 'pin' });
          }
          hapticNotify('success');
          close();
          refresh();
        } catch (err) { toast(err.message); }
      });
    },
  });
}

// ─────────────── комментарии ───────────────

/**
 * Шторка обсуждения. Открывается поверх ленты, а не отдельным экраном:
 * комментарий обычно читают, не теряя из виду сам пост.
 *
 * onChange получает новое число комментариев — карточка под шторкой
 * должна показывать то же, что человек только что видел.
 */
function comments(postId, onChange) {
  let list = [];
  let canClean = false;
  let replyTo = null;     // на чей комментарий отвечаем

  /** Ссылка на аккаунт в Telegram. Без ника открыть профиль нельзя. */
  const contactLink = c => {
    if (!c.contact) return '';
    return c.contact.username
      ? `<button class="comment-contact" data-tg="${esc(c.contact.username)}">
           ${icon('external', 13)} @${esc(c.contact.username)}
         </button>`
      : `<span class="comment-contact muted" title="Ник в Telegram не задан">
           id ${c.contact.id}
         </span>`;
  };

  const line = c => `
    <div class="comment ${c.reply_to ? 'reply' : ''}" data-comment="${c.id}">
      <div class="comment-head">
        <span class="comment-author">${esc(c.author_name)}</span>
        <span class="comment-role">${esc(c.author_label)}</span>
        ${contactLink(c)}
        <span class="comment-time">${esc(ago(c.created_at))}</span>
        ${(c.author_id === account.id || canClean)
      ? `<button class="comment-drop" data-drop="${c.id}">${icon('trash', 15)}</button>`
      : ''}
      </div>
      <div class="comment-text">${esc(c.text)}</div>
      <button class="comment-reply" data-reply="${c.id}">Ответить</button>
    </div>`;

  sheet({
    title: 'Комментарии',
    height: '76vh',
    body: `
      <div id="clist"><div class="skeleton" style="height:80px"></div></div>
      <div class="comment-form">
        <div class="reply-note" id="rnote" hidden>
          <span id="rwho"></span>
          <button class="reply-cancel" id="rcancel">${icon('x', 14)}</button>
        </div>
        <div class="comment-input-row">
          <input class="field-input" id="ctext" placeholder="Написать комментарий"
                 maxlength="1000" autocomplete="off">
          <button class="btn-primary" id="csend">Отправить</button>
        </div>
      </div>`,
    onMount(root) {
      const box = root.querySelector('#clist');
      const input = root.querySelector('#ctext');
      const send = root.querySelector('#csend');

      const draw = () => {
        box.innerHTML = list.length
          ? `<div class="stack">${list.map(line).join('')}</div>`
          : emptyState('Пока никто не написал. Будь первым', 'messageCircle');
        onChange?.(list.length);
      };

      const load = () => get(`/api/posts/${postId}/comments`)
        .then(r => { list = r.comments; canClean = r.can_moderate; draw(); });

      load().catch(err => { box.innerHTML = errorCard(err); });

      const note = root.querySelector('#rnote');
      const who = root.querySelector('#rwho');

      const setReply = c => {
        replyTo = c ? c.id : null;
        note.hidden = !c;
        if (c) {
          who.textContent = `Ответ ${c.author_name}: ${excerpt(c.text, 40)}`;
          input.focus();
        }
      };
      root.querySelector('#rcancel').addEventListener('click', () => setReply(null));

      send.addEventListener('click', async () => {
        const text = input.value.trim();
        if (!text) return;
        send.disabled = true;
        try {
          await post(`/api/posts/${postId}/comments`,
            { text, reply_to: replyTo });
          setReply(null);
          input.value = '';
          // Перечитываем список целиком: порядок веток собирает сервер, и
          // дописывать ответ в конец на клиенте значило бы решать это
          // второй раз — с шансом решить иначе.
          await load();
          hapticNotify('success');
          // Прокручиваем к своему: длинное обсуждение иначе оставляет
          // человека наверху, и кажется, что ничего не отправилось.
          box.lastElementChild?.lastElementChild?.scrollIntoView(
            { behavior: 'smooth', block: 'nearest' });
        } catch (err) {
          toast(err.message);
        } finally {
          send.disabled = false;
        }
      });

      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') send.click();
      });

      box.addEventListener('click', async e => {
        const tg = e.target.closest('[data-tg]');
        if (tg) return openLink(`https://t.me/${tg.dataset.tg}`);

        const reply = e.target.closest('[data-reply]');
        if (reply) {
          haptic('light');
          return setReply(list.find(c => String(c.id) === reply.dataset.reply));
        }

        const drop = e.target.closest('[data-drop]');
        if (!drop) return;
        if (!await confirmDialog('Удалить комментарий?')) return;
        try {
          await post(`/api/comments/${drop.dataset.drop}/delete`, {});
          // Ответы уходят вместе с родителем — так же, как на сервере.
          const gone = Number(drop.dataset.drop);
          list = list.filter(c => c.id !== gone && c.reply_to !== gone);
          draw();
        } catch (err) { toast(err.message); }
      });
    },
  });
}

// ─────────────── редактор поста ───────────────

function composer() {
  let groups = [];
  let image = '';
  let anon = false;

  sheet({
    title: 'Новый пост',
    height: '78vh',
    body: `
      <div class="field-group">
        <div class="field-label">Текст</div>
        <textarea class="field-input" id="text" rows="5"
                  placeholder="Что рассказать?"></textarea>
      </div>

      <div class="field-group">
        <div class="field-label">Опрос — по желанию</div>
        <input class="field-input" id="o1" placeholder="Вариант 1">
        <input class="field-input" id="o2" placeholder="Вариант 2" style="margin-top:8px">
        <input class="field-input" id="o3" placeholder="Вариант 3" style="margin-top:8px">
      </div>

      <div class="field-group">
        <div class="field-label">Картинка</div>
        <input type="file" id="file" accept="image/*" class="field-input">
        <div class="row-subtitle" id="imgnote" style="margin-top:6px"></div>
      </div>

      <div class="field-group">
        <div class="field-label">Кому видно</div>
        <div class="list-card">
          <div class="list-row tap" id="pick">
            <div class="list-row-body">
              <div class="row-title">Группы</div>
              <div class="row-subtitle" id="aud">Всем</div>
            </div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">Анонимно</div>
              <div class="row-subtitle">${account.can_anon
    ? 'Подпись «Анонимно», публикуется сразу'
    : 'Появится в ленте после одобрения'}</div>
            </div>
            <div class="toggle" data-toggle="anon"><div class="toggle-knob"></div></div>
          </div>
        </div>
      </div>

      ${account.premoderate ? `
        <div class="warn-note">
          ${icon('info', 16)}
          Пост появится в ленте после одобрения — сейчас так работает вся
          лента, а не только анонимные записи.
        </div>` : ''}

      <button class="btn-primary" id="send">
        ${account.premoderate ? 'Отправить на одобрение' : 'Опубликовать'}
      </button>`,
    onMount(root, close) {
      const aud = root.querySelector('#aud');

      root.querySelector('#pick').addEventListener('click', () => {
        pickGroups(groups, picked => {
          groups = picked;
          aud.textContent = groups.length ? groups.join(', ') : 'Всем';
        });
      });

      root.querySelector('[data-toggle="anon"]').addEventListener('click', e => {
        anon = !anon;
        e.currentTarget.classList.toggle('on', anon);
        haptic('light');
      });

      root.querySelector('#file').addEventListener('change', e => {
        const f = e.target.files?.[0];
        const note = root.querySelector('#imgnote');
        if (!f) { image = ''; note.textContent = ''; return; }
        if (f.size > 5 * 1024 * 1024) {
          image = '';
          note.textContent = 'Слишком большая — нужно меньше 5 МБ';
          return;
        }
        const reader = new FileReader();
        reader.onload = () => { image = reader.result; note.textContent = f.name; };
        reader.readAsDataURL(f);
      });

      root.querySelector('#send').addEventListener('click', async () => {
        const text = root.querySelector('#text').value.trim();
        const options = ['o1', 'o2', 'o3']
          .map(id => root.querySelector('#' + id).value.trim()).filter(Boolean);
        if (!text) return toast('Напиши текст');
        if (options.length === 1) return toast('В опросе нужно минимум два варианта');
        const btn = root.querySelector('#send');
        btn.disabled = true;
        btn.textContent = 'Публикую…';
        try {
          const r = await post('/api/posts', { text, options, groups, anon, image });
          hapticNotify('success');
          close();
          toast(r.pending ? 'Отправлено на одобрение' : 'Опубликовано');
          // Пост в очереди в ленте не появится — обновлять её незачем,
          // но человек должен видеть, что кнопка сработала.
          refresh();
        } catch (err) {
          toast(err.message);
          btn.disabled = false;
          btn.textContent = 'Опубликовать';
        }
      });
    },
  });
}

/** Выбор групп-получателей: тот же список, что и в настройках, но с галочками. */
function pickGroups(current, onDone) {
  const all = data.groups || [];
  const picked = new Set(current);
  sheet({
    title: 'Кому показать',
    body: `
      <div class="row-subtitle" style="margin-bottom:12px">
        Ничего не выбрано — пост увидят все. Выбранные группы увидят только они.
      </div>
      <div class="search-box" style="margin-bottom:12px">
        ${icon('search', 19, 'muted')}
        <input id="gq" type="search" placeholder="Например, ПИН-31" autocomplete="off">
      </div>
      <div class="sheet-list" id="glist"></div>
      <button class="btn-primary" id="done" style="margin-top:12px">Готово</button>`,
    onMount(root, close) {
      const list = root.querySelector('#glist');
      const draw = q => {
        const needle = q.trim().toLowerCase().replace(/\s+/g, '');
        const found = (needle
          ? all.filter(g => g.toLowerCase().replace(/\s+/g, '').includes(needle))
          : [...picked, ...all.filter(g => !picked.has(g))]).slice(0, 120);
        list.innerHTML = `<div class="list-card">${found.map(g => `
          <div class="list-row tap" data-g="${esc(g)}">
            <div class="list-row-body"><div class="row-title">${esc(g)}</div></div>
            ${picked.has(g) ? `<span class="chevron">${icon('check', 18)}</span>` : ''}
          </div>`).join('')}</div>`;
      };
      draw('');
      root.querySelector('#gq').addEventListener('input', e => draw(e.target.value));
      list.addEventListener('click', e => {
        const row = e.target.closest('[data-g]');
        if (!row) return;
        const g = row.dataset.g;
        picked.has(g) ? picked.delete(g) : picked.add(g);
        haptic('light');
        draw(root.querySelector('#gq').value);
      });
      root.querySelector('#done').addEventListener('click', () => {
        onDone([...picked]);
        close();
      });
    },
  });
}

// ─────────────── очередь модерации ───────────────

async function moderationScreen() {
  let queue;
  try {
    queue = await get('/api/admin/moderation');
  } catch (err) {
    return screen({ title: 'Модерация', body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const node = screen({
    title: 'Модерация',
    subtitle: 'Анонимные посты ждут разрешения',
    body: queue.posts.length ? `<div class="stack">${queue.posts.map(p => `
      <div class="card post" data-post="${p.id}">
        ${p.media ? mediaTag(p.media, 'post-media', false) : ''}
        <div class="post-body">
          <div class="post-text">${paragraphs(p.text)}</div>
          <div class="post-foot">
            <span class="post-author">Автор: id ${p.author_id}</span>
            <span>·</span><span>${esc(ago(p.created_at))}</span>
          </div>
          <div class="stack" style="margin-top:12px">
            <button class="btn-primary" data-ok="${p.id}">Опубликовать</button>
            <button class="btn-secondary danger-btn" data-no="${p.id}">Отклонить</button>
          </div>
        </div>
      </div>`).join('')}</div>`
      : emptyState('Очередь пуста', 'check'),
  });

  node.addEventListener('click', async e => {
    const ok = e.target.closest('[data-ok]');
    const no = e.target.closest('[data-no]');
    if (!ok && !no) return;
    const id = (ok || no).dataset.ok || (ok || no).dataset.no;
    try {
      await post(`/api/admin/posts/${id}/${ok ? 'approve' : 'reject'}`, {});
      hapticNotify('success');
      toast(ok ? 'Опубликовано' : 'Отклонено');
      refresh();
    } catch (err) { toast(err.message); }
  });

  return node;
}

void settings;

return {'default': feedScreen, 'mediaSize': mediaSize, 'mediaTag': mediaTag, 'excerpt': excerpt, 'postCard': postCard, 'feedRow': feedRow, 'moderationScreen': moderationScreen};
})();

/* ==== js\screens\guide.js ==== */
__mod['js/screens/guide.js'] = (function () {
// Справочные экраны: словарь первокурсника, контакты и ключевые даты.
//
// Всё, что здесь написано про МИЭТ, взято из данных приложения или из
// расписания. Там, где точной информации нет — сроки сессии, правила
// конкретной кафедры, — стоит ссылка на официальный источник, а не
// придуманная дата: неверная дата хуже её отсутствия.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var data = __mod['js/store.js']['data'];
var settings = __mod['js/store.js']['settings'];
var fetchSchedule = __mod['js/schedule.js']['fetchSchedule'];
var weekOfCycle = __mod['js/schedule.js']['weekOfCycle'];
var semesterStart = __mod['js/schedule.js']['semesterStart'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

// ─────────────── словарь ───────────────

const TERMS = [
  ['ОРИОКС', 'Система, где живут баллы, задания и оценки. Туда же '
    + 'преподаватели выкладывают материалы. Вход по логину из деканата.',
  'учёба'],
  ['БРС', 'Балльно-рейтинговая система: за семестр набирается 100 баллов — '
    + 'часть за контрольные точки в течение семестра, часть за экзамен или '
    + 'зачёт. Вес каждой части задаёт кафедра, он виден в ОРИОКС.', 'учёба'],
  ['КТ', 'Контрольная точка — промежуточная проверка внутри семестра: '
    + 'коллоквиум, контрольная, защита лабораторной. Баллы за неё идут в БРС.',
  'учёба'],
  ['Автомат', 'Оценка без экзамена, если баллов за семестр уже достаточно. '
    + 'Право поставить автомат — решение преподавателя, а не правило.', 'учёба'],
  ['Допуск', 'Минимум баллов, без которого до экзамена не допускают. '
    + 'Обычно закрывается сдачей долгов до сессии.', 'учёба'],
  ['Пересдача', 'Повторная сдача после незачёта. Первые две — преподавателю, '
    + 'третья — комиссии. Сроки назначает деканат.', 'учёба'],
  ['Неделя цикла', 'Расписание МИЭТ повторяется каждые четыре недели. '
    + 'Поэтому в приложении и в боте всегда указано, какая сейчас неделя: '
    + 'от неё зависит, какие пары в этот день.', 'учёба'],
  ['Деканат', 'Отдел института, который ведёт группы: справки, переводы, '
    + 'допуски, стипендия, академический отпуск. Первое место, куда идти с '
    + 'любым вопросом про учёбу.', 'место'],
  ['УВЦ', 'Военный учебный центр. Занятия у тех, кто поступил на военную '
    + 'подготовку; в расписании стоят как обычные пары.', 'место'],
  ['КЭИ', 'Колледж электроники и информатики при МИЭТ — среднее '
    + 'профессиональное образование, свой набор и свои группы.', 'место'],
  ['ПИШ', 'Передовая инженерная школа — программа подготовки под задачи '
    + 'микроэлектронной промышленности.', 'место'],
  ['СНО', 'Студенческое научное общество: конференции, публикации, помощь '
    + 'с первой научной работой.', 'место'],
  ['Академ', 'Академический отпуск — перерыв в учёбе по здоровью, семейным '
    + 'обстоятельствам или призыву, с сохранением места. Оформляется через '
    + 'деканат.', 'бумаги'],
  ['Соцстипендия', 'Стипендия по социальным основаниям — назначается '
    + 'отдельно от академической, по документам о доходе или льготном '
    + 'статусе. Подробности — в разделе «Деньги».', 'бумаги'],
  ['Справка об обучении', 'Документ для военкомата, банка, работы или '
    + 'проездного. Заказывается в личном кабинете или в деканате.', 'бумаги'],
  ['Обходной', 'Лист, который подписывают перед выпуском или отчислением: '
    + 'библиотека, общежитие, кафедра. Без него не отдадут документы.',
  'бумаги'],
];

const TERM_TAGS = { учёба: 'Учёба', место: 'Где что', бумаги: 'Документы' };

async function glossaryScreen() {
  let active = 'all';

  const node = screen({
    title: 'Словарь',
    subtitle: 'Что означают слова, которые все вокруг уже знают',
    body: `
      <div class="search-box" style="margin-bottom:12px">
        ${icon('search', 19, 'muted')}
        <input id="gq" type="search" placeholder="Найти термин" autocomplete="off">
      </div>
      <div class="pill-row" id="tags" style="margin-bottom:14px">
        <button class="pill active" data-tag="all">Все</button>
        ${Object.entries(TERM_TAGS).map(([id, label]) =>
      `<button class="pill" data-tag="${id}">${esc(label)}</button>`).join('')}
      </div>
      <div id="terms" class="stack"></div>`,
  });

  const box = node.querySelector('#terms');
  const draw = (q = '') => {
    const needle = q.trim().toLowerCase();
    const found = TERMS.filter(([name, text, tag]) =>
      (active === 'all' || tag === active)
      && (!needle || name.toLowerCase().includes(needle)
        || text.toLowerCase().includes(needle)));
    box.innerHTML = found.length ? found.map(([name, text]) => `
      <div class="card" style="padding:14px 16px">
        <div class="row-title" style="margin-bottom:4px">${esc(name)}</div>
        <div class="row-subtitle" style="line-height:1.5">${esc(text)}</div>
      </div>`).join('') : emptyState('Такого термина пока нет', 'search');
  };
  draw();

  node.querySelector('#gq').addEventListener('input', e => draw(e.target.value));
  node.querySelector('#tags').addEventListener('click', e => {
    const b = e.target.closest('[data-tag]');
    if (!b) return;
    active = b.dataset.tag;
    node.querySelectorAll('#tags .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    draw(node.querySelector('#gq').value);
  });

  return node;
}

// ─────────────── контакты ───────────────

/** Телефон в виде, пригодном для набора: только цифры и плюс. */
const dial = phone => String(phone || '').replace(/[^\d+]/g, '');

const contactRow = c => `
  <a class="list-row tap" href="tel:${esc(dial(c.phone))}">
    <div class="icon-tile">${icon(c.ico || 'phone', 19)}</div>
    <div class="list-row-body">
      <div class="row-title">${esc(c.title)}</div>
      <div class="row-subtitle">
        ${esc(c.phone)}${c.inner ? ` · внутр. ${esc(c.inner)}` : ''}
        ${c.room ? ` · ауд. ${esc(c.room)}` : ''}
      </div>
    </div>
  </a>`;

const mailRow = c => `
  <a class="list-row tap" href="mailto:${esc(c.email)}">
    <div class="icon-tile">${icon('mail', 19)}</div>
    <div class="list-row-body">
      <div class="row-title">${esc(c.title)}</div>
      <div class="row-subtitle">${esc(c.email)}</div>
    </div>
  </a>`;

async function contactsScreen() {
  const uni = data.university || {};
  // Контакты не выдуманы: подразделения кампуса и институты приезжают с
  // сайта вместе с телефонами, почтой и аудиториями.
  const places = (data.campus || []).filter(c => c.phone || c.email);
  const institutes = (data.institutes || []).filter(i => i.phone || i.email);

  const node = screen({
    title: 'Контакты',
    subtitle: 'Куда звонить и писать',
    body: `
      <div class="section-head" style="margin-top:0">
        <div class="section-title">Университет</div>
      </div>
      <div class="list-card">
        ${uni.phone ? contactRow({ title: 'Приёмная', phone: uni.phone, ico: 'landmark' }) : ''}
        ${uni.email ? mailRow({ title: 'Общая почта', email: uni.email }) : ''}
        ${uni.address ? `
          <div class="list-row">
            <div class="icon-tile">${icon('pin', 19)}</div>
            <div class="list-row-body">
              <div class="row-title">${esc(uni.address)}</div>
              <div class="row-subtitle">Главный корпус</div>
            </div>
          </div>` : ''}
      </div>
      ${uni.address ? `
        <button class="btn-secondary" id="map" style="margin-top:10px">
          ${icon('map', 17)} Открыть на карте
        </button>` : ''}

      <div class="section-head"><div class="section-title">Подразделения</div></div>
      <p class="section-note">Библиотека, столовая, здравпункт и остальное.</p>
      <div class="list-card">
        ${places.length ? places.map(p => p.phone
      ? contactRow({ title: p.title, phone: p.phone, inner: p.inner,
        room: p.room, ico: p.icon })
      : mailRow({ title: p.title, email: p.email })).join('')
    : emptyState('Контакты подразделений не собраны', 'phone')}
      </div>

      <div class="section-head"><div class="section-title">Институты</div></div>
      <p class="section-note">Деканат — первое место с любым вопросом про учёбу.</p>
      <div class="list-card">
        ${institutes.map(i => `
          <div class="list-row tap" data-inst="${esc(i.id)}">
            <div class="icon-tile">${icon('graduate', 19)}</div>
            <div class="list-row-body">
              <div class="row-title">${esc(i.short || i.name)}</div>
              <div class="row-subtitle">
                ${esc(i.phone || i.email || '')}${i.room ? ` · ауд. ${esc(i.room)}` : ''}
              </div>
            </div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>`).join('')}
      </div>

      <div class="fab-note">
        Номера собраны с miet.ru вместе с остальными данными приложения.
      </div>`,
  });

  node.querySelector('#map')?.addEventListener('click', () =>
    openLink('https://yandex.ru/maps/?text='
      + encodeURIComponent(`${uni.name || 'МИЭТ'} ${uni.address || ''}`)));

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-inst]');
    if (row) go('institute', { id: row.dataset.inst });
  });

  return node;
}

// ─────────────── ключевые даты ───────────────

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
  'августа', 'сентября', 'октября', 'ноября', 'декабря'];

const human = d => `${d.getDate()} ${MONTHS[d.getMonth()]}`;

async function datesScreen() {
  const node = screen({
    title: 'Ключевые даты',
    subtitle: 'Где мы сейчас в семестре',
    body: '<div id="dslot"><div class="skeleton" style="height:150px"></div></div>',
  });

  const slot = node.querySelector('#dslot');
  let sched = null;
  if (settings.group) {
    try {
      sched = await fetchSchedule(settings.group);
    } catch { /* покажем то, что знаем без расписания */ }
  }

  const now = new Date();
  const start = sched ? semesterStart(sched.semestr) : null;
  const week = sched ? weekOfCycle(now, sched.semestr, settings.weekShift) : null;
  const passed = start
    ? Math.max(0, Math.floor((now - start) / (7 * 24 * 3600 * 1000)) + 1) : null;

  slot.innerHTML = `
    ${sched ? `
      <div class="card" style="padding:18px">
        <div class="now-kicker">${esc(sched.semestr)}</div>
        <div style="font-size:22px;font-weight:800;margin:6px 0 2px">
          ${week + 1}-я неделя цикла
        </div>
        <div class="row-subtitle">
          Идёт ${passed}-я учебная неделя · семестр начался ${esc(human(start))}
        </div>
      </div>

      <div class="kpi-grid" style="margin-top:12px">
        <div class="kpi-tile">
          <div class="kpi-number">${passed}</div>
          <div class="kpi-label">Недель позади</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${week + 1}/4</div>
          <div class="kpi-label">Неделя цикла</div>
        </div>
      </div>` : `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:6px">Сначала выбери группу</div>
        <div class="row-subtitle">
          Без неё не из чего считать неделю цикла и начало семестра.
        </div>
      </div>`}

    <div class="section-head"><div class="section-title">Как устроен год</div></div>
    <div class="list-card">
      ${[
      ['Осенний семестр', 'Начинается 1 сентября, идёт до зимней сессии', 'calendar'],
      ['Весенний семестр', 'Начинается в феврале — отсчёт недель цикла стартует заново', 'calendar'],
      ['Сессия', 'Экзамены после каждого семестра; допуск закрывается до её начала', 'clipboard'],
      ['Пересдачи', 'Назначает деканат после сессии, третья попытка — комиссии', 'refresh'],
    ].map(([t, s, ico]) => `
        <div class="list-row">
          <div class="icon-tile">${icon(ico, 19)}</div>
          <div class="list-row-body">
            <div class="row-title">${esc(t)}</div>
            <div class="row-subtitle">${esc(s)}</div>
          </div>
        </div>`).join('')}
    </div>

    <div class="section-head"><div class="section-title">Точные даты</div></div>
    <p class="section-note">
      Сроки сессии и каникул каждый год объявляет университет — приложение
      их не выдумывает.
    </p>
    <div class="stack">
      <button class="btn-secondary" data-url="https://www.miet.ru/schedule">
        График учебного процесса
      </button>
      <button class="btn-secondary" data-url="https://orioks.miet.ru/main/login">
        Сроки контрольных точек в ОРИОКС
      </button>
    </div>`;

  node.addEventListener('click', e => {
    const b = e.target.closest('[data-url]');
    if (b) openLink(b.dataset.url);
  });

  return node;
}

return {'glossaryScreen': glossaryScreen, 'contactsScreen': contactsScreen, 'datesScreen': datesScreen};
})();

/* ==== js\screens\help.js ==== */
__mod['js/screens/help.js'] = (function () {
// Помощь в заданиях: доска «нужна помощь» и «могу помочь».
//
// Смысл раздела — свести двух людей, поэтому ник автора виден всем, кто
// открыл объявление. Экран обязан сказать об этом до публикации, а не
// после: человек должен понимать, что оставляет контакт.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var toast = __mod['js/ui.js']['toast'];
var sheet = __mod['js/ui.js']['sheet'];
var get = __mod['js/api.js']['get'];
var post = __mod['js/api.js']['post'];
var account = __mod['js/api.js']['account'];
var canTalk = __mod['js/api.js']['canTalk'];
var refresh = __mod['js/router.js']['refresh'];
var haptic = __mod['js/tg.js']['haptic'];
var hapticNotify = __mod['js/tg.js']['hapticNotify'];
var confirmDialog = __mod['js/tg.js']['confirmDialog'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

let kind = 'need';   // какую сторону доски показываем

const parseTs = ts => new Date(String(ts || '').replace(' ', 'T') + 'Z');

function ago(ts) {
  const min = Math.floor((Date.now() - parseTs(ts).getTime()) / 60000);
  if (min < 60) return `${Math.max(1, min)} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const d = Math.floor(h / 24);
  return d === 1 ? 'вчера' : `${d} дн назад`;
}

const card = (o, me) => `
  <div class="card offer ${o.status === 'closed' ? 'closed' : ''}" data-offer="${o.id}">
    <div class="offer-head">
      <span class="offer-kind ${o.kind}">
        ${o.kind === 'need' ? 'Нужна помощь' : 'Могу помочь'}
      </span>
      ${o.price === 'deal' ? '<span class="chip">по договорённости</span>'
    : '<span class="chip">бесплатно</span>'}
      ${o.status === 'closed' ? '<span class="chip">закрыто</span>' : ''}
    </div>
    <div class="offer-subject">${esc(o.subject)}</div>
    ${o.text ? `<div class="offer-text">${esc(o.text)}</div>` : ''}
    <div class="offer-foot">
      <span>${esc(o.author_name)}${o.group ? ` · ${esc(o.group)}` : ''}</span>
      <span>·</span>
      <span>${esc(ago(o.created_at))}</span>
    </div>
    <div class="offer-actions">
      ${o.author_id === me.id ? `
        <button class="btn-secondary" data-do="${o.status === 'open' ? 'close' : 'reopen'}"
                data-id="${o.id}">
          ${o.status === 'open' ? 'Вопрос решён' : 'Открыть снова'}
        </button>
        <button class="btn-secondary danger-btn" data-do="delete" data-id="${o.id}">
          Удалить
        </button>`
    : o.username ? `
        <button class="btn-primary" data-write="${esc(o.username)}">
          ${icon('messageCircle', 17)} Написать
        </button>`
      : `<div class="row-subtitle">У автора нет ника в Telegram —
           напиши в комментариях к ленте или найди его в группе</div>`}
      ${me.can_manage && o.author_id !== me.id ? `
        <button class="btn-secondary danger-btn" data-do="delete" data-id="${o.id}">
          Убрать
        </button>` : ''}
    </div>
  </div>`;

async function helpScreen() {
  if (!canTalk) {
    return screen({
      title: 'Помощь в заданиях',
      body: emptyState('Раздел работает внутри Telegram', 'handHeart'),
    });
  }

  let board;
  try {
    board = await get(`/api/help?kind=${kind}`);
  } catch (err) {
    return screen({
      title: 'Помощь в заданиях',
      body: `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`,
    });
  }

  // Свой id приходит из /api/me — по нему и отличаем своё объявление от
  // чужого: у своего кнопки «решено» и «удалить», у чужого — «написать».
  const me = { id: account.id, can_manage: board.can_manage };

  const node = screen({
    title: 'Помощь в заданиях',
    subtitle: 'Найди старшекурсника или помоги сам',
    body: `
      <div class="segmented" id="side">
        <button class="segmented-item ${kind === 'need' ? 'active' : ''}"
                data-kind="need">Нужна помощь · ${board.need}</button>
        <button class="segmented-item ${kind === 'offer' ? 'active' : ''}"
                data-kind="offer">Могу помочь · ${board.offer}</button>
      </div>

      <div class="search-box" style="margin:12px 0">
        ${icon('search', 19, 'muted')}
        <input id="hq" type="search" placeholder="Предмет или тема" autocomplete="off">
      </div>

      <button class="btn-primary compose-btn" id="add">
        ${icon('edit', 18)} Разместить объявление
      </button>

      <div class="stack" id="hlist" style="margin-top:14px"></div>

      ${board.mine.length ? `
        <div class="section-head"><div class="section-title">Мои объявления</div></div>
        <div class="stack">${board.mine.map(o => card(o, me)).join('')}</div>`
    : ''}`,
  });

  const list = node.querySelector('#hlist');
  const draw = offers => {
    list.innerHTML = offers.length
      ? offers.map(o => card(o, me)).join('')
      : emptyState(kind === 'need'
        ? 'Никто пока не просил помощи'
        : 'Никто пока не предлагал помощь', 'handHeart');
  };
  draw(board.offers);

  node.querySelector('#side').addEventListener('click', e => {
    const b = e.target.closest('[data-kind]');
    if (!b || b.dataset.kind === kind) return;
    kind = b.dataset.kind;
    haptic('light');
    refresh();
  });

  let timer = null;
  node.querySelector('#hq').addEventListener('input', e => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    timer = setTimeout(async () => {
      try {
        const r = await get(`/api/help?kind=${kind}&q=${encodeURIComponent(q)}`);
        draw(r.offers);
      } catch (err) { toast(err.message); }
    }, 250);
  });

  node.querySelector('#add').addEventListener('click', () => composer(kind));

  node.addEventListener('click', async e => {
    const write = e.target.closest('[data-write]');
    if (write) return openLink(`https://t.me/${write.dataset.write}`);

    const act = e.target.closest('[data-do]');
    if (!act) return;
    const what = act.dataset.do;
    if (what === 'delete' && !await confirmDialog('Удалить объявление?')) return;
    try {
      await post(`/api/help/${act.dataset.id}/${what}`, {});
      hapticNotify('success');
      refresh();
    } catch (err) { toast(err.message); }
  });

  return node;
}

function composer(startKind) {
  let side = startKind;
  let price = 'free';

  sheet({
    title: 'Новое объявление',
    height: '72vh',
    body: `
      <div class="field-group">
        <div class="field-label">Что именно</div>
        <div class="segmented" id="ckind">
          <button class="segmented-item ${side === 'need' ? 'active' : ''}"
                  data-k="need">Нужна помощь</button>
          <button class="segmented-item ${side === 'offer' ? 'active' : ''}"
                  data-k="offer">Могу помочь</button>
        </div>
      </div>

      <div class="field-group">
        <div class="field-label">Предмет</div>
        <input class="field-input" id="subj" maxlength="80"
               placeholder="Например, матанализ">
      </div>

      <div class="field-group">
        <div class="field-label">Подробности — по желанию</div>
        <textarea class="field-input" id="text" rows="4" maxlength="600"
                  placeholder="С чем именно нужна помощь"></textarea>
      </div>

      <div class="field-group">
        <div class="field-label">Условия</div>
        <div class="segmented" id="cprice">
          <button class="segmented-item active" data-p="free">Бесплатно</button>
          <button class="segmented-item" data-p="deal">По договорённости</button>
        </div>
      </div>

      <div class="warn-note">
        ${icon('info', 16)}
        Твой ник в Telegram увидят все, кто откроет объявление — иначе с
        тобой не свяжутся. Закрыть его можно кнопкой «Вопрос решён».
      </div>

      <button class="btn-primary" id="send" style="margin-top:12px">
        Разместить
      </button>`,
    onMount(root, close) {
      root.querySelector('#ckind').addEventListener('click', e => {
        const b = e.target.closest('[data-k]');
        if (!b) return;
        side = b.dataset.k;
        root.querySelectorAll('#ckind .segmented-item')
          .forEach(x => x.classList.remove('active'));
        b.classList.add('active');
      });
      root.querySelector('#cprice').addEventListener('click', e => {
        const b = e.target.closest('[data-p]');
        if (!b) return;
        price = b.dataset.p;
        root.querySelectorAll('#cprice .segmented-item')
          .forEach(x => x.classList.remove('active'));
        b.classList.add('active');
      });

      root.querySelector('#send').addEventListener('click', async () => {
        const subject = root.querySelector('#subj').value.trim();
        if (!subject) return toast('Укажи предмет');
        const btn = root.querySelector('#send');
        btn.disabled = true;
        try {
          await post('/api/help', {
            kind: side, subject, price,
            text: root.querySelector('#text').value.trim(),
          });
          hapticNotify('success');
          close();
          toast('Объявление размещено');
          kind = side;
          refresh();
        } catch (err) {
          toast(err.message);
          btn.disabled = false;
        }
      });
    },
  });
}


return {'default': helpScreen};
})();

/* ==== js\screens\links.js ==== */
__mod['js/screens/links.js'] = (function () {
// Полезные ссылки: сервисы МИЭТ, учёба, студенческая жизнь, общежитие.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var emptyState = __mod['js/ui.js']['emptyState'];
var data = __mod['js/store.js']['data'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

const norm = s => String(s || '').toLowerCase().replace(/ё/g, 'е');

async function linksScreen() {
  const groups = data.links || [];
  const total = groups.reduce((n, g) => n + g.items.length, 0);

  const node = screen({
    title: 'Ссылки',
    subtitle: `${total} сервисов и разделов МИЭТ`,
    body: `
      <div class="search-box" style="margin-bottom:18px">
        ${icon('search', 19, 'muted')}
        <input id="lq" type="search" placeholder="Найти ссылку" autocomplete="off"
               enterkeyhint="search" spellcheck="false">
      </div>
      <div id="groups"></div>
      <div class="fab-note">Все ссылки ведут на официальные ресурсы МИЭТ.</div>`,
  });

  const box = node.querySelector('#groups');
  const input = node.querySelector('#lq');

  const row = it => listRow({
    ico: it.icon, title: it.title, sub: it.sub,
    chevron: true, id: it.url, cls: 'tap',
  });

  const draw = q => {
    const needle = norm(q);
    if (needle.length >= 2) {
      const found = groups.flatMap(g => g.items)
        .filter(it => norm(it.title).includes(needle) || norm(it.sub).includes(needle));
      box.innerHTML = found.length
        ? listCard(found.map(row))
        : emptyState(`Ничего не нашлось по «${q}»`, 'search');
      return;
    }
    box.innerHTML = groups.map(g => `
      <div class="section-head"><div class="section-title">${esc(g.title)}</div></div>
      ${listCard(g.items.map(row))}`).join('');
  };

  draw('');
  input.addEventListener('input', () => draw(input.value));

  node.addEventListener('click', e => {
    const r = e.target.closest('.list-row[data-id]');
    if (r) openLink(r.dataset.id);
  });

  return node;
}

return {'default': linksScreen};
})();

/* ==== js\screens\news.js ==== */
__mod['js/screens/news.js'] = (function () {
// Архив новостей МИЭТ и экран статьи.
//
// Это то, что собрано в data/app.json скриптами tools/ — снимок на момент
// сборки, с тегами и галереями. Живая лента (свежие новости и посты людей)
// живёт в screens/feed.js и приходит с сервера.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var lightbox = __mod['js/ui.js']['lightbox'];
var data = __mod['js/store.js']['data'];
var markRead = __mod['js/store.js']['markRead'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];
var newsCard = __mod['js/screens/common.js']['newsCard'];
var iconBtn = __mod['js/screens/common.js']['iconBtn'];

const key = t => String(t).toLowerCase().replace(/ё/g, 'е').trim();

/**
 * Список тегов по частоте. Сайт отдаёт один и тот же тег то с заглавной,
 * то со строчной («Наука» и «наука»), поэтому считаем без учёта регистра,
 * а показываем вариант с заглавной.
 */
function topTags(news, limit = 8) {
  const agg = new Map();
  for (const n of news) {
    for (const t of n.tags || []) {
      const k = key(t);
      const cur = agg.get(k) || { count: 0, label: t };
      cur.count++;
      if (/^[А-ЯЁA-Z]/.test(t) && !/^[А-ЯЁA-Z]/.test(cur.label)) cur.label = t;
      agg.set(k, cur);
    }
  }
  return [...agg.values()]
    .filter(v => v.count > 1)
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(v => v.label);
}

async function newsScreen() {
  const all = data.news || [];
  const tags = topTags(all);
  let active = 'all';

  const node = screen({
    title: 'Архив новостей',
    subtitle: `${all.length} публикаций, собранных с miet.ru`,
    actions: iconBtn('external', 'site'),
    body: `
      ${tags.length ? `<div class="pill-row" id="tags" style="margin-bottom:16px">
        <button class="pill active" data-tag="all">Все</button>
        ${tags.map(t => `<button class="pill" data-tag="${esc(t)}">${esc(t)}</button>`).join('')}
      </div>` : ''}
      <div class="stack" id="feed"></div>`,
  });

  const feed = node.querySelector('#feed');
  const draw = () => {
    const items = active === 'all'
      ? all
      : all.filter(n => (n.tags || []).some(t => key(t) === key(active)));
    feed.innerHTML = items.length
      ? items.map(newsCard).join('')
      : emptyState('По этому тегу пока пусто', 'inbox');
  };
  draw();

  node.querySelector('#tags')?.addEventListener('click', e => {
    const b = e.target.closest('[data-tag]');
    if (!b) return;
    active = b.dataset.tag;
    node.querySelectorAll('#tags .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    draw();
  });

  feed.addEventListener('click', e => {
    const c = e.target.closest('[data-news]');
    if (c) go('article', { id: c.dataset.news });
  });

  node.querySelector('[data-action="site"]').addEventListener('click', () =>
    openLink('https://www.miet.ru/news/'));

  return node;
}

/** Экран одной новости. */
async function articleScreen({ id }) {
  const n = (data.news || []).find(x => x.id === String(id));
  if (!n) return screen({ title: 'Новость', body: emptyState('Новость не найдена', 'helpCircle') });
  markRead(n.id);

  const paragraphs = (n.text || '')
    .split(/\n{2,}/)
    .map(p => p.trim())
    .filter(Boolean);

  const node = screen({
    body: `
      ${n.cover ? `<img class="article-cover" src="img/${esc(n.cover)}" alt="" decoding="async">` : ''}
      <div class="article-title">${esc(n.title)}</div>
      <div class="news-date" style="margin-bottom:14px">${esc(n.date)}</div>
      ${n.tags?.length ? `<div class="tag-row" style="margin-bottom:18px">
        ${n.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}
      </div>` : ''}
      ${paragraphs.length
        ? `<div class="article-text">${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}</div>`
        : `<div class="row-subtitle" style="margin-bottom:18px">
             Полный текст — на сайте университета.
           </div>`}
      ${n.gallery?.length ? `
        <div class="section-head"><div class="section-title">Фото</div></div>
        <div class="gallery">
          ${n.gallery.map(g => `<img src="img/${esc(g)}" data-full="img/${esc(g)}" alt="" loading="lazy" decoding="async">`).join('')}
        </div>` : ''}
      <div style="margin-top:22px">
        <button class="btn-primary" id="open">
          ${icon('external', 18)} Открыть на miet.ru
        </button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(n.url));
  node.addEventListener('click', e => {
    const img = e.target.closest('[data-full]');
    if (img) lightbox(img.dataset.full);
  });
  return node;
}

return {'default': newsScreen, 'articleScreen': articleScreen};
})();

/* ==== js\screens\profile.js ==== */
__mod['js/screens/profile.js'] = (function () {
// Профиль: группа, тема, поправка недели, избранное, обслуживание кеша.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var toast = __mod['js/ui.js']['toast'];
var sheet = __mod['js/ui.js']['sheet'];
var emptyState = __mod['js/ui.js']['emptyState'];
var data = __mod['js/store.js']['data'];
var settings = __mod['js/store.js']['settings'];
var save = __mod['js/store.js']['save'];
var applyTheme = __mod['js/store.js']['applyTheme'];
var resolveTheme = __mod['js/store.js']['resolveTheme'];
var BUILD = __mod['js/config.js']['BUILD'];
var fetchSchedule = __mod['js/schedule.js']['fetchSchedule'];
var weekOfCycle = __mod['js/schedule.js']['weekOfCycle'];
var go = __mod['js/router.js']['go'];
var refresh = __mod['js/router.js']['refresh'];
var tgUser = __mod['js/tg.js']['tgUser'];
var openLink = __mod['js/tg.js']['openLink'];
var syncChrome = __mod['js/tg.js']['syncChrome'];
var haptic = __mod['js/tg.js']['haptic'];
var confirmDialog = __mod['js/tg.js']['confirmDialog'];
var account = __mod['js/api.js']['account'];
var screen = __mod['js/screens/common.js']['screen'];
var pickGroup = __mod['js/screens/common.js']['pickGroup'];

async function profileScreen() {
  const user = tgUser();
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || 'Студент МИЭТ';
  const initials = (user?.first_name?.[0] || 'М') + (user?.last_name?.[0] || '');
  const favCount = settings.favorites.length;

  let weekLabel = '—';
  if (settings.group) {
    try {
      const s = await fetchSchedule(settings.group);
      weekLabel = `${weekOfCycle(new Date(), s.semestr, settings.weekShift) + 1}-я из 4`;
    } catch { weekLabel = 'нет данных'; }
  }

  const node = screen({
    body: `
      <div class="profile-head">
        ${user?.photo_url
        ? `<img class="avatar-lg" src="${esc(user.photo_url)}" alt="" decoding="async">`
        : `<div class="avatar-lg">${esc(initials)}</div>`}
        <div style="min-width:0">
          <div style="font-size:22px;font-weight:800;letter-spacing:-.02em">${esc(name)}</div>
          <div class="row-subtitle">${user?.username ? '@' + esc(user.username) : 'НИУ МИЭТ'}</div>
        </div>
      </div>

      ${account.can_stats ? `
        <div class="section-head" style="margin-top:0">
          <div class="section-title">Управление</div>
        </div>
        ${listCard([listRow({
    ico: 'shield',
    title: 'Админка',
    sub: account.is_admin ? 'Статистика, юзеры, роли' : 'Статистика и юзеры',
    chevron: true, id: 'admin', cls: 'tap',
  })])}` : ''}

      <div class="section-head" ${account.can_stats ? '' : 'style="margin-top:0"'}>
        <div class="section-title">Учёба</div>
      </div>
      ${listCard([
      listRow({ ico: 'users', title: 'Группа', value: settings.group || 'не выбрана', chevron: true, id: 'group', cls: 'tap' }),
      listRow({ ico: 'calendar', title: 'Текущая неделя', value: weekLabel, chevron: true, id: 'week', cls: 'tap' }),
      listRow({ ico: 'heart', title: 'Избранные кружки', value: String(favCount), chevron: true, id: 'fav', cls: 'tap' }),
    ])}

      <div class="section-head"><div class="section-title">Оформление</div></div>
      <div class="card" style="padding:14px 16px">
        <div class="field-label" style="margin-bottom:9px">Тема</div>
        <div class="segmented" id="theme">
          ${[['auto', 'Как в Telegram'], ['light', 'Светлая'], ['dark', 'Тёмная']]
      .map(([id, label]) => `<button class="segmented-item
        ${settings.theme === id ? 'active' : ''}" data-theme="${id}">${label}</button>`)
      .join('')}
        </div>
      </div>

      <div class="section-head"><div class="section-title">Университет</div></div>
      ${listCard([
      listRow({ ico: 'landmark', title: 'О МИЭТ', sub: 'История, факты, контакты', chevron: true, id: 'about', cls: 'tap' }),
      listRow({ ico: 'compass', title: 'Разделы кампуса', chevron: true, id: 'campus', cls: 'tap' }),
      listRow({ ico: 'graduate', title: 'Институты', chevron: true, id: 'institutes', cls: 'tap' }),
      listRow({ ico: 'link', title: 'Полезные ссылки', sub: 'ОРИОКС, кабинет, сервисы', chevron: true, id: 'links', cls: 'tap' }),
      listRow({ ico: 'globe', title: 'Сайт miet.ru', chevron: true, id: 'site', cls: 'tap' }),
      listRow({ ico: 'lifebuoy', title: 'Поддержка', sub: 'Написать автору приложения', chevron: true, id: 'support', cls: 'tap' }),
    ])}

      <div class="section-head"><div class="section-title">Данные</div></div>
      ${listCard([
      listRow({ ico: 'refresh', title: 'Обновить расписание', sub: 'Сбросить сохранённую копию', chevron: true, id: 'reload', cls: 'tap' }),
      listRow({ ico: 'trash', title: 'Сбросить настройки', sub: 'Группа, тема, избранное', chevron: true, id: 'reset', cls: 'tap' }),
    ])}

      <div class="fab-note">
        Расписание — miet.ru/schedule, обновляется при каждом открытии.<br>
        Новости и справочная информация собраны ${esc(data.meta?.generated || '')}.<br>
        Версия приложения ${esc(BUILD)}.
      </div>`,
  });

  node.querySelector('#theme').addEventListener('click', e => {
    const b = e.target.closest('[data-theme]');
    if (!b) return;
    const theme = b.dataset.theme;
    save({ theme });
    applyTheme(theme);
    syncChrome(resolveTheme(theme));
    haptic('light');
    node.querySelectorAll('#theme .segmented-item').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
  });

  node.addEventListener('click', async e => {
    const row = e.target.closest('.list-row[data-id]');
    if (!row) return;
    switch (row.dataset.id) {
      case 'admin': return go('admin');
      case 'group': return pickGroup(() => refresh());
      case 'week': return weekShiftSheet();
      case 'fav': return go('clubs');
      case 'about': return go('about');
      case 'campus': return go('campus');
      case 'institutes': return go('institutes');
      case 'links': return go('links');
      case 'support': return go('support');
      case 'site': return openLink('https://www.miet.ru');
      case 'reload': {
        if (!settings.group) return toast('Сначала выбери группу');
        try {
          await fetchSchedule(settings.group, { force: true });
          toast('Расписание обновлено');
        } catch (err) { toast(err.message); }
        return;
      }
      case 'reset': {
        if (await confirmDialog('Сбросить группу, тему и избранное?')) {
          Object.keys(localStorage)
            .filter(k => k.startsWith('miet-'))
            .forEach(k => localStorage.removeItem(k));
          location.reload();
        }
      }
    }
  });

  return node;
}

/**
 * Поправка недели. Цикл в МИЭТе четырёхнедельный, отсчёт ведём от начала
 * семестра — если у деканата счёт другой, здесь его можно сдвинуть.
 */
function weekShiftSheet() {
  sheet({
    title: 'Поправка недели',
    body: `
      <div class="row-subtitle" style="margin-bottom:14px;line-height:1.5">
        Неделя цикла считается от начала семестра. Если приложение показывает
        не ту неделю, что деканат, — сдвинь на нужное число.
      </div>
      <div class="pill-row" id="shift">
        ${[0, 1, 2, 3].map(s => `
          <button class="pill ${settings.weekShift === s ? 'active' : ''}" data-shift="${s}">
            ${s === 0 ? 'без сдвига' : `+${s}`}
          </button>`).join('')}
      </div>`,
    onMount(root, close) {
      root.querySelector('#shift').addEventListener('click', e => {
        const b = e.target.closest('[data-shift]');
        if (!b) return;
        save({ weekShift: +b.dataset.shift });
        haptic('medium');
        close();
        refresh();
      });
    },
  });
}

void emptyState;
void icon;

return {'default': profileScreen};
})();

/* ==== js\screens\schedule.js ==== */
__mod['js/screens/schedule.js'] = (function () {
// Расписание: неделя цикла → день → пары. Данные тянутся с miet.ru живьём.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var toast = __mod['js/ui.js']['toast'];
var art = __mod['js/art.js']['art'];
var artState = __mod['js/art.js']['artState'];
var settings = __mod['js/store.js']['settings'];
var save = __mod['js/store.js']['save'];
var fetchSchedule = __mod['js/schedule.js']['fetchSchedule'];
var weekOfCycle = __mod['js/schedule.js']['weekOfCycle'];
var slotsOf = __mod['js/schedule.js']['slotsOf'];
var dayCounts = __mod['js/schedule.js']['dayCounts'];
var mondayOf = __mod['js/schedule.js']['mondayOf'];
var shortSemestr = __mod['js/schedule.js']['shortSemestr'];
var gapsOf = __mod['js/schedule.js']['gapsOf'];
var humanGap = __mod['js/schedule.js']['humanGap'];
var DAY_SHORT = __mod['js/schedule.js']['DAY_SHORT'];
var DAY_NAMES = __mod['js/schedule.js']['DAY_NAMES'];
var refresh = __mod['js/router.js']['refresh'];
var haptic = __mod['js/tg.js']['haptic'];
var hapticSelect = __mod['js/tg.js']['hapticSelect'];
var screen = __mod['js/screens/common.js']['screen'];
var pickGroup = __mod['js/screens/common.js']['pickGroup'];
var iconBtn = __mod['js/screens/common.js']['iconBtn'];
var shortDate = __mod['js/screens/common.js']['shortDate'];

/**
 * Как звать преподавателя в строке.
 *
 * Приложение показывает короткое имя — на длинное в карточке нет места.
 * Но расписание приходит двумя путями: у miet.ru короткое лежит своим
 * полем, а из кеша бота может прийти только полное. Пусто — не рисуем
 * ничего, это лучше пустой строки со значком.
 */
const teacherOf = l =>
  (l && (l.teacherShort || l.teacher)) || '';

/** Преподаватель и аудитория — одна строка на подгруппу. */
const whereLine = e => `
  <div class="lesson-meta">
    ${e.room ? `<span>${icon('door', 14)} ${esc(e.room)}</span>` : ''}
    ${teacherOf(e) ? `<span>${icon('teacher', 14)} ${esc(teacherOf(e))}</span>` : ''}
  </div>`;

/**
 * Карточка пары. Принимает слот из slotsOf, но переживает и одиночную
 * запись — на главной и в поиске приходит именно она.
 */
// Какой значок какому виду занятия. Лекция — доска, лабораторная —
// колба, практика и семинар — карандаш: это не украшение, а второй
// признак рядом с цветом, потому что цвет различают не все.
const KIND_ICONS = { lek: 'board', lab: 'flask', pr: 'pencil' };

/**
 * Полоска окна между парами.
 *
 * Стоит между строками, а не внутри: окно — это не занятие, и делать
 * из него такую же карточку значило бы прятать его среди пар. Здесь
 * важно ровно две вещи — сколько ждать и до которого часа.
 */
const gapRow = g => `
  <div class="gap-row">
    <span class="gap-line"></span>
    <span class="gap-text">
      ${icon('clock', 13)}
      Окно ${esc(humanGap(g.minutes) || `${g.pairs} пары`)}
      ${g.from && g.to ? `· ${esc(g.from)}–${esc(g.to)}` : ''}
    </span>
    <span class="gap-line"></span>
  </div>`;

/** Пары дня вперемешку с окнами — в том порядке, в каком их проживают. */
function dayRows(slots, now = null) {
  const gaps = gapsOf(slots);
  return slots.map((l, i) => {
    const after = gaps.find(g => g.after === l.pair);
    return lessonRow(l, now) + (after && i + 1 < slots.length ? gapRow(after) : '');
  }).join('');
}

function lessonRow(l, now = null, showState = true) {
  const entries = l.entries || [l];
  const sameSubject = l.sameSubject ?? true;

  let state = '';
  if (now && showState) {
    const mins = now.getHours() * 60 + now.getMinutes();
    const to = m => { const [h, x] = m.split(':').map(Number); return h * 60 + x; };
    if (mins >= to(l.from) && mins < to(l.to)) state = 'live';
    else if (mins >= to(l.to)) state = 'past';
  }

  const body = sameSubject
    ? `<div class="lesson-name">${esc(l.subject || entries[0].subject)}</div>
       ${entries.map(whereLine).join('')}`
    : entries.map(e => `
        <div class="lesson-name">${esc(e.subject)}</div>
        ${whereLine(e)}`).join('');

  const kind = sameSubject ? l.kind || entries[0].kind : '';
  const kindCls = sameSubject ? l.kindCls || entries[0].kindCls : 'oth';
  const flags = (sameSubject ? l.flags : null) || [];

  return `
    <div class="lesson ${state}">
      <div class="lesson-time">
        <div class="lesson-from">${esc(l.from)}</div>
        <div class="lesson-to">${esc(l.to)}</div>
      </div>
      <div class="lesson-body">
        ${body}
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
          ${kind ? `<span class="kind ${kindCls}">
            ${icon(KIND_ICONS[kindCls] || 'clipboard', 12)}${esc(kind)}
          </span>` : ''}
          ${flags.map(f => `<span class="kind oth">${esc(f)}</span>`).join('')}
          ${entries.length > 1 ? '<span class="kind oth">подгруппы</span>' : ''}
          ${state === 'live' ? '<span class="live-badge"><i></i>идёт сейчас</span>' : ''}
        </div>
      </div>
    </div>`;
}

async function scheduleScreen(params = {}) {
  if (!settings.group) {
    const node = screen({
      title: 'Расписание',
      subtitle: 'Сначала выбери группу',
      body: `<div class="card has-art" style="padding:20px">
          <div class="has-art-body">
            <div class="row-subtitle" style="margin-bottom:16px">
              Расписание берётся напрямую с miet.ru и обновляется автоматически.
            </div>
            <button class="btn-primary" id="pick">Выбрать группу</button>
          </div>
          ${art('group', 84, 'art-aside')}
        </div>`,
    });
    node.querySelector('#pick').addEventListener('click', () => pickGroup(() => refresh()));
    return node;
  }

  const now = new Date();
  let sched;
  try {
    sched = await fetchSchedule(settings.group, { force: params.force });
  } catch (err) {
    const node = screen({
      title: 'Расписание',
      subtitle: settings.group,
      body: `<div class="card">
        ${artState('offline', 'Расписание не загрузилось', err.message)}
        <button class="btn-primary" id="retry" style="margin:0 20px 20px">
          Попробовать снова
        </button>
      </div>`,
    });
    node.querySelector('#retry').addEventListener('click', () => refresh());
    return node;
  }

  const curWeek = weekOfCycle(now, sched.semestr, settings.weekShift);
  const todayDay = ((now.getDay() + 6) % 7) + 1;
  let week = params.week ?? curWeek;
  let day = params.day ?? (todayDay <= 6 ? todayDay : 1);

  const node = screen({
    title: 'Расписание',
    subtitle: `${settings.group} · ${shortSemestr(sched.semestr)}`,
    actions: iconBtn('refresh', 'reload') + iconBtn('sliders', 'group'),
    body: `
      <div class="pill-row" id="weeks">
        ${[0, 1, 2, 3].map(w => `
          <button class="pill ${w === week ? 'active' : ''}" data-week="${w}">
            ${w + 1}-я неделя${w === curWeek ? ' · сейчас' : ''}
          </button>`).join('')}
      </div>
      <div class="week-strip" id="days"></div>
      <div id="stale"></div>
      <div id="list" class="stack" style="margin-top:16px"></div>`,
  });

  const daysEl = node.querySelector('#days');
  const listEl = node.querySelector('#list');
  const staleEl = node.querySelector('#stale');

  /** Честная плашка: показываем сохранённое, потому что сайт молчит. */
  function drawStale() {
    staleEl.innerHTML = sched.stale
      ? `<div class="warn-note" style="margin-top:12px">
           ${icon('info', 16)}
           Показываю сохранённое расписание: ${esc(sched.why || 'сайт МИЭТ не ответил')}.
         </div>`
      : '';
  }

  function drawDays() {
    const counts = dayCounts(sched, week);
    const mon = mondayOf(now);
    mon.setDate(mon.getDate() + (week - curWeek) * 7);
    daysEl.innerHTML = [1, 2, 3, 4, 5, 6].map(d => {
      const date = new Date(mon);
      date.setDate(mon.getDate() + d - 1);
      const isToday = date.toDateString() === now.toDateString();
      return `
        <button class="week-day ${d === day ? 'active' : ''} ${isToday ? 'today' : ''}"
                data-day="${d}">
          <span class="week-day-name">${DAY_SHORT[d]}</span>
          <span class="week-day-num">${date.getDate()}</span>
          <span class="dot ${counts[d] ? '' : 'empty'}"></span>
        </button>`;
    }).join('');
  }

  function drawList() {
    const items = slotsOf(sched, week, day);
    const mon = mondayOf(now);
    mon.setDate(mon.getDate() + (week - curWeek) * 7 + day - 1);
    const isToday = mon.toDateString() === now.toDateString();
    listEl.innerHTML = `
      <div class="section-head" style="margin:0 2px 2px">
        <div class="section-title">${DAY_NAMES[day]}</div>
        <span class="muted" style="font-size:14px;font-weight:600">${shortDate(mon)}</span>
      </div>
      ${items.length
        ? dayRows(items, isToday ? now : null)
        : `<div class="card">${day === 6
          ? artState('rest', 'Суббота свободна', 'Пар в этот день нет')
          : artState('free', 'В этот день пар нет',
            'Свободно — можно закрыть хвосты или выдохнуть')}</div>`}
      ${items.length ? `<div class="fab-note">
          ${items.length} ${plural(items.length, 'пара', 'пары', 'пар')} ·
          источник: miet.ru${sched.cached ? ' · из кеша' : ''}
        </div>` : ''}`;
  }

  drawDays();
  drawList();
  drawStale();

  node.querySelector('#weeks').addEventListener('click', e => {
    const b = e.target.closest('[data-week]');
    if (!b) return;
    week = +b.dataset.week;
    hapticSelect();
    node.querySelectorAll('#weeks .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    drawDays();
    drawList();
  });

  daysEl.addEventListener('click', e => {
    const b = e.target.closest('[data-day]');
    if (!b) return;
    day = +b.dataset.day;
    hapticSelect();
    daysEl.querySelectorAll('.week-day').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    drawList();
  });

  node.querySelector('[data-action="group"]').addEventListener('click', () =>
    pickGroup(() => refresh()));

  node.querySelector('[data-action="reload"]').addEventListener('click', async e => {
    const btn = e.currentTarget;
    haptic('medium');
    btn.innerHTML = '<div class="spinner"></div>';
    try {
      sched = await fetchSchedule(settings.group, { force: true });
      drawDays();
      drawList();
      drawStale();
      toast(sched.stale ? 'Сайт МИЭТ молчит — расписание прежнее'
        : 'Расписание обновлено');
    } catch (err) {
      toast(err.message);
    }
    btn.innerHTML = icon('refresh', 19);
  });

  void save;
  return node;
}

function plural(n, one, few, many) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}



return {'default': scheduleScreen, 'teacherOf': teacherOf, 'gapRow': gapRow, 'dayRows': dayRows, 'lessonRow': lessonRow, 'plural': plural};
})();

/* ==== js\screens\search.js ==== */
__mod['js/screens/search.js'] = (function () {
// Общий поиск: новости, кружки, институты, разделы кампуса и группы.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var emptyState = __mod['js/ui.js']['emptyState'];
var data = __mod['js/store.js']['data'];
var settings = __mod['js/store.js']['settings'];
var save = __mod['js/store.js']['save'];
var go = __mod['js/router.js']['go'];
var switchTab = __mod['js/router.js']['switchTab'];
var haptic = __mod['js/tg.js']['haptic'];
var screen = __mod['js/screens/common.js']['screen'];

const norm = s => String(s || '').toLowerCase().replace(/ё/g, 'е');

function collect(q) {
  const n = norm(q);
  if (n.length < 2) return [];
  const hit = t => norm(t).includes(n);
  const out = [];

  for (const g of data.groups || []) {
    if (norm(g).replace(/\s+/g, '').includes(n.replace(/\s+/g, ''))) {
      out.push({ kind: 'group', ico: 'users', title: g, sub: 'Учебная группа', id: g });
    }
    if (out.length > 6) break;
  }
  for (const c of data.clubs || []) {
    if (hit(c.title) || hit(c.tagline) || hit(c.cat)) {
      out.push({ kind: 'club', ico: c.icon || 'sparkles', title: c.title, sub: c.cat, id: c.id });
    }
  }
  for (const c of data.campus || []) {
    if (hit(c.title) || hit(c.sub)) {
      out.push({ kind: 'campusItem', ico: c.icon, title: c.title, sub: c.sub, id: c.id });
    }
  }
  for (const i of data.institutes || []) {
    if (hit(i.name) || hit(i.short) || hit(i.director) || (i.departments || []).some(hit)) {
      out.push({ kind: 'institute', ico: 'graduate', title: i.name, sub: i.short, id: i.id });
    }
  }
  for (const a of data.news || []) {
    if (hit(a.title) || hit(a.text)) {
      out.push({ kind: 'article', ico: 'news', title: a.title, sub: a.date, id: a.id });
    }
    if (out.length > 60) break;
  }
  return out.slice(0, 60);
}

async function searchScreen() {
  const node = screen({
    title: 'Поиск',
    subtitle: 'Пары, кружки, институты, новости',
    body: `
      <div class="search-box" style="margin-bottom:16px">
        ${icon('search', 19, 'muted')}
        <input id="q" type="search" placeholder="Что ищем?" autocomplete="off"
               enterkeyhint="search" spellcheck="false">
      </div>
      <div id="res"></div>`,
  });

  const input = node.querySelector('#q');
  const res = node.querySelector('#res');

  const HINTS = ['ПИН-31', 'хор', 'бассейн', 'столовая', 'общежитие', 'стипендия'];
  const idle = () => `
    <div class="section-head" style="margin-top:4px"><div class="section-title">Попробуй</div></div>
    <div class="pill-row">
      ${HINTS.map(h => `<button class="pill" data-hint="${esc(h)}">${esc(h)}</button>`).join('')}
    </div>`;

  const draw = () => {
    const q = input.value.trim();
    if (q.length < 2) { res.innerHTML = idle(); return; }
    const items = collect(q);
    res.innerHTML = items.length
      ? listCard(items.map((r, i) => listRow({
        ico: r.ico, title: r.title, sub: r.sub,
        chevron: true, id: String(i), cls: 'tap',
      })))
      : emptyState(`Ничего не нашлось по «${q}»`, 'search');
    res.dataset.payload = JSON.stringify(items);
  };

  draw();
  input.addEventListener('input', draw);
  setTimeout(() => input.focus({ preventScroll: true }), 150);

  node.addEventListener('click', e => {
    const hint = e.target.closest('[data-hint]');
    if (hint) { input.value = hint.dataset.hint; draw(); return; }
    const row = e.target.closest('.list-row[data-id]');
    if (!row) return;
    const items = JSON.parse(res.dataset.payload || '[]');
    const r = items[+row.dataset.id];
    if (!r) return;
    haptic('light');
    if (r.kind === 'group') {
      save({ group: r.id });
      return switchTab('schedule');
    }
    go(r.kind, { id: r.id });
  });

  void settings;
  return node;
}

return {'default': searchScreen};
})();

/* ==== js\screens\support.js ==== */
__mod['js/screens/support.js'] = (function () {
// Поддержка: кто сделал приложение и куда писать, если что-то не так.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var data = __mod['js/store.js']['data'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

const OWNER = 'xxxddsm';

async function supportScreen() {
  const meta = data.meta || {};

  const node = screen({
    title: 'Поддержка',
    subtitle: 'Приложение сделано студентом для студентов',
    small: true,
    body: `
      <div class="card owner-card">
        <div class="owner-avatar">${icon('user', 30)}</div>
        <div style="min-width:0">
          <div class="owner-name">@${esc(OWNER)}</div>
          <div class="row-subtitle">Автор и поддержка</div>
        </div>
      </div>

      <div style="margin-top:14px">
        <button class="btn-primary" id="write">
          ${icon('messageCircle', 18)} Написать в Telegram
        </button>
      </div>

      <div class="section-head"><div class="section-title">Что писать</div></div>
      ${listCard([
      listRow({ ico: 'info', title: 'Расписание показывает не то', sub: 'Проверь поправку недели в профиле — цикл мог сдвинуться' }),
      listRow({ ico: 'refresh', title: 'Данные устарели', sub: 'Новости и разделы обновляются вручную, напомни' }),
      listRow({ ico: 'sparkles', title: 'Хочется новой функции', sub: 'Предлагай — приложение делается для вас' }),
    ])}

      <div class="section-head"><div class="section-title">Об источниках</div></div>
      ${listCard([
      listRow({ ico: 'calendar', title: 'Расписание', sub: 'Тянется с miet.ru при каждом открытии', value: 'живое' }),
      listRow({ ico: 'news', title: 'Новости и разделы', sub: `Собраны ${esc(meta.generated || '—')}` }),
      listRow({ ico: 'globe', title: 'Источник', sub: 'miet.ru', chevron: true, id: 'site', cls: 'tap' }),
    ])}

      <div class="fab-note">
        Приложение неофициальное. Вся информация и фотографии принадлежат
        НИУ МИЭТ.
      </div>`,
  });

  const write = () => openLink(`https://t.me/${OWNER}`);
  node.querySelector('#write').addEventListener('click', write);
  node.addEventListener('click', e => {
    const row = e.target.closest('.list-row[data-id="site"]');
    if (row) openLink('https://www.miet.ru');
  });
  return node;
}

return {'default': supportScreen, 'OWNER': OWNER};
})();

/* ==== js\screens\tasks.js ==== */
__mod['js/screens/tasks.js'] = (function () {
// Задания из ОРИОКС — список дел, а не выгрузка данных.
//
// Первая версия показывала всё подряд, сгруппированное по предметам, и
// была нечитаемой: у студента шесть-восемь дисциплин по пять-десять
// контрольных мероприятий в каждой, то есть полсотни строк, в которых
// не видно главного — что делать в ближайшие дни.
//
// Поэтому здесь один список, отсортированный по сроку и разбитый на
// «просрочено / эта неделя / следующая / потом». Предмет крупно, тип
// задания мелко: человек ищет глазами «Матанализ», а не «ДЗ №2».
// Сданное убрано вниз и свёрнуто — оно уже не дело.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var toast = __mod['js/ui.js']['toast'];
var sheet = __mod['js/ui.js']['sheet'];
var toggle = __mod['js/ui.js']['toggle'];
var get = __mod['js/api.js']['get'];
var post = __mod['js/api.js']['post'];
var account = __mod['js/api.js']['account'];
var canTalk = __mod['js/api.js']['canTalk'];
var settings = __mod['js/store.js']['settings'];
var fetchSchedule = __mod['js/schedule.js']['fetchSchedule'];
var semesterStart = __mod['js/schedule.js']['semesterStart'];
var mondayOf = __mod['js/schedule.js']['mondayOf'];
var weekOfCycle = __mod['js/schedule.js']['weekOfCycle'];
var refresh = __mod['js/router.js']['refresh'];
var hapticNotify = __mod['js/tg.js']['hapticNotify'];
var haptic = __mod['js/tg.js']['haptic'];
var confirmDialog = __mod['js/tg.js']['confirmDialog'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

const WEEKDAYS = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];

/**
 * Понедельник учебной недели N.
 *
 * Считать от самой даты начала семестра нельзя: 1 сентября бывает
 * вторником, и тогда вторая неделя съезжала на день вперёд — ОРИОКС
 * показывал вторую, а приложение считало её концом четырнадцатое.
 * Недели везде начинаются с понедельника, и здесь тоже.
 */
function weekMonday(start, week) {
  if (!start || !week) return null;
  const d = mondayOf(start);
  d.setDate(d.getDate() + (week - 1) * 7);
  return d;
}

/** Конец учебной недели N — крайний срок, если пары найти не удалось. */
function dueDate(start, week) {
  const d = weekMonday(start, week);
  if (d) d.setDate(d.getDate() + 6);
  return d;
}

// Тип мероприятия ОРИОКС → тип пары в расписании. Лабораторную сдают
// на лабораторной, контрольную пишут на практике: это не догадка, а
// то, как устроено занятие.
const KIND_TO_CLASS = [
  [/лаборатор/i, 'lab'],
  [/практич|контрольн|коллоквиум|тест|семинар|деловая игра|кейс/i, 'pr'],
  [/лекц/i, 'lek'],
];

/** Слова названия, по которым предмет узнаётся в другом источнике. */
function subjectKey(name) {
  return String(name || '').toLowerCase()
    .replace(/[«»"'()]/g, ' ')
    .split(/[\s.,;:—–-]+/)
    .filter(w => w.length >= 5)
    .slice(0, 2)
    .join(' ');
}

/**
 * День пары, на которой это мероприятие сдают.
 *
 * ОРИОКС знает только номер недели, а человек живёт днями: «лаба на
 * второй неделе» и «лаба завтра» — про одно и то же, но понятно
 * второе. Ищем в расписании пару нужного предмета и вида на этой
 * неделе; если их несколько, берём последнюю — крайний срок.
 */
function lessonDay(sched, start, event, discipline, shift) {
  if (!sched || !start || !event.week) return null;
  const monday = weekMonday(start, event.week);
  if (!monday) return null;

  const cycle = weekOfCycle(monday, sched.semestr, shift);
  const want = (KIND_TO_CLASS.find(([re]) => re.test(event.type || '')) || [])[1];
  const key = subjectKey(discipline);
  if (!key) return null;

  const sameWeek = (sched.lessons || []).filter(
    l => l.week === cycle && subjectKey(l.subject) === key);
  const exact = want ? sameWeek.filter(l => l.kindCls === want) : [];
  // Копия перед сортировкой: pop() опустошал сам массив, и «нашли
  // именно лабораторную» превращалось в «нашли хоть что-нибудь»
  // ровно в тот момент, когда это проверялось.
  const found = (exact.length ? exact : sameWeek).slice()
    .sort((a, b) => a.day - b.day || a.pair - b.pair).pop();
  if (!found) return null;

  const d = new Date(monday.getTime());
  d.setDate(d.getDate() + found.day - 1);
  return { date: d, lesson: found, exact: exact.length > 0 };
}

const humanDate = d =>
  d ? `${d.getDate()} ${MONTHS[d.getMonth()]}, ${WEEKDAYS[d.getDay()]}` : '';

function daysLeft(due) {
  if (!due) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((due - today) / 86400000);
}

/**
 * Название задания у ОРИОКС бывает кодом: «dz.1», «КТ.2», иногда пустым.
 * Человеку нужен смысл, поэтому главным делаем тип («Домашнее задание»),
 * а код показываем рядом — по нему задание ищут уже в самом ОРИОКС.
 */
function titleOf(t) {
  const name = (t.name || '').trim();
  const type = (t.type || '').trim();
  const looksLikeCode = name.length <= 6 || /^[a-zA-Z.\d\s]+$/.test(name);
  if (type && looksLikeCode) return { main: type, note: name };
  return { main: name || type || 'Задание', note: type === name ? '' : type };
}

// Виды работ для фильтра. Ключ — то, что ищем в типе мероприятия;
// у ОРИОКС названия длинные («Большое домашнее задание»), поэтому
// сравниваем по куску, а не целиком.
const KINDS = [
  { id: 'all', label: 'Всё', match: () => true },
  { id: 'hw', label: 'Домашние', match: t => /домашн|индивидуал|расчет|расчёт|курсов|реферат/i.test(t) },
  { id: 'lab', label: 'Лабы', match: t => /лаборатор/i.test(t) },
  { id: 'test', label: 'Контрольные', match: t => /контрольн|тест|коллоквиум|самостоятельн/i.test(t) },
];

// Группы по срочности. Порядок здесь же задаёт порядок на экране.
const BUCKETS = [
  { id: 'late', title: 'Просрочено', note: 'Срок уже прошёл' },
  { id: 'now', title: 'На этой неделе', note: '' },
  { id: 'next', title: 'На следующей неделе', note: '' },
  { id: 'later', title: 'Потом', note: '' },
  { id: 'nodate', title: 'Без срока', note: 'ОРИОКС не указал неделю' },
];

function bucketOf(left) {
  if (left === null) return 'nodate';
  if (left < 0) return 'late';
  if (left <= 7) return 'now';
  if (left <= 14) return 'next';
  return 'later';
}

function leftLabel(left) {
  if (left === null) return '';
  if (left < 0) return `${-left} дн назад`;
  if (left === 0) return 'сегодня';
  if (left === 1) return 'завтра';
  if (left < 7) return `через ${left} дн`;
  return `через ${Math.round(left / 7)} нед`;
}

const taskRow = t => `
  <div class="todo ${t.bucket}">
    <div class="todo-main">
      <div class="todo-subject">${esc(t.subject)}</div>
      <div class="todo-what">
        ${esc(t.title.main)}${t.title.note ? ` · ${esc(t.title.note)}` : ''}
      </div>
      ${t.materials && t.materials.length ? `
        <button class="todo-files" data-files="${t.idx}">
          ${icon('fileText', 14)}
          ${t.materials.length === 1 ? 'Файл задания'
            : `Файлов: ${t.materials.length}`}
        </button>` : ''}
    </div>
    <div class="todo-side">
      <div class="todo-when">${esc(t.due ? humanDate(t.due) : `${t.week || '?'} нед`)}</div>
      <div class="todo-left">
        ${esc(leftLabel(t.left))}${t.max_grade ? ` · ${t.max_grade} б.` : ''}
      </div>
      ${t.lesson ? `<div class="todo-lesson">
        ${esc(t.lesson.from || '')}${t.lesson.room ? ` · ${esc(t.lesson.room)}` : ''}
      </div>` : ''}
    </div>
  </div>`;

// Значок предмета. Читать название дисциплины целиком в списке никто
// не будет — глаз цепляется за цвет и форму, и уже по ним объявление
// находится среди других.
const SUBJECT_ICONS = [
  [/физик|механик|термодинам/i, 'atom', 4],
  [/матем|анализ|алгебр|геометр/i, 'sigma', 0],
  [/информат|программ|вычислит/i, 'code', 5],
  [/истори|философ|культур|право/i, 'landmark', 3],
  [/язык|английск|лингв/i, 'languages', 2],
  [/физическ.*культур|спорт/i, 'medal', 1],
  [/командн|коммуникац|психолог/i, 'users', 2],
  [/хими|биолог/i, 'microscope', 1],
  [/эконом|менеджмент|финанс/i, 'wallet', 3],
];

function subjectLook(name) {
  for (const [re, glyph, tone] of SUBJECT_ICONS) {
    if (re.test(name || '')) return { glyph, tone };
  }
  // Незнакомый предмет получает свой постоянный цвет, а не случайный:
  // при следующем открытии он должен выглядеть так же.
  let sum = 0;
  for (const ch of String(name || '')) sum = (sum + ch.charCodeAt(0)) % 997;
  return { glyph: 'bookOpen', tone: sum % 6 };
}

/** Дата ОРИОКС «03.09.2026 15:05» — в то, как о ней говорят вслух. */
function newsDate(raw) {
  const m = /^(\d{2})\.(\d{2})\.(\d{4})(?:\s+(\d{2}):(\d{2}))?/.exec(raw || '');
  if (!m) return { text: raw || '', fresh: false };
  const [, d, mo, y, hh, mm] = m;
  const when = new Date(+y, +mo - 1, +d, +(hh || 0), +(mm || 0));
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((today - new Date(+y, +mo - 1, +d)) / 86400000);
  const clock = hh ? `${hh}:${mm}` : '';
  if (days === 0) return { text: clock ? `сегодня, ${clock}` : 'сегодня', fresh: true };
  if (days === 1) return { text: 'вчера', fresh: true };
  if (days > 1 && days < 7) return { text: `${days} дн. назад`, fresh: days <= 2 };
  return { text: `${+d} ${MONTHS[+mo - 1]}`, fresh: false, when };
}

const newsRow = n => {
  const look = subjectLook(n.discipline);
  const date = newsDate(n.date);
  return `
  <button class="notice-card tone-${look.tone}" data-news="${esc(n.href)}">
    <div class="notice-badge">${icon(look.glyph, 20)}</div>
    <div class="notice-main">
      <div class="notice-top">
        <span class="notice-subject">
          ${esc(n.discipline || (n.course ? 'Дисциплина' : 'Институт'))}
        </span>
        ${date.fresh ? '<span class="notice-fresh">новое</span>' : ''}
        <span class="notice-date">${esc(date.text)}</span>
      </div>
      <div class="notice-title">${esc(n.title)}</div>
      ${n.preview ? `<div class="notice-preview">${esc(n.preview)}</div>` : ''}
      <div class="notice-foot">
        ${n.author ? `${icon('user', 13)}<span>${esc(n.author)}</span>` : ''}
        <span class="notice-open">Читать ${icon('chevronRight', 13)}</span>
      </div>
    </div>
  </button>`;
};

// Что за файл — видно по значку раньше, чем прочитано название: у
// преподавателей они называются «Федотова_ТА_КРиДК_СР1_Деловое письмо».
function fileLook(name, link) {
  const what = (name + ' ' + (link || '')).toLowerCase();
  if (/\.pdf(\?|$|%|\s)/.test(what)) return { glyph: 'fileText', label: 'PDF' };
  if (/\.docx?(\?|$|%|\s)/.test(what)) return { glyph: 'edit', label: 'DOC' };
  if (/\.xlsx?(\?|$|%|\s)/.test(what)) return { glyph: 'grid', label: 'Таблица' };
  if (/\.pptx?(\?|$|%|\s)/.test(what)) return { glyph: 'palette', label: 'Слайды' };
  if (/\.zip|\.rar|\.7z/.test(what)) return { glyph: 'folder', label: 'Архив' };
  if (/ссылк|http/.test(what)) return { glyph: 'link', label: 'Ссылка' };
  return { glyph: 'clipboard', label: '' };
}

const fileRow = f => {
  const look = fileLook(f.name, f.link);
  return `
  <button class="notice-card file-card" data-link="${esc(f.link)}">
    <div class="notice-badge">${icon(look.glyph, 19)}</div>
    <div class="notice-main">
      <div class="notice-title">${esc(f.name)}</div>
      <div class="notice-foot">
        <span>${esc(f.subject)}</span>
        ${look.label ? `<span class="file-kind">${esc(look.label)}</span>` : ''}
        <span class="notice-open">Открыть ${icon('external', 13)}</span>
      </div>
    </div>
  </button>`;
};

/**
 * Всё, что ОРИОКС знает о заданиях, — одним плоским списком со сроками.
 *
 * Предмет здесь часть строки, а не заголовок блока: задание нельзя
 * понять в отрыве от него, а группировка по дисциплинам давала полсотни
 * строк, в которых не видно главного — что делать в ближайшие дни.
 *
 * Живёт отдельно от экрана, потому что тот же список нужен главной: она
 * показывает из него три ближайших дела.
 */
function flatten(tasks, sched, start, shift) {
  const all = [];
  (tasks.disciplines || []).forEach(d => (d.events || []).forEach(e => {
    const at = lessonDay(sched, start, e, d.name, shift);
    const due = at ? at.date : dueDate(start, e.week);
    const left = daysLeft(due);
    all.push({
      ...e,
      idx: all.length,
      // Пара, на которой сдают: по ней и показываем день вместо
      // безликого «конца второй недели».
      lesson: at ? at.lesson : null,
      exactDay: !!(at && at.exact),
      subject: d.name,
      title: titleOf(e),
      due,
      left,
      bucket: bucketOf(left),
    });
  }));
  return all;
}

/**
 * Несданные задания, ближайшие сверху.
 *
 * Формальности (посещаемость, «порядок НБС») и события сессии сюда не
 * попадают: сдавать там нечего, а строк они дают больше трети.
 */
function pendingOf(all) {
  return all.filter(t => t.task && !t.done)
    .sort((a, b) => (a.left ?? 9999) - (b.left ?? 9999));
}

const doneRow = t => `
  <div class="todo done">
    <div class="todo-main">
      <div class="todo-subject">${esc(t.subject)}</div>
      <div class="todo-what">${esc(t.title.main)}</div>
    </div>
    <div class="todo-side">
      <div class="todo-grade">${t.grade} из ${t.max_grade}</div>
    </div>
  </div>`;

async function tasksScreen() {
  if (!canTalk) {
    return screen({
      title: 'Задания',
      body: emptyState('Раздел работает внутри Telegram', 'backpack'),
    });
  }

  let data;
  let news = [];
  // Доступ к сайту ОРИОКС — это не то же самое, что подключение: токен
  // может быть жив, а сессия сайта кончиться. Объявления и подписка на
  // них есть только при живой сессии.
  let web = false;
  try {
    const both = await Promise.all([
      get('/api/orioks', { timeout: 25000 }),
      // Объявления не должны мешать заданиям: не пришли — экран
      // работает дальше, просто без них.
      get('/api/orioks/news', { timeout: 25000 }).catch(() => ({ news: [] })),
    ]);
    data = both[0];
    news = both[1].news || [];
    web = both[1].web === true;
  } catch (err) {
    return screen({
      title: 'Задания',
      body: `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`,
    });
  }

  if (!data.linked) return notLinked();
  if (data.error) return linkedButBroken(data.error);

  // Расписание нужно целиком, а не только ради начала семестра: по нему
  // находится день пары, на которой задание и сдают.
  let start = null;
  let sched = null;
  if (settings.group) {
    try {
      sched = await fetchSchedule(settings.group);
      start = semesterStart(sched.semestr);
    } catch { /* без дат покажем недели */ }
  }

  const all = flatten(data.tasks, sched, start, settings.weekShift);

  // ОРИОКС отдаёт вперемешку с заданиями формальности: посещаемость,
  // «порядок НБС», семестровый план. Сдавать там нечего, а строк они
  // дают больше трети — из-за них список и был нечитаемым.
  const tasks = all.filter(t => t.task);
  const session = all.filter(t => t.session)
    .sort((a, b) => (a.left ?? 9999) - (b.left ?? 9999));
  const formal = all.filter(t => !t.task && !t.session);

  const pending = pendingOf(all);
  const done = tasks.filter(t => t.done);

  const soon = pending.filter(t => t.left !== null && t.left <= 7).length;

  // Вложения со всех мероприятий разом, включая те, что висят не на
  // заданиях: у живого студента половина файлов лежит именно там.
  const files = [];
  all.forEach(t => (t.materials || []).forEach(
    m => files.push({ ...m, subject: t.subject, event: t.title.main })));

  const node = screen({
    title: 'Задания',
    subtitle: start ? 'Сроки, баллы и файлы из ОРИОКС'
      : 'Выбери группу в профиле, чтобы видеть даты',
    actions: `<button class="icon-btn" data-action="orioks">${icon('external', 19)}</button>`,
    body: `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${pending.length}</div>
          <div class="kpi-label">Не сдано</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${soon}</div>
          <div class="kpi-label">На этой неделе</div>
        </div>
      </div>

      ${news.length ? `
        <div class="section-head">
          <div class="section-title with-icon">
            ${icon('megaphone', 17)} Что задали
          </div>
          ${news.length > 3 ? `<button class="section-link"
            id="toggle-news">${news.length}</button>` : ''}
        </div>
        <p class="section-note">
          Объявления преподавателей — то, что они пишут к занятию.
        </p>
        <div class="notice-list">
          ${news.slice(0, 3).map(newsRow).join('')}
        </div>
        <div class="notice-list" id="news-rest" hidden>
          ${news.slice(3).map(newsRow).join('')}
        </div>` : ''}

      ${web ? `
        <div class="list-card watch-card">
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">Сообщать о новом</div>
              <div class="row-subtitle">
                Бот напишет в личку, когда преподаватель выложит
                объявление. Проверяет днём, раз в полтора часа.
              </div>
            </div>
            ${toggle(data.notify !== false, 'watch')}
          </div>
        </div>` : ''}

      <div class="pill-row" id="kinds" style="margin:14px 0 4px">
        ${KINDS.map(k => `
          <button class="pill ${k.id === 'all' ? 'active' : ''}"
                  data-kind="${k.id}">${esc(k.label)}</button>`).join('')}
      </div>

      <div id="task-list"></div>

      ${session.length ? `
        <div class="section-head"><div class="section-title with-icon">${icon('award', 17)} Сессия</div></div>
        <p class="section-note">Экзамены и зачёты — ими семестр кончается.</p>
        <div class="list-card">${session.map(taskRow).join('')}</div>` : ''}

      ${done.length ? `
        <div class="section-head">
          <div class="section-title">Сдано</div>
          <button class="section-link" id="toggle-done">${done.length}</button>
        </div>
        <div class="list-card" id="done-list" hidden>
          ${done.map(doneRow).join('')}
        </div>` : ''}

      ${files.length ? `
        <div class="section-head">
          <div class="section-title with-icon">${icon('folder', 17)} Файлы от преподавателей</div>
          <button class="section-link" id="toggle-files">${files.length}</button>
        </div>
        <p class="section-note">
          Методички, условия и бланки. Это всё, что ОРИОКС знает о
          заданиях сверх их названий.
        </p>
        <div class="notice-list" id="files-list" hidden>
          ${files.map(fileRow).join('')}
        </div>` : ''}

      ${formal.length ? `
        <div class="section-head">
          <div class="section-title">Не задания</div>
          <button class="section-link" id="toggle-formal">${formal.length}</button>
        </div>
        <p class="section-note">
          Посещаемость, активность и записи для порядка — сдавать нечего.
        </p>
        <div class="list-card" id="formal-list" hidden>
          ${formal.map(t => `
            <div class="todo done">
              <div class="todo-main">
                <div class="todo-subject">${esc(t.subject)}</div>
                <div class="todo-what">${esc(t.title.main)}</div>
              </div>
              <div class="todo-side">
                <div class="todo-left">${t.max_grade ? `до ${t.max_grade} б.` : '—'}</div>
              </div>
            </div>`).join('')}
        </div>` : ''}

      <div class="section-head"><div class="section-title">По предметам</div></div>
      <div class="list-card">
        ${data.tasks.disciplines.map(d => {
      const left = d.events.filter(e => e.task && !e.done).length;
      return `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(d.name)}</div>
              <div class="row-subtitle">
                ${d.current_grade ?? 0} из ${d.max_grade ?? 0} б.
                ${d.control_form ? ` · ${esc(d.control_form)}` : ''}
              </div>
            </div>
            <div class="list-row-value ${left ? '' : 'muted'}">
              ${left ? `${left} ост.` : 'всё'}
            </div>
          </div>`;
    }).join('')}
      </div>

      <button class="btn-secondary danger-btn" id="unlink" style="margin-top:14px">
        Отключить ОРИОКС
      </button>
      <div class="fab-note">
        Текста задания в ОРИОКС нет вовсе — ни в приложении, ни на сайте.
        Есть файлы, которые выложил преподаватель: они собраны здесь и
        открываются в ОРИОКС.
      </div>`,
  });

  // Список перерисовывается на месте: фильтр по виду работы не должен
  // перезагружать экран и терять прокрутку.
  const listBox = node.querySelector('#task-list');
  let kind = KINDS[0];
  const unfolded = new Set();

  const drawList = () => {
    const items = pending.filter(t => kind.match(`${t.type} ${t.name}`));
    const groups = BUCKETS
      .map(b => ({ ...b, items: items.filter(t => t.bucket === b.id) }))
      .filter(b => b.items.length);

    if (!groups.length) {
      listBox.innerHTML = emptyState(
        kind.id === 'all' ? 'Всё сдано — свободен' : 'Таких работ нет', 'check');
      return;
    }
    listBox.innerHTML = groups.map(g => {
      // «Потом» у студента — полсотни записей: развёрнутым этот блок и
      // превращал экран в простыню. Сворачиваем, оставляя счётчик.
      const folded = g.id === 'later' && g.items.length > 6
        && !unfolded.has(g.id);
      return `
        <div class="section-head">
          <div class="section-title">${esc(g.title)}</div>
          ${folded ? `<button class="section-link" data-unfold="${g.id}">
            ${g.items.length}</button>` : ''}
        </div>
        ${g.note ? `<p class="section-note">${esc(g.note)}</p>` : ''}
        <div class="list-card">
          ${(folded ? g.items.slice(0, 3) : g.items).map(taskRow).join('')}
        </div>`;
    }).join('');
  };
  drawList();

  node.querySelector('#kinds').addEventListener('click', e => {
    const b = e.target.closest('[data-kind]');
    if (!b) return;
    kind = KINDS.find(k => k.id === b.dataset.kind);
    node.querySelectorAll('#kinds .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    drawList();
  });

  listBox.addEventListener('click', e => {
    const filesBtn = e.target.closest('[data-files]');
    if (filesBtn) return filesSheet(all[+filesBtn.dataset.files]);
    const more = e.target.closest('[data-unfold]');
    if (!more) return;
    // Перерисовываем список целиком вместо поиска соседних узлов: так
    // разметка может меняться, не ломая обработчик.
    unfolded.add(more.dataset.unfold);
    drawList();
  });

  const toggler = (btnId, listId, count) =>
    node.querySelector(btnId)?.addEventListener('click', e => {
      const list = node.querySelector(listId);
      list.hidden = !list.hidden;
      e.target.textContent = list.hidden ? count : 'скрыть';
    });
  toggler('#toggle-done', '#done-list', done.length);
  toggler('#toggle-files', '#files-list', files.length);
  toggler('#toggle-news', '#news-rest', news.length);
  node.addEventListener('click', e => {
    const row = e.target.closest('[data-news]');
    if (row) newsSheet(row.dataset.news, news);
  });
  node.querySelector('#files-list')?.addEventListener('click', e => {
    const row = e.target.closest('[data-link]');
    if (row) openLink(row.dataset.link);
  });
  toggler('#toggle-formal', '#formal-list', formal.length);
  node.querySelector('[data-toggle="watch"]')?.addEventListener('click', async e => {
    const t = e.currentTarget;
    const on = !t.classList.contains('on');
    // Переключаем сразу, а откатываем при отказе: подписка — мелочь, и
    // ждать ответа сервера, глядя на неподвижный тумблер, незачем.
    t.classList.toggle('on', on);
    haptic('light');
    try {
      await post('/api/orioks/notify', { on });
      data.notify = on;
    } catch (err) {
      toast(err.message);
      t.classList.toggle('on', !on);
    }
  });
  node.querySelector('[data-action="orioks"]').addEventListener('click',
    () => openLink('https://orioks.miet.ru/main/login'));
  node.querySelector('#unlink').addEventListener('click', async () => {
    if (!await confirmDialog('Отключить ОРИОКС? Токен будет отозван.')) return;
    try {
      await post('/api/orioks/unlink', {});
      account.orioks = false;
      hapticNotify('success');
      refresh();
    } catch (err) { toast(err.message); }
  });

  return node;
}

// ─────────────── подключение ───────────────

function notLinked() {
  const node = screen({
    title: 'Задания',
    subtitle: 'Что задали, что сдать и файлы из ОРИОКС',
    body: `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:8px">Подключи ОРИОКС</div>
        <div class="row-subtitle" style="line-height:1.55">
          Приложение соберёт все контрольные мероприятия семестра в один
          список: что сдавать, к какому числу и сколько это даёт баллов.
          Ближайшее — сверху, просроченное — отдельно.
        </div>
      </div>

      <div class="warn-note" style="margin-top:12px">
        ${icon('shield', 16)}
        Пароль не сохраняется. ОРИОКС меняет его на токен — в базе лежит
        только токен, и отозвать его можно кнопкой «Отключить».
      </div>

      <button class="btn-primary" id="link" style="margin-top:14px">
        Подключить
      </button>`,
  });

  node.querySelector('#link').addEventListener('click', linkSheet);
  return node;
}

function linkedButBroken(message) {
  const node = screen({
    title: 'Задания',
    body: `
      <div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:6px">ОРИОКС не ответил</div>
        <div class="row-subtitle" style="margin-bottom:14px">${esc(message)}</div>
        <button class="btn-primary" id="relink">Подключить заново</button>
      </div>`,
  });
  node.querySelector('#relink').addEventListener('click', linkSheet);
  return node;
}

function linkSheet() {
  sheet({
    title: 'Вход в ОРИОКС',
    body: `
      <div class="field-group">
        <div class="field-label">Логин</div>
        <input class="field-input" id="olog" autocomplete="username"
               autocapitalize="none" spellcheck="false"
               placeholder="тот же, что при входе в ОРИОКС">
      </div>
      <div class="field-group">
        <div class="field-label">Пароль</div>
        <input class="field-input" id="opass" type="password"
               autocomplete="current-password">
      </div>
      <div class="warn-note">
        ${icon('shield', 16)}
        Пароль уходит в ОРИОКС за доступом к твоему кабинету и нигде не
        сохраняется — ни в боте, ни в телефоне. Доступ нужен, чтобы
        показать текст заданий: в кратком виде ОРИОКС отдаёт только их
        названия. Отключишь — доступ стирается сразу.
      </div>
      <button class="btn-primary" id="ogo" style="margin-top:12px">Войти</button>`,
    onMount(root, close) {
      const go = root.querySelector('#ogo');
      go.addEventListener('click', async () => {
        const login = root.querySelector('#olog').value.trim();
        const password = root.querySelector('#opass').value;
        if (!login || !password) return toast('Введи логин и пароль');
        go.disabled = true;
        go.textContent = 'Подключаю…';
        try {
          await post('/api/orioks/link', { login, password }, { timeout: 45000 });
          account.orioks = true;
          hapticNotify('success');
          close();
          refresh();
        } catch (err) {
          toast(err.message);
          go.disabled = false;
          go.textContent = 'Войти';
        }
      });
    },
  });
}


/**
 * Файлы одного задания.
 *
 * Открываются в ОРИОКС, а не скачиваются сюда: ссылка живёт под
 * сессией института, и подменять её собственным хранилищем значило бы
 * копировать чужие материалы неизвестно куда.
 */
function filesSheet(task) {
  const items = task.materials || [];
  sheet({
    title: task.title.main,
    body: `
      <div class="notice-head tone-${subjectLook(task.subject).tone}">
        <div class="notice-badge">
          ${icon(subjectLook(task.subject).glyph, 22)}
        </div>
        <div class="notice-head-text">
          <div class="notice-subject">${esc(task.subject)}</div>
          <div class="notice-head-meta">
            ${icon('clipboard', 13)}
            <span>${esc(task.title.main)}</span>
          </div>
        </div>
      </div>
      <div class="notice-list">
        ${items.map((m, i) => {
          const look = fileLook(m.name, m.link);
          return `
          <button class="notice-card file-card" data-open="${i}">
            <div class="notice-badge">${icon(look.glyph, 19)}</div>
            <div class="notice-main">
              <div class="notice-title">${esc(m.name)}</div>
              <div class="notice-foot">
                ${m.kind ? `<span>${esc(m.kind)}</span>` : ''}
                ${look.label
                  ? `<span class="file-kind">${esc(look.label)}</span>` : ''}
                <span class="notice-open">Открыть ${icon('external', 13)}</span>
              </div>
            </div>
          </button>`;
        }).join('')}
      </div>
      <div class="fab-note">
        Откроется в ОРИОКС. Если попросит войти — это обычный вход,
        приложение тут ни при чём.
      </div>`,
    onMount(root) {
      root.addEventListener('click', e => {
        const row = e.target.closest('[data-open]');
        if (row) openLink(items[+row.dataset.open].link);
      });
    },
  });
}


/**
 * Объявление преподавателя целиком.
 *
 * Текст тянется отдельным запросом, а не вместе со списком: объявлений
 * бывает два десятка, а читают обычно одно, и качать все ради этого —
 * лишние секунды на каждом открытии экрана.
 */
async function newsSheet(href, list) {
  const known = (list || []).find(n => n.href === href) || {};
  const look = subjectLook(known.discipline);
  const date = newsDate(known.date);

  sheet({
    title: known.title || 'Объявление',
    body: `
      <div class="notice-head tone-${look.tone}">
        <div class="notice-badge">${icon(look.glyph, 22)}</div>
        <div class="notice-head-text">
          <div class="notice-subject">
            ${esc(known.discipline || 'Объявление')}
          </div>
          <div class="notice-head-meta">
            ${known.author ? `${icon('user', 13)}
              <span>${esc(known.author)}</span>` : ''}
            ${date.text ? `${icon('clock', 13)}
              <span>${esc(date.text)}</span>` : ''}
          </div>
        </div>
      </div>
      <div class="notice-body" id="notice-body">
        <div class="skeleton notice-skeleton"></div>
        <div class="skeleton notice-skeleton"></div>
        <div class="skeleton notice-skeleton short"></div>
      </div>`,
    onMount(root) {
      const box = root.querySelector('#notice-body');
      post('/api/orioks/news', { item: href }, { timeout: 25000 })
        .then(r => {
          const it = r.item || {};
          if (!it.text) {
            box.innerHTML = emptyState(
              r.error || 'ОРИОКС не отдал текст объявления', 'info');
            return;
          }
          box.innerHTML = it.text.split('\n').filter(Boolean)
            .map(line => NUMBERED.test(line)
              ? `<p class="notice-item">${linkify(line)}</p>`
              : `<p>${linkify(line)}</p>`).join('');
        })
        .catch(err => { box.innerHTML = emptyState(err.message, 'info'); });

      box.addEventListener('click', e => {
        const a = e.target.closest('a[data-url]');
        if (!a) return;
        e.preventDefault();
        openLink(a.dataset.url);
      });
    },
  });
}



/**
 * Текст со ссылками: преподаватели дают в объявлениях литературу
 * ссылками, и оставлять их непрожимаемой строкой — значит заставлять
 * переписывать адрес руками.
 *
 * Экранируем по кускам, а не целиком: экранированный текст уже нельзя
 * разбирать регулярным выражением, не рискуя склеить разметку.
 */
function linkify(text) {
  const parts = String(text).split(/(https?:\/\/[^\s<>"']+)/g);
  return parts.map((part, i) => {
    if (i % 2 === 0) return esc(part);
    const shown = part.length > 48 ? part.slice(0, 45) + '…' : part;
    return `<a href="#" data-url="${esc(part)}">${esc(shown)}</a>`;
  }).join('');
}


// Строка списка внутри объявления: «1.», «2)», «А)», «·». Преподаватели
// пишут задания перечнем, и сплошным текстом он читается вдвое хуже.
const NUMBERED = /^\s*(?:[0-9]{1,2}\s*[.)]|[А-Яа-яA-Za-z]\s*\)|[·•\-–])\s+/;

return {'default': tasksScreen, 'weekMonday': weekMonday, 'subjectKey': subjectKey, 'lessonDay': lessonDay, 'subjectLook': subjectLook, 'newsDate': newsDate, 'fileLook': fileLook, 'flatten': flatten, 'pendingOf': pendingOf, 'linkify': linkify, 'NUMBERED': NUMBERED};
})();

/* ==== js\screens\teachers.js ==== */
__mod['js/screens/teachers.js'] = (function () {
// Преподаватели и аудитории: поиск по расписанию всего университета.
//
// miet.ru отвечает только на вопрос «что у группы», поэтому «где сейчас
// Иванов» и «что идёт в 3105» собирает сервер (bot/directory.py) — раз в
// сутки обходит все группы и складывает плоский индекс. Здесь только
// показ найденного.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var get = __mod['js/api.js']['get'];
var canTalk = __mod['js/api.js']['canTalk'];
var go = __mod['js/router.js']['go'];
var settings = __mod['js/store.js']['settings'];
var screen = __mod['js/screens/common.js']['screen'];
var DAY_NAMES = __mod['js/schedule.js']['DAY_NAMES'];

const KIND_NAMES = { lek: 'лекция', pr: 'практика', lab: 'лаборатор.', oth: '' };

/** Пара в списке: время, предмет, где и с кем. */
const slotRow = (s, showTeacher) => `
  <div class="lesson">
    <div class="lesson-time">
      <div class="lesson-from">${esc(s.from || '')}</div>
      <div class="lesson-to">${esc(s.to || '')}</div>
    </div>
    <div class="lesson-body">
      <div class="lesson-name">${esc(s.subject || 'Занятие')}</div>
      <div class="lesson-meta">
        ${s.kind && KIND_NAMES[s.kind]
    ? `<span class="kind ${esc(s.kind)}">${KIND_NAMES[s.kind]}</span>` : ''}
        ${showTeacher && s.teacher
    ? `<span>${icon('teacher', 14)} ${esc(s.teacher)}</span>` : ''}
        ${s.room ? `<span>${icon('door', 14)} ${esc(s.room)}</span>` : ''}
        <span>${icon('users', 14)} ${esc(s.groups.join(', '))}</span>
      </div>
    </div>
  </div>`;

/**
 * Пары, разложенные по неделям цикла и дням. Плоский список из сорока
 * занятий читать невозможно, а «неделя 2, среда» — уже ответ.
 */
function timetable(slots, showTeacher) {
  const weeks = [[], [], [], []];
  slots.forEach(s => weeks[s.week % 4]?.push(s));
  return weeks.map((week, i) => {
    if (!week.length) return '';
    const days = {};
    week.forEach(s => (days[s.day] = days[s.day] || []).push(s));
    return `
      <div class="section-head"><div class="section-title">${i + 1}-я неделя</div></div>
      ${Object.keys(days).sort().map(d => `
        <div class="day-block">
          <div class="day-name">${esc(DAY_NAMES[d] || 'День ' + d)}</div>
          <div class="stack">${days[d].map(s => slotRow(s, showTeacher)).join('')}</div>
        </div>`).join('')}`;
  }).join('');
}

// ─────────────── список ───────────────

async function directoryScreen({ mode = 'teachers' } = {}) {
  const rooms = mode === 'rooms';

  if (!canTalk) {
    return screen({
      title: rooms ? 'Аудитории' : 'Преподаватели',
      body: emptyState('Справочник работает внутри Telegram', 'teacher'),
    });
  }

  const node = screen({
    title: rooms ? 'Аудитории' : 'Преподаватели',
    subtitle: rooms ? 'Что и когда идёт в кабинете'
      : 'Кто ведёт, где и с какими группами',
    body: `
      <div class="search-box" style="margin-bottom:12px">
        ${icon('search', 19, 'muted')}
        <input id="dq" type="search" autocomplete="off" spellcheck="false"
               placeholder="${rooms ? 'Например, 3105' : 'Фамилия преподавателя'}">
      </div>
      <div id="dlist"><div class="skeleton" style="height:140px"></div></div>
      <div class="fab-note" id="dnote"></div>`,
  });

  const list = node.querySelector('#dlist');
  const note = node.querySelector('#dnote');

  const draw = async q => {
    try {
      const r = await get(`/api/directory/${rooms ? 'rooms' : 'teachers'}`
        + `?q=${encodeURIComponent(q)}`);
      const items = rooms ? r.rooms : r.teachers;
      list.innerHTML = items.length
        ? `<div class="list-card">${items.map(x => `
            <div class="list-row tap" data-name="${esc(x.name)}">
              <div class="icon-tile">${icon(rooms ? 'door' : 'teacher', 19)}</div>
              <div class="list-row-body">
                <div class="row-title">${esc(x.name)}</div>
                <div class="row-subtitle">
                  ${x.lessons} ${plural(x.lessons, 'пара', 'пары', 'пар')} в цикле${
  rooms ? '' : ` · ${x.groups} ${plural(x.groups, 'группа', 'группы', 'групп')}`}
                </div>
              </div>
              <span class="chevron">${icon('chevronRight', 18)}</span>
            </div>`).join('')}</div>`
        : emptyState(q ? 'Ничего не нашлось' : 'Справочник ещё собирается', 'search');
      note.innerHTML = r.meta?.built_at
        ? `По расписанию ${esc(r.meta.semestr || '')} · обновлено ${esc(when(r.meta.built_at))}`
        : 'Справочник собирается — обычно это занимает несколько минут после запуска бота.';
    } catch (err) {
      list.innerHTML = `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`;
    }
  };

  draw('');

  let timer = null;
  node.querySelector('#dq').addEventListener('input', e => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    timer = setTimeout(() => draw(q), 250);
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-name]');
    if (row) go(rooms ? 'room' : 'teacher', { name: row.dataset.name });
  });

  return node;
}

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

/** Когда собран индекс — «сегодня» понятнее, чем «2026-09-07 03:00». */
function when(ts) {
  const d = new Date(String(ts).replace(' ', 'T') + 'Z');
  const hours = Math.floor((Date.now() - d.getTime()) / 3600000);
  if (hours < 1) return 'только что';
  if (hours < 24) return `${hours} ч назад`;
  return d.toLocaleDateString('ru-RU');
}

// ─────────────── карточка ───────────────

async function teacherScreen({ name }) {
  return card(name, false);
}

async function roomScreen({ name }) {
  return card(name, true);
}

async function card(name, rooms) {
  let found;
  try {
    found = await get(`/api/directory/${rooms ? 'room' : 'teacher'}`
      + `?name=${encodeURIComponent(name)}`);
  } catch (err) {
    return screen({ title: name, body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const mine = settings.group
    ? found.slots.filter(s => s.groups.includes(settings.group))
    : [];

  return screen({
    title: name,
    subtitle: rooms
      ? `${found.slots.length} ${plural(found.slots.length, 'пара', 'пары', 'пар')} в цикле`
      : found.subjects.slice(0, 3).join(' · '),
    body: `
      <div class="kpi-grid">
        ${kpiTile(found.slots.length, 'Пар в цикле')}
        ${rooms
    ? kpiTile(found.teachers.length, 'Преподавателей')
    : kpiTile(found.groups.length, 'Групп')}
      </div>

      ${mine.length ? `
        <div class="section-head"><div class="section-title">У твоей группы</div></div>
        <p class="section-note">${esc(settings.group)} — ${mine.length}
          ${plural(mine.length, 'пара', 'пары', 'пар')} в цикле</p>
        <div class="stack">${mine.map(s => slotRow(s, !rooms)).join('')}</div>` : ''}

      ${!rooms && found.rooms.length ? `
        <div class="section-head"><div class="section-title">Аудитории</div></div>
        <div class="chip-row">${found.rooms.map(r =>
      `<span class="chip">${esc(r)}</span>`).join('')}</div>` : ''}

      ${rooms && found.teachers.length ? `
        <div class="section-head"><div class="section-title">Кто ведёт</div></div>
        <div class="chip-row">${found.teachers.map(t =>
      `<span class="chip">${esc(t)}</span>`).join('')}</div>` : ''}

      <div class="section-head"><div class="section-title">Всё расписание</div></div>
      ${timetable(found.slots, !rooms)}`,
  });
}

const kpiTile = (n, label) =>
  `<div class="kpi-tile"><div class="kpi-number">${n}</div>
   <div class="kpi-label">${esc(label)}</div></div>`;

return {'default': directoryScreen, 'teacherScreen': teacherScreen, 'roomScreen': roomScreen};
})();

/* ==== js\screens\tools.js ==== */
__mod['js/screens/tools.js'] = (function () {
// Два счётных инструмента: баллы БРС и конвертер величин.
//
// Оба считают на месте и без сети. Оценки из ОРИОКС сюда не тянутся —
// доступа к чужому личному кабинету у приложения нет и быть не должно;
// баллы человек вводит сам, глядя в ОРИОКС, а приложение отвечает на
// вопрос, ради которого туда и лезут: сколько осталось набрать.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

// ─────────────── баллы ───────────────

// Шкала МИЭТ: 100 баллов за семестр, из них экзамен — отдельная часть.
// Пороги взяты из общей практики БРС и подписаны как ориентир: у разных
// дисциплин вес контрольных точек свой, и выдавать это за точный расчёт
// нельзя.
const GRADES = [
  { from: 86, label: 'Отлично', tone: 'success' },
  { from: 69, label: 'Хорошо', tone: 'primary' },
  { from: 50, label: 'Удовлетворительно', tone: 'warning' },
  { from: 0, label: 'Не сдано', tone: 'danger' },
];

const gradeOf = n => GRADES.find(g => n >= g.from);

async function scoreScreen() {
  const node = screen({
    title: 'Баллы и БРС',
    subtitle: 'Посчитать, сколько осталось набрать',
    body: `
      <div class="card" style="padding:16px">
        <div class="field-label" style="margin-bottom:10px">
          Баллы за контрольные точки
        </div>
        <div id="kts" class="stack"></div>
        <button class="btn-secondary" id="add" style="margin-top:10px">
          Добавить точку
        </button>
      </div>

      <div class="card" style="padding:16px;margin-top:12px">
        <div class="field-label" style="margin-bottom:8px">
          Сколько даёт экзамен или зачёт
        </div>
        <input class="field-input" id="exam" type="number" inputmode="numeric"
               value="30" min="0" max="100">
        <div class="row-subtitle" style="margin-top:6px">
          В МИЭТе это обычно 30 из 100, но у каждой дисциплины свой вес —
          посмотри в ОРИОКС.
        </div>
      </div>

      <div id="out" style="margin-top:14px"></div>

      <button class="btn-primary" id="orioks" style="margin-top:14px">
        ${icon('external', 17)} Открыть ОРИОКС
      </button>
      <div class="fab-note">
        Приложение не знает твои настоящие баллы: доступа к личному кабинету
        у него нет. Введи то, что видишь в ОРИОКС, — и оно посчитает остаток.
      </div>`,
  });

  const kts = node.querySelector('#kts');
  const out = node.querySelector('#out');

  const row = (i, value = '') => `
    <div class="kt-row" data-kt="${i}">
      <span class="kt-label">КТ${i + 1}</span>
      <input class="field-input" type="number" inputmode="numeric"
             placeholder="баллы" value="${value}" min="0" max="100">
      <button class="kt-drop" data-drop="${i}">${icon('x', 16)}</button>
    </div>`;

  let count = 3;
  const render = () => {
    const values = [...kts.querySelectorAll('input')].map(i => i.value);
    kts.innerHTML = Array.from({ length: count },
      (_, i) => row(i, values[i] ?? '')).join('');
    recount();
  };

  function recount() {
    const got = [...kts.querySelectorAll('input')]
      .map(i => Number(i.value) || 0)
      .reduce((a, b) => a + b, 0);
    const exam = Number(node.querySelector('#exam').value) || 0;
    const max = got + exam;
    const grade = gradeOf(got);

    // Сколько нужно на экзамене до каждой ступени — это и есть ответ,
    // ради которого считают: «мне хватит тройки или надо стараться».
    const need = GRADES.slice(0, 3).map(g => ({
      label: g.label,
      need: Math.max(0, g.from - got),
      real: g.from - got <= exam,
    }));

    out.innerHTML = `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${got}</div>
          <div class="kpi-label">Набрано сейчас</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${max}</div>
          <div class="kpi-label">Максимум с экзаменом</div>
        </div>
      </div>
      <div class="card" style="padding:16px;margin-top:12px">
        <div class="row-title" style="color:var(--${grade.tone})">
          Сейчас: ${esc(grade.label)}
        </div>
        <div class="stack" style="margin-top:12px">
          ${need.map(n => `
            <div class="need-row ${n.real ? '' : 'unreal'}">
              <span>${esc(n.label)}</span>
              <b>${n.need === 0 ? 'уже есть'
    : n.real ? `нужно ещё ${n.need}` : 'уже не набрать'}</b>
            </div>`).join('')}
        </div>
      </div>`;
  }

  render();

  kts.addEventListener('input', recount);
  node.querySelector('#exam').addEventListener('input', recount);
  node.querySelector('#add').addEventListener('click', () => {
    if (count < 8) { count++; render(); }
  });
  kts.addEventListener('click', e => {
    const drop = e.target.closest('[data-drop]');
    if (drop && count > 1) { count--; render(); }
  });
  node.querySelector('#orioks').addEventListener('click',
    () => openLink('https://orioks.miet.ru/main/login'));

  return node;
}

// ─────────────── конвертер ───────────────

// Всё через коэффициент к базовой единице: так добавление величины —
// одна строка, а не новая формула перевода в каждую сторону.
const UNITS = {
  Длина: { m: 1, км: 1000, см: 0.01, мм: 0.001, мкм: 1e-6, нм: 1e-9,
    дюйм: 0.0254, фут: 0.3048 },
  Масса: { кг: 1, г: 0.001, мг: 1e-6, т: 1000, фунт: 0.45359237 },
  Время: { с: 1, мс: 0.001, мкс: 1e-6, мин: 60, ч: 3600, сут: 86400 },
  Информация: { Б: 1, КБ: 1024, МБ: 1024 ** 2, ГБ: 1024 ** 3, ТБ: 1024 ** 4,
    бит: 0.125 },
  Энергия: { Дж: 1, кДж: 1000, кВт·ч: 3.6e6, эВ: 1.602176634e-19,
    кал: 4.184 },
  Давление: { Па: 1, кПа: 1000, МПа: 1e6, бар: 1e5, атм: 101325,
    'мм рт. ст.': 133.322 },
  Напряжение: { В: 1, мВ: 0.001, мкВ: 1e-6, кВ: 1000 },
  Сопротивление: { Ом: 1, мОм: 0.001, кОм: 1000, МОм: 1e6 },
  Ёмкость: { Ф: 1, мкФ: 1e-6, нФ: 1e-9, пФ: 1e-12 },
  Частота: { Гц: 1, кГц: 1000, МГц: 1e6, ГГц: 1e9 },
};

// Константы, которые в электронике спрашивают чаще всего. Значения — по
// системе СИ 2019 года, где часть из них определена точно.
const CONSTANTS = [
  ['Заряд электрона', 'e', '1,602176634·10⁻¹⁹ Кл'],
  ['Постоянная Планка', 'h', '6,62607015·10⁻³⁴ Дж·с'],
  ['Постоянная Больцмана', 'k', '1,380649·10⁻²³ Дж/К'],
  ['Скорость света', 'c', '299 792 458 м/с'],
  ['Число Авогадро', 'Nₐ', '6,02214076·10²³ 1/моль'],
  ['Тепловой потенциал при 300 K', 'kT/e', '≈ 25,85 мВ'],
  ['Диэлектрическая проницаемость кремния', 'ε(Si)', '≈ 11,7'],
  ['Ширина запрещённой зоны кремния', 'Eg(Si)', '≈ 1,12 эВ при 300 K'],
];

async function convertScreen() {
  let kind = 'Длина';

  const node = screen({
    title: 'Конвертер',
    subtitle: 'Единицы, которые нужны на парах',
    body: `
      <div class="pill-row" id="kinds">
        ${Object.keys(UNITS).map(k => `
          <button class="pill ${k === kind ? 'active' : ''}" data-kind="${esc(k)}">
            ${esc(k)}
          </button>`).join('')}
      </div>

      <div class="card" style="padding:16px;margin-top:14px">
        <div class="convert-row">
          <input class="field-input" id="val" type="number" inputmode="decimal" value="1">
          <select class="field-input" id="from"></select>
        </div>
        <div class="convert-eq">${icon('shuffle', 18)}</div>
        <div class="convert-row">
          <input class="field-input" id="res" readonly>
          <select class="field-input" id="to"></select>
        </div>
      </div>

      <div id="all" class="list-card" style="margin-top:12px"></div>

      <div class="section-head"><div class="section-title">Константы</div></div>
      <p class="section-note">Те, что чаще всего нужны в задачах по электронике.</p>
      <div class="list-card">
        ${CONSTANTS.map(([name, sign, value]) => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(name)}</div>
              <div class="row-subtitle">${esc(sign)}</div>
            </div>
            <div class="list-row-value tnum">${esc(value)}</div>
          </div>`).join('')}
      </div>`,
  });

  const val = node.querySelector('#val');
  const from = node.querySelector('#from');
  const to = node.querySelector('#to');
  const res = node.querySelector('#res');
  const all = node.querySelector('#all');

  const fillUnits = () => {
    const names = Object.keys(UNITS[kind]);
    const options = names.map(u => `<option>${esc(u)}</option>`).join('');
    from.innerHTML = options;
    to.innerHTML = options;
    from.value = names[0];
    to.value = names[1] || names[0];
    recount();
  };

  function pretty(n) {
    if (!isFinite(n)) return '—';
    if (n !== 0 && (Math.abs(n) < 1e-4 || Math.abs(n) >= 1e9)) {
      return n.toExponential(4).replace('e', '·10^');
    }
    // Округляем до разумного: у конвертера нет задачи показать
    // шестнадцать знаков после запятой.
    return String(Math.round(n * 1e6) / 1e6);
  }

  function recount() {
    const table = UNITS[kind];
    const base = (Number(val.value) || 0) * table[from.value];
    res.value = pretty(base / table[to.value]);
    all.innerHTML = Object.keys(table).map(u => `
      <div class="list-row">
        <div class="list-row-body"><div class="row-title">${esc(u)}</div></div>
        <div class="list-row-value tnum">${esc(pretty(base / table[u]))}</div>
      </div>`).join('');
  }

  fillUnits();

  node.querySelector('#kinds').addEventListener('click', e => {
    const b = e.target.closest('[data-kind]');
    if (!b) return;
    kind = b.dataset.kind;
    node.querySelectorAll('#kinds .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    fillUnits();
  });

  [val, from, to].forEach(el => el.addEventListener('input', recount));
  return node;
}

return {'scoreScreen': scoreScreen, 'convertScreen': convertScreen};
})();

/* ==== js\screens\useful.js ==== */
__mod['js/screens/useful.js'] = (function () {
// «Полезное» — оглавление всего, что не расписание и не лента.
//
// Плитки, а не список: у карточки есть место на подпись, и по ней видно,
// что внутри, без открытия. Порядок задан не алфавитом, а частотой
// вопросов первокурсника: сначала «кто ведёт и где», потом «сколько у меня
// баллов», и только потом справочное.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var data = __mod['js/store.js']['data'];
var account = __mod['js/api.js']['account'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];
var iconBtn = __mod['js/screens/common.js']['iconBtn'];

/**
 * Разделы. tone — цвет плитки: одинаковые все были бы неразличимы, а
 * пёстрые превратили бы экран в новогоднюю ёлку, поэтому оттенков пять и
 * они закреплены за смыслом: учёба синяя, деньги и жильё тёплые,
 * справочное зелёное, своё — фиолетовое.
 */
const SECTIONS = [
  {
    title: 'Учёба',
    note: 'То, что спрашивают чаще всего',
    tiles: [
      { id: 'tasks', ico: 'backpack', tone: 'blue', title: 'Задания',
        sub: 'Что задали, сроки и файлы из ОРИОКС' },
      { id: 'teachers', ico: 'teacher', tone: 'blue', title: 'Преподаватели',
        sub: 'Кто, где и когда ведёт' },
      { id: 'rooms', ico: 'door', tone: 'blue', title: 'Аудитории',
        sub: 'Что идёт в кабинете' },
      { id: 'score', ico: 'chart', tone: 'blue', title: 'Баллы и БРС',
        sub: 'Сколько нужно набрать' },
      { id: 'dates', ico: 'calendar', tone: 'blue', title: 'Ключевые даты',
        sub: 'Семестр, недели, сессия' },
      { id: 'help', ico: 'handshake', tone: 'blue', title: 'Помощь в заданиях',
        sub: 'Найти старшекурсника' },
    ],
  },
  {
    title: 'Университет',
    tiles: [
      { id: 'institutes', ico: 'graduate', tone: 'green', title: 'Институты',
        sub: d => `${(d.institutes || []).length} подразделений` },
      { id: 'clubs', ico: 'sparkles', tone: 'green', title: 'Кружки',
        sub: d => `${(d.clubs || []).length} сообществ` },
      { id: 'campus', ico: 'compass', tone: 'green', title: 'Кампус',
        sub: 'Библиотека, столовая, спорт' },
      { id: 'contacts', ico: 'phone', tone: 'green', title: 'Контакты',
        sub: 'Телефоны и почта' },
      { id: 'chats', ico: 'messageCircle', tone: 'green', title: 'Чаты',
        sub: 'Каналы и сообщества' },
      { id: 'curators', ico: 'handHeart', tone: 'green', title: 'Кураторы',
        sub: 'Кто ведёт первый курс' },
      { id: 'dorm', ico: 'homes', tone: 'warm', title: 'Общежития',
        sub: 'Адреса и заселение' },
      { id: 'money', ico: 'wallet', tone: 'warm', title: 'Деньги',
        sub: 'Стипендии и поддержка' },
    ],
  },
  {
    title: 'Инструменты',
    tiles: [
      { id: 'convert', ico: 'sliders', tone: 'violet', title: 'Конвертер',
        sub: 'Единицы и величины' },
      { id: 'glossary', ico: 'bookOpen', tone: 'violet', title: 'Словарь',
        sub: 'Термины первокурсника' },
      { id: 'links', ico: 'link', tone: 'violet', title: 'Веб-сервисы',
        sub: 'ОРИОКС, кабинет, почта' },
      { id: 'search', ico: 'search', tone: 'violet', title: 'Поиск',
        sub: 'По всему приложению' },
    ],
  },
  {
    title: 'Своё',
    tiles: [
      { id: 'profile', ico: 'user', tone: 'grey', title: 'Профиль',
        sub: 'Группа, тема, избранное' },
      { id: 'about', ico: 'landmark', tone: 'grey', title: 'О МИЭТ',
        sub: 'История и факты' },
      { id: 'support', ico: 'lifebuoy', tone: 'grey', title: 'Вопрос автору',
        sub: 'Написать напрямую' },
      { id: 'site', ico: 'globe', tone: 'grey', title: 'Сайт miet.ru',
        sub: 'Официальный' },
    ],
  },
];

const tile = t => `
  <button class="tile-card tone-${t.tone}" data-open="${t.id}">
    <span class="tile-ico">${icon(t.ico, 22)}</span>
    <span class="tile-name">${esc(t.title)}</span>
    <span class="tile-note">${esc(typeof t.sub === 'function' ? t.sub(data) : t.sub)}</span>
  </button>`;

async function usefulScreen() {
  const node = screen({
    title: 'Полезное',
    subtitle: 'Справочник студента МИЭТ',
    actions: iconBtn('search', 'search'),
    body: SECTIONS.map(s => `
      <div class="section-head"><div class="section-title">${esc(s.title)}</div></div>
      ${s.note ? `<p class="section-note">${esc(s.note)}</p>` : ''}
      <div class="tile-grid">${s.tiles.map(tile).join('')}</div>
    `).join('') + (account.can_stats ? `
      <div class="section-head"><div class="section-title">Управление</div></div>
      <div class="tile-grid">
        <button class="tile-card tone-blue" data-open="admin">
          <span class="tile-ico">${icon('shield', 22)}</span>
          <span class="tile-name">Админка</span>
          <span class="tile-note">Статистика и юзеры</span>
        </button>
      </div>` : ''),
  });

  node.addEventListener('click', e => {
    const b = e.target.closest('[data-open]');
    if (!b) return;
    const id = b.dataset.open;
    // Общежития и деньги — это разделы кампуса, а не отдельные экраны:
    // данные там уже собраны, и дублировать их было бы враньём про две
    // разные страницы с одним содержимым.
    if (id === 'dorm') return go('campusItem', { id: 'dorm' });
    if (id === 'money') return go('campusItem', { id: 'scholarship' });
    if (id === 'site') return openLink('https://www.miet.ru');
    if (id === 'rooms') return go('teachers', { mode: 'rooms' });
    go(id);
  });

  node.querySelector('[data-action="search"]')?.addEventListener('click',
    () => go('search'));

  return node;
}

return {'default': usefulScreen};
})();

/* ==== js\screens\about.js ==== */
__mod['js/screens/about.js'] = (function () {
// О университете: факты, описание, реквизиты и контакты.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var contactRows = __mod['js/ui.js']['contactRows'];
var data = __mod['js/store.js']['data'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

async function aboutScreen() {
  const u = data.university || {};
  const paragraphs = (u.about || '').split(/\n{2,}/).map(p => p.trim()).filter(Boolean);

  const node = screen({
    title: u.short || 'МИЭТ',
    subtitle: u.name,
    small: true,
    body: `
      <div class="kpi-grid" style="margin-bottom:18px">
        ${(u.facts || []).map(f => `
          <div class="kpi-tile">
            <div class="kpi-number">${esc(f.k)}</div>
            <div class="kpi-label">${esc(f.v)}</div>
          </div>`).join('')}
      </div>

      ${paragraphs.length ? `<div class="article-text" style="font-size:15px">
        ${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}
      </div>` : ''}

      <div class="section-head"><div class="section-title">Контакты</div></div>
      ${contactRows({ phone: u.phone, email: u.email, address: u.address })}

      <div class="section-head"><div class="section-title">Реквизиты</div></div>
      ${listCard([
      listRow({ title: 'Полное наименование', sub: u.full }),
      listRow({ title: 'Дата создания', value: u.founded }),
    ])}

      <div class="section-head"><div class="section-title">Ссылки</div></div>
      ${listCard([
      listRow({ ico: 'globe', title: 'miet.ru', sub: 'Официальный сайт', chevron: true, id: 'https://www.miet.ru', cls: 'tap' }),
      listRow({ ico: 'calendar', title: 'Расписание занятий', sub: 'miet.ru/schedule', chevron: true, id: 'https://miet.ru/schedule', cls: 'tap' }),
      listRow({ ico: 'news', title: 'Новости', sub: 'miet.ru/news', chevron: true, id: 'https://www.miet.ru/news/', cls: 'tap' }),
      listRow({ ico: 'clipboard', title: 'Сведения об образовательной организации', chevron: true, id: 'https://miet.ru/sveden/', cls: 'tap' }),
      listRow({ ico: 'key', title: 'Личный кабинет', sub: 'account.miet.ru', chevron: true, id: 'https://account.miet.ru/', cls: 'tap' }),
    ])}

      <div class="fab-note">
        Неофициальное приложение. Вся информация — с miet.ru.
      </div>`,
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('.list-row[data-id^="http"]');
    if (row) openLink(row.dataset.id);
  });
  void icon;
  return node;
}

return {'default': aboutScreen};
})();

/* ==== js\screens\admin-days.js ==== */
__mod['js/screens/admin-days.js'] = (function () {
// Разбор статистики по дням: не «сколько», а «кто именно и когда».
//
// Дневные графики в сводке отвечают на вопрос «растёт ли», но не
// отвечают на «что было во вторник». Здесь наоборот: выбираешь день —
// видишь список людей, время первого и последнего касания и чем они
// занимались.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var listCard = __mod['js/ui.js']['listCard'];
var get = __mod['js/api.js']['get'];
var go = __mod['js/router.js']['go'];
var haptic = __mod['js/tg.js']['haptic'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

const KIND_NAMES = {
  open: 'Заходы в приложение', tab: 'Переключения вкладок',
  screen: 'Открытия экранов', bot: 'Обращения к боту',
};

const TAB_NAMES = {
  home: 'Главная', schedule: 'Расписание', news: 'Лента', useful: 'Полезное',
  clubs: 'Кружки', profile: 'Профиль',
};

const dayLabel = iso => `${iso.slice(8, 10)}.${iso.slice(5, 7)}`;

const WEEK = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
const weekdayOf = iso => WEEK[new Date(iso + 'T12:00:00Z').getUTCDay()];

/**
 * Полоса часов суток. Двадцать четыре столбика читаются с одного взгляда
 * и отвечают на вопрос, в какое время писать объявление.
 */
function hoursStrip(hours) {
  const max = Math.max(1, ...hours.map(h => h.count));
  return `
    <div class="hours">
      ${hours.map(h => `
        <div class="hour-col" title="${h.hour}:00 — ${h.count}">
          <div class="hour-bar" style="height:${Math.round(h.count / max * 100)}%"></div>
          <div class="hour-tick">${h.hour % 6 === 0 ? h.hour : ''}</div>
        </div>`).join('')}
    </div>`;
}

async function adminDaysScreen({ date } = {}) {
  if (date) return dayScreen(date);

  let list;
  try {
    list = await get('/api/admin/days?days=30');
  } catch (err) {
    return screen({ title: 'По дням', body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const days = [...list.days].reverse();      // свежие сверху
  const max = Math.max(1, ...days.map(d => d.actions));

  const node = screen({
    title: 'По дням',
    subtitle: 'Выбери день — увидишь, кто в нём был',
    body: days.some(d => d.actions) ? `
      <div class="list-card">
        ${days.map(d => `
          <div class="list-row tap" data-date="${d.date}">
            <div class="list-row-body">
              <div class="row-title">
                ${esc(dayLabel(d.date))} · ${esc(weekdayOf(d.date))}
              </div>
              <div class="row-subtitle">
                ${d.people} ${plural(d.people, 'человек', 'человека', 'человек')} ·
                ${d.actions} ${plural(d.actions, 'действие', 'действия', 'действий')}
              </div>
            </div>
            <div class="day-bar">
              <i style="width:${Math.round(d.actions / max * 100)}%"></i>
            </div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>`).join('')}
      </div>`
      : emptyState('Пока нечего разбирать — событий не было', 'calendar'),
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-date]');
    if (row) {
      haptic('light');
      go('adminDay', { date: row.dataset.date });
    }
  });
  return node;
}

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

async function dayScreen({ date }) {
  let day;
  try {
    day = await get(`/api/admin/day?date=${encodeURIComponent(date)}`);
  } catch (err) {
    return screen({ title: date, body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const total = Object.values(day.kinds).reduce((a, b) => a + b, 0);

  const node = screen({
    title: `${dayLabel(day.date)} · ${weekdayOf(day.date)}`,
    subtitle: `${day.people.length} ${plural(day.people.length, 'человек', 'человека', 'человек')}, ${total} ${plural(total, 'действие', 'действия', 'действий')}`,
    body: `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${day.people.length}</div>
          <div class="kpi-label">Были в этот день</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${day.newcomers}</div>
          <div class="kpi-label">Пришли впервые</div>
        </div>
      </div>

      <div class="section-head"><div class="section-title">Часы</div></div>
      <p class="section-note">Когда именно заходили — по московскому времени.</p>
      <div class="card" style="padding:14px">${hoursStrip(day.hours)}</div>

      ${Object.keys(day.kinds).length ? `
        <div class="section-head"><div class="section-title">Что делали</div></div>
        ${listCard(Object.entries(day.kinds).map(([k, n]) => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(KIND_NAMES[k] || k)}</div>
            </div>
            <div class="list-row-value tnum">${n}</div>
          </div>`))}` : ''}

      ${day.tabs.length ? `
        <div class="section-head"><div class="section-title">Разделы этого дня</div></div>
        ${listCard(day.tabs.map(t => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(TAB_NAMES[t.name] || t.name)}</div>
            </div>
            <div class="list-row-value tnum">${t.count}</div>
          </div>`))}` : ''}

      <div class="section-head"><div class="section-title">Кто был</div></div>
      <p class="section-note">Тапни, чтобы открыть карточку человека.</p>
      ${day.people.length ? `<div class="list-card">
        ${day.people.map(p => `
          <div class="list-row tap" data-user="${p.id}">
            <div class="list-row-body">
              <div class="row-title">
                ${esc(p.name)}${p.username ? ` · <span class="muted-name">@${esc(p.username)}</span>` : ''}
              </div>
              <div class="row-subtitle">
                ${esc(p.first_at?.slice(0, 5) || '')}–${esc(p.last_at?.slice(0, 5) || '')}
                ${p.group ? ` · ${esc(p.group)}` : ''}
                ${p.bot ? ` · бот: ${p.bot}` : ''}
              </div>
            </div>
            <div class="list-row-value tnum">${p.actions}</div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>`).join('')}
      </div>` : emptyState('В этот день никого не было', 'users')}`,
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('[data-user]');
    if (row) go('adminUser', { id: +row.dataset.user });
  });
  return node;
}


void openLink;

return {'default': adminDaysScreen, 'dayScreen': dayScreen, 'hoursStrip': hoursStrip, 'plural': plural, 'KIND_NAMES': KIND_NAMES, 'TAB_NAMES': TAB_NAMES, 'dayLabel': dayLabel, 'weekdayOf': weekdayOf};
})();

/* ==== js\screens\admin.js ==== */
__mod['js/screens/admin.js'] = (function () {
// Админка: статистика, список людей, роли и доступы.
//
// Экран целиком живёт на сервере: здесь нет ни одной цифры из localStorage.
// Кнопка входа в профиле спрятана от посторонних, но это только удобство —
// решает всё равно сервер, и каждый запрос отсюда он проверяет заново.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var segmented = __mod['js/ui.js']['segmented'];
var bindChoice = __mod['js/ui.js']['bindChoice'];
var toggle = __mod['js/ui.js']['toggle'];
var toast = __mod['js/ui.js']['toast'];
var emptyState = __mod['js/ui.js']['emptyState'];
var kpi = __mod['js/ui.js']['kpi'];
var get = __mod['js/api.js']['get'];
var post = __mod['js/api.js']['post'];
var account = __mod['js/api.js']['account'];
var data = __mod['js/store.js']['data'];
var TABS = __mod['js/router.js']['TABS'];
var go = __mod['js/router.js']['go'];
var refresh = __mod['js/router.js']['refresh'];
var haptic = __mod['js/tg.js']['haptic'];
var hapticNotify = __mod['js/tg.js']['hapticNotify'];
var confirmDialog = __mod['js/tg.js']['confirmDialog'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];
var hoursStrip = __mod['js/screens/admin-days.js']['hoursStrip'];
var plural = __mod['js/screens/admin-days.js']['plural'];
var dayLabel = __mod['js/screens/admin-days.js']['dayLabel'];
var weekdayOf = __mod['js/screens/admin-days.js']['weekdayOf'];

// Какую вкладку админки показывать. Живёт в модуле, а не в параметрах
// экрана: возврат из карточки человека должен вернуть на список, а не
// на статистику.
let tab = 'stats';

const TAB_META = Object.fromEntries(TABS.map(t => [t.id, t]));

const SCREEN_NAMES = {
  article: 'Новость', club: 'Кружок', campus: 'Кампус',
  campusItem: 'Раздел кампуса', institute: 'Институт', institutes: 'Институты',
  about: 'О МИЭТ', search: 'Поиск', links: 'Полезные ссылки',
  support: 'Поддержка', admin: 'Админка', adminUser: 'Карточка человека',
};

const ROLE_NAMES = { admin: 'Полный админ', moderator: 'Модератор', none: 'Без роли' };

// ─────────────── мелкие помощники ───────────────

/**
 * Время с сервера приходит в UTC строкой «2026-09-06 09:12:44». Без явного
 * Z браузер прочитал бы её как местное время и показал «через 3 часа».
 */
const parseTs = ts => new Date(String(ts || '').replace(' ', 'T') + 'Z');

function ago(ts) {
  if (!ts) return 'никогда';
  const min = Math.floor((Date.now() - parseTs(ts).getTime()) / 60000);
  if (min < 1) return 'только что';
  if (min < 60) return `${min} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const d = Math.floor(h / 24);
  if (d === 1) return 'вчера';
  if (d < 30) return `${d} дн назад`;
  return parseTs(ts).toLocaleDateString('ru-RU');
}

// dayLabel и weekdayOf приезжают из admin-days.js — свои копии здесь были
// бы вторым определением того же имени, а это уже не дубль кода, а
// SyntaxError: модуль перестаёт грузиться целиком.

const fullName = u =>
  [u.first_name, u.last_name].filter(Boolean).join(' ') || `id ${u.id}`;

const avatar = (u, size = 44) => (u.photo_url
  ? `<img class="avatar" src="${esc(u.photo_url)}" alt=""
       style="width:${size}px;height:${size}px;object-fit:cover" decoding="async">`
  : `<div class="avatar" style="width:${size}px;height:${size}px;font-size:${Math.round(size / 2.6)}px">
       ${esc((u.first_name || '?')[0])}</div>`);

/**
 * Столбчатый график по дням. Своими руками, без библиотеки: у приложения
 * нет сборки, а тянуть чужой скрипт ради четырнадцати прямоугольников —
 * это лишние полтораста килобайт на телефон.
 */
function bars(title, series, tone = 'primary') {
  const max = Math.max(1, ...series.map(p => p.count));
  const last = series[series.length - 1] || { date: '', count: 0 };
  return `
    <div class="card chart-card">
      <div class="chart-title">${esc(title)}</div>
      <div class="chart-last">${esc(dayLabel(last.date))}: <b>${last.count}</b></div>
      <div class="bars">
        ${series.map((p, i) => `
          <div class="bar-col" title="${esc(p.date)}: ${p.count}">
            <div class="bar bar-${tone}" style="height:${Math.max(2, Math.round(p.count / max * 100))}%"></div>
            <div class="bar-day">${i % 3 === 0 || i === series.length - 1 ? esc(dayLabel(p.date)) : ''}</div>
          </div>`).join('')}
      </div>
    </div>`;
}

const errorCard = err => `
  <div class="card" style="padding:18px">
    <div class="row-title" style="margin-bottom:6px">Не получилось загрузить</div>
    <div class="row-subtitle">${esc(err.message)}</div>
  </div>`;

// ─────────────── экран админки ───────────────

async function adminScreen() {
  const node = screen({
    title: 'Админка',
    body: `
      <div class="pill-row admin-tabs" id="atabs">
        ${[['stats', 'Статистика'], ['days', 'По дням'], ['users', 'Юзеры'],
    ['roles', 'Роли'], ['flags', 'Настройки']]
    .map(([id, label]) => `
          <button class="pill ${tab === id ? 'active' : ''}" data-atab="${id}">${label}</button>`).join('')}
      </div>
      <div id="apane"><div class="skeleton" style="height:120px"></div></div>`,
  });

  const pane = node.querySelector('#apane');
  node.querySelector('#atabs').addEventListener('click', e => {
    const b = e.target.closest('[data-atab]');
    if (!b || b.dataset.atab === tab) return;
    tab = b.dataset.atab;
    haptic('light');
    refresh();
  });

  paint(pane);
  return node;
}

async function paint(pane) {
  try {
    if (tab === 'stats') pane.innerHTML = await statsPane();
    else if (tab === 'days') await daysPane(pane);
    else if (tab === 'users') await usersPane(pane);
    else if (tab === 'flags') await flagsPane(pane);
    else await rolesPane(pane);
  } catch (err) {
    pane.innerHTML = errorCard(err);
  }
}

// ─────────────── вкладка «Статистика» ───────────────

async function statsPane() {
  const s = await get('/api/admin/stats?days=14');
  const t = s.totals;

  const f = s.feed || {};
  const tiles = [
    [t.users, 'Всего пользователей'],
    [t.today, 'Активны сегодня'],
    [t.week, 'Активны за 7 дней'],
    [t.subs, 'Подписок на расписание'],
    [t.app, 'Открывали приложение'],
    [t.bot, 'Писали боту'],
    [t.premium, 'С Telegram Premium'],
    [t.blocked, 'Заблокировано'],
  ];

  const feedTiles = [
    [f.posts ?? 0, 'Постов в ленте'],
    [f.news ?? 0, 'Новостей с miet.ru'],
    [f.comments ?? 0, 'Комментариев'],
    [f.reads ?? 0, 'Прочтений'],
    [f.reactions ?? 0, 'Реакций'],
    [f.votes ?? 0, 'Голосов в опросах'],
    [f.pending ?? 0, 'Ждут одобрения'],
  ];

  const h = s.help || {};
  const helpTiles = [
    [h.need ?? 0, 'Просят помощи'],
    [h.offer ?? 0, 'Предлагают помощь'],
    [h.closed ?? 0, 'Вопросов закрыто'],
  ];

  const sections = s.tabs.length ? listCard(s.tabs.map(x => {
    const meta = TAB_META[x.name];
    return `
      <div class="list-row">
        <div class="icon-tile">${icon(meta?.ico || 'grid', 19)}</div>
        <div class="list-row-body">
          <div class="row-title">${esc(meta?.label || x.name)}</div>
          <div class="row-subtitle">${x.share}% от всех открытий вкладок</div>
        </div>
        <div class="list-row-value tnum">${x.count}</div>
      </div>`;
  })) : emptyState('Вкладки ещё никто не открывал', 'grid');

  const screens = s.screens.length ? listCard(s.screens.map(x => listRow({
    title: SCREEN_NAMES[x.name] || x.name,
    value: String(x.count),
  }))) : '';

  const groups = s.groups.length ? listCard(s.groups.map(x => listRow({
    title: x.name, value: String(x.count),
  }))) : emptyState('Группу пока никто не выбрал', 'users');

  const cmds = s.bot_commands.length ? listCard(s.bot_commands.map(x => listRow({
    title: x.name, value: String(x.count),
  }))) : '';

  return `
    <div class="kpi-grid">${tiles.map(([n, l]) => kpi(n, l)).join('')}</div>

    <div class="section-head"><div class="section-title">Лента</div></div>
    <p class="section-note">Посты людей, новости с сайта и что с ними делают.</p>
    <div class="kpi-grid">${feedTiles.map(([n, l]) => kpi(n, l)).join('')}</div>

    <div class="section-head"><div class="section-title">Помощь в заданиях</div></div>
    <div class="kpi-grid">${helpTiles.map(([n, l]) => kpi(n, l)).join('')}</div>

    <div class="section-head"><div class="section-title">Активность</div></div>
    <p class="section-note">Заходы в приложение, новые люди и обращения к боту по дням.</p>
    <div class="stack">
      ${bars('Заходы в приложение', s.opens, 'primary')}
      ${bars('Новые пользователи', s.newcomers, 'success')}
      ${bars('Обращения к боту', s.commands, 'warning')}
    </div>

    <div class="section-head"><div class="section-title">Часы и дни</div></div>
    <p class="section-note">Когда людям удобно — по московскому времени.</p>
    <div class="card" style="padding:14px">${hoursStrip(s.hours || [])}</div>
    <div class="card" style="padding:14px;margin-top:10px">
      <div class="weekdays">
        ${(s.weekdays || []).map(d => {
    const top = Math.max(1, ...(s.weekdays || []).map(x => x.count));
    return `<div class="wd-col" title="${esc(d.day)}: ${d.count}">
              <div class="wd-bar" style="height:${Math.round(d.count / top * 100)}%"></div>
              <div class="wd-name">${esc(d.day)}</div>
            </div>`;
  }).join('')}
      </div>
    </div>

    <div class="section-head"><div class="section-title">Какие разделы смотрят</div></div>
    <p class="section-note">Сколько раз открывали каждую вкладку нижнего меню.</p>
    ${sections}

    ${screens ? `<div class="section-head"><div class="section-title">Экраны внутри разделов</div></div>${screens}` : ''}

    <div class="section-head"><div class="section-title">Популярные группы</div></div>
    <p class="section-note">Расписание какой группы люди выбрали своим.</p>
    ${groups}

    ${cmds ? `<div class="section-head"><div class="section-title">Что нажимают в боте</div></div>${cmds}` : ''}`;
}

// ─────────────── вкладка «По дням» ───────────────

/**
 * Оглавление дней. Сам разбор дня живёт в отдельном экране: там список
 * людей, часы и разделы, и вкладка под ним стала бы длиннее любой другой.
 */
async function daysPane(pane) {
  const list = await get('/api/admin/days?days=30');
  const days = [...list.days].reverse();
  const max = Math.max(1, ...days.map(d => d.actions));

  pane.innerHTML = days.some(d => d.actions) ? `
    <p class="section-note" style="margin-top:0">
      Тапни день — увидишь, кто в нём был, во сколько и что смотрел.
    </p>
    <div class="list-card">
      ${days.map(d => `
        <div class="list-row tap" data-date="${d.date}">
          <div class="list-row-body">
            <div class="row-title">${esc(dayLabel(d.date))} · ${esc(weekdayOf(d.date))}</div>
            <div class="row-subtitle">
              ${d.people} ${plural(d.people, 'человек', 'человека', 'человек')} ·
              ${d.actions} ${plural(d.actions, 'действие', 'действия', 'действий')}
            </div>
          </div>
          <div class="day-bar"><i style="width:${Math.round(d.actions / max * 100)}%"></i></div>
          <span class="chevron">${icon('chevronRight', 18)}</span>
        </div>`).join('')}
    </div>`
    : emptyState('Событий пока не было', 'calendar');

  pane.addEventListener('click', e => {
    const row = e.target.closest('[data-date]');
    if (row) go('adminDay', { date: row.dataset.date });
  });
}

// ─────────────── вкладка «Юзеры» ───────────────

const userRow = u => `
  <div class="list-row tap" data-user="${u.id}">
    ${avatar(u)}
    <div class="list-row-body">
      <div class="row-title">${esc(fullName(u))}${u.username ? ` · <span class="muted-name">@${esc(u.username)}</span>` : ''}</div>
      <div class="row-subtitle">
        ${u.blocked ? 'Заблокирован · ' : ''}${u.role && u.role !== 'none' ? esc(ROLE_NAMES[u.role]) + ' · ' : ''}Последний раз: ${esc(ago(u.last_seen))}
      </div>
    </div>
    <span class="chevron">${icon('chevronRight', 18)}</span>
  </div>`;

async function usersPane(pane) {
  let offset = 0;
  let query = '';
  const PAGE = 50;

  pane.innerHTML = `
    <p class="section-note" style="margin-top:0">
      Все, кто хоть раз открывал мини-апп или писал боту. Тапни, чтобы
      посмотреть подробную статистику.
    </p>
    <div class="search-box" style="margin-bottom:12px">
      ${icon('search', 19, 'muted')}
      <input id="uq" type="search" placeholder="Имя, ник, группа или id"
             autocomplete="off" spellcheck="false">
    </div>
    <div id="ulist"><div class="skeleton" style="height:120px"></div></div>
    <div id="umore"></div>`;

  const list = pane.querySelector('#ulist');
  const more = pane.querySelector('#umore');

  async function load(reset) {
    if (reset) offset = 0;
    const page = await get(
      `/api/admin/users?limit=${PAGE}&offset=${offset}&q=${encodeURIComponent(query)}`);
    const html = page.users.length
      ? listCard(page.users.map(userRow))
      : emptyState('Никого не нашлось', 'search');
    if (reset) list.innerHTML = html;
    else list.insertAdjacentHTML('beforeend', html);
    offset += page.users.length;
    more.innerHTML = offset < page.total
      ? `<button class="btn-secondary" id="umorebtn" style="margin-top:12px">
           Показать ещё · осталось ${page.total - offset}</button>`
      : (page.total ? `<div class="fab-note">Всего ${page.total}</div>` : '');
  }

  // Ввод «дребезжит» специально: список грузится с сервера, и запрос на
  // каждую букву при быстром наборе обгонял бы сам себя.
  let timer = null;
  pane.querySelector('#uq').addEventListener('input', e => {
    query = e.target.value.trim();
    clearTimeout(timer);
    timer = setTimeout(() => load(true).catch(err => { list.innerHTML = errorCard(err); }), 250);
  });

  pane.addEventListener('click', e => {
    if (e.target.closest('#umorebtn')) {
      load(false).catch(err => toast(err.message));
      return;
    }
    const row = e.target.closest('[data-user]');
    if (row) go('adminUser', { id: +row.dataset.user });
  });

  await load(true);
}

// ─────────────── вкладка «Роли» ───────────────

async function rolesPane(pane) {
  // Отдельного списка ролей на сервере нет: людей с ролью единицы, и проще
  // отфильтровать первую страницу, чем заводить ради этого маршрут.
  const page = await get('/api/admin/users?limit=200');
  const held = page.users.filter(u => (u.role && u.role !== 'none') || u.blocked);
  pane.innerHTML = `
    <p class="section-note" style="margin-top:0">
      Кому что выдано. Роль назначается в карточке человека — открой его во
      вкладке «Юзеры».
    </p>
    ${held.length ? listCard(held.map(userRow))
    : emptyState('Роли пока никому не выданы', 'shield')}
    <div class="section-head"><div class="section-title">Как это работает</div></div>
    <div class="card" style="padding:16px">
      <div class="row-subtitle" style="line-height:1.55">
        <b>Полный админ</b> видит всё и раздаёт роли. <b>Модератор</b> —
        только то, что отмечено тумблерами. Человеку без роли можно открыть
        доступ к разделам: саму админку он не увидит, но сможет писать в
        выбранное.<br><br>
        Владельцы из переменной <b>ADMIN_IDS</b> — постоянные админы: их
        нельзя ни разжаловать, ни заблокировать отсюда, иначе можно было бы
        одним тапом закрыть себе вход.
      </div>
    </div>`;
}

// ─────────────── вкладка «Настройки» ───────────────

/**
 * Переключатели режима ленты. Меняет их только полный админ — сервер это
 * и проверяет; здесь тумблеры просто не показываются остальным.
 */
async function flagsPane(pane) {
  const { flags } = await get('/api/admin/settings');

  const draw = list => {
    pane.innerHTML = `
      <p class="section-note" style="margin-top:0">
        Меняются на ходу и переживают перезапуск бота.
      </p>
      <div class="list-card">
        ${list.map(f => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(f.title)}</div>
              <div class="row-subtitle">${esc(f.note)}</div>
            </div>
            ${toggle(f.value, f.key)}
          </div>`).join('')}
      </div>

      <div class="fab-note">
        Премодерация не касается тех, кто сам разбирает очередь: отправлять
        пост на одобрение самому себе незачем.
      </div>`;
  };
  draw(flags);

  pane.addEventListener('click', async e => {
    const t = e.target.closest('[data-toggle]');
    if (!t) return;
    const key = t.dataset.toggle;
    const value = !t.classList.contains('on');
    t.classList.toggle('on', value);
    haptic('light');
    try {
      const r = await post('/api/admin/settings', { key, value });
      hapticNotify('success');
      draw(r.flags);
    } catch (err) {
      toast(err.message);
      t.classList.toggle('on', !value);
    }
  });
}

// ─────────────── карточка человека ───────────────

async function adminUserScreen({ id }) {
  let card;
  try {
    card = await get(`/api/admin/users/${id}`);
  } catch (err) {
    return screen({ title: 'Человек', body: errorCard(err) });
  }

  const perms = await get('/api/admin/perms').catch(() => ({ perms: [], roles: [] }));
  const access = card.access;
  const clubs = data.clubs || [];

  const maxDay = Math.max(1, ...card.activity.map(d => d.count));
  const heat = card.activity.map(d => {
    const level = d.count === 0 ? 0 : Math.min(4, Math.ceil(d.count / maxDay * 4));
    return `<div class="heat-cell heat-${level}" title="${esc(d.date)}: ${d.count}"></div>`;
  }).join('');

  const feed = card.feed.length ? listCard(card.feed.map(f => {
    const label =
      f.kind === 'open' ? 'Открыл приложение'
        : f.kind === 'tab' ? `Вкладка «${TAB_META[f.name]?.label || f.name}»`
          : f.kind === 'screen' ? `Экран «${SCREEN_NAMES[f.name] || f.name}»`
            : `Бот: ${f.name}`;
    const ico = f.kind === 'open' ? 'zap'
      : f.kind === 'tab' ? 'grid' : f.kind === 'screen' ? 'fileText' : 'messageCircle';
    return listRow({ ico, title: label, sub: ago(f.ts) });
  })) : emptyState('Действий пока нет', 'clock');

  const canRole = account.is_admin && !access.root;
  const canBlock = (account.is_admin || account.perms.includes('users_block'))
    && !access.root && account.id !== card.id;

  const node = screen({
    title: fullName(card),
    body: `
      <div class="card" style="padding:14px 16px;display:flex;gap:12px;align-items:center">
        ${avatar(card, 46)}
        <div style="min-width:0">
          <div class="row-title">${esc(fullName(card))}${card.username ? ` · <span class="muted-name">@${esc(card.username)}</span>` : ''}</div>
          <div class="row-subtitle">
            ${access.root ? 'Владелец' : esc(ROLE_NAMES[access.role])}
            ${card.premium ? ' · Premium' : ''}
            · Последний раз: ${esc(ago(card.last_seen))}
          </div>
          <div class="row-subtitle">
            id ${card.id}${card.group ? ` · группа ${esc(card.group)}` : ' · группа не выбрана'}
          </div>
        </div>
      </div>

      ${card.username ? `
        <button class="btn-secondary" id="tg" style="margin-top:12px">
          ${icon('external', 17)} Написать в Telegram
        </button>` : ''}

      ${canBlock ? `
        <button class="btn-secondary danger-btn" id="block" style="margin-top:12px">
          ${access.blocked ? 'Разблокировать' : 'Заблокировать'}
        </button>` : ''}

      <div class="kpi-grid" style="margin-top:12px">
        ${kpi(card.counts.opens, 'Заходов в приложение')}
        ${kpi(card.counts.tabs, 'Открытий вкладок')}
        ${kpi(card.counts.screens, 'Открытий экранов')}
        ${kpi(card.counts.commands, 'Обращений к боту')}
      </div>

      <div class="section-head"><div class="section-title">Активность за 30 дней</div></div>
      <div class="card heat-card">${heat}</div>

      <div class="section-head"><div class="section-title">Когда заходит</div></div>
      <p class="section-note">Часы суток по московскому времени.</p>
      <div class="card" style="padding:14px">${hoursStrip(card.hours || [])}</div>

      ${(card.bot_actions || []).length ? `
        <div class="section-head"><div class="section-title">Что нажимает в боте</div></div>
        ${listCard(card.bot_actions.map(a => listRow({
    title: a.name, value: String(a.count),
  })))}` : ''}

      ${(card.screens_top || []).length ? `
        <div class="section-head"><div class="section-title">Какие экраны открывает</div></div>
        ${listCard(card.screens_top.map(a => listRow({
    title: SCREEN_NAMES[a.name] || a.name, value: String(a.count),
  })))}` : ''}

      ${(card.days || []).length ? `
        <div class="section-head"><div class="section-title">По дням</div></div>
        <p class="section-note">
          Активных дней: ${card.active_days}. Тапни, чтобы открыть весь день.
        </p>
        <div class="list-card">
          ${card.days.map(d => `
            <div class="list-row tap" data-date="${d.date}">
              <div class="list-row-body">
                <div class="row-title">${esc(dayLabel(d.date))} · ${esc(weekdayOf(d.date))}</div>
                <div class="row-subtitle">
                  ${d.opens ? `${d.opens} ${plural(d.opens, 'заход', 'захода', 'заходов')}` : 'без заходов'}
                  ${d.bot ? ` · бот: ${d.bot}` : ''}
                </div>
              </div>
              <div class="list-row-value tnum">${d.actions}</div>
              <span class="chevron">${icon('chevronRight', 18)}</span>
            </div>`).join('')}
        </div>` : ''}

      <div class="section-head"><div class="section-title">Лента действий</div></div>
      ${feed}

      ${canRole ? `
        <div class="section-head"><div class="section-title">Роль в админке</div></div>
        ${segmented([
      { id: 'admin', label: 'Полный админ' },
      { id: 'moderator', label: 'Модератор' },
      { id: 'none', label: 'Без роли' },
    ], access.role, 'role')}
        <div class="list-card" id="perms" style="margin-top:12px">
          ${perms.perms.map(p => `
            <div class="list-row">
              <div class="list-row-body"><div class="row-title">${esc(p.label)}</div></div>
              ${toggle(access.granted.includes(p.id), p.id)}
            </div>`).join('')}
        </div>
        <button class="btn-primary" id="saveRole" style="margin-top:14px">Сохранить роль</button>

        <div class="section-head"><div class="section-title">Доступ к разделам</div></div>
        <p class="section-note">
          Это не роль в админке — человек не получит саму админку, только
          сможет писать в выбранное.
        </p>
        <div class="list-card" id="sections">
          ${clubs.map(c => `
            <div class="list-row">
              <div class="icon-tile">${icon(c.icon || 'sparkles', 19)}</div>
              <div class="list-row-body"><div class="row-title">Кружок «${esc(c.title)}»</div></div>
              ${toggle(access.granted_sections.includes(c.id), 'sec:' + c.id)}
            </div>`).join('')}
        </div>
        <button class="btn-primary" id="saveSections" style="margin-top:14px">Сохранить доступ</button>
      ` : `
        <div class="section-head"><div class="section-title">Роль</div></div>
        <div class="card" style="padding:16px">
          <div class="row-subtitle">
            ${access.root
    ? 'Это владелец из ADMIN_IDS — его роль задаётся переменной окружения и отсюда не меняется.'
    : 'Роли раздаёт только полный админ.'}
          </div>
        </div>`}`,
  });

  // Тумблеры переключаются на месте, а сохраняются кнопкой — как на любом
  // экране настроек: случайный тап по списку из девяти прав не должен
  // немедленно менять человеку доступ.
  node.addEventListener('click', e => {
    const t = e.target.closest('[data-toggle]');
    if (!t) return;
    t.classList.toggle('on');
    haptic('light');
  });

  if (canRole) {
    let role = access.role;
    bindChoice(node, 'role', v => { role = v; }, 'seg');

    node.querySelector('#saveRole').addEventListener('click', async () => {
      const picked = [...node.querySelectorAll('#perms [data-toggle].on')]
        .map(t => t.dataset.toggle);
      const sections = [...node.querySelectorAll('#sections [data-toggle].on')]
        .map(t => t.dataset.toggle.slice(4));
      try {
        await post(`/api/admin/users/${card.id}/role`,
          { role, perms: picked, sections });
        hapticNotify('success');
        toast(role === 'none' ? 'Роль снята' : `Сохранено: ${ROLE_NAMES[role]}`);
      } catch (err) {
        toast(err.message);
      }
    });

    // Роль и доступы уходят одним запросом — сервер хранит их в одной
    // строке. Кнопки две, потому что на экране это два разных разговора,
    // и «Сохранить доступ» внизу списка кружков ищут именно там.
    node.querySelector('#saveSections').addEventListener('click', () => {
      node.querySelector('#saveRole').click();
    });
  }

  node.querySelector('#tg')?.addEventListener('click', () =>
    openLink(`https://t.me/${card.username}`));

  node.addEventListener('click', e => {
    const day = e.target.closest('[data-date]');
    if (day) go('adminDay', { date: day.dataset.date });
  });

  const blockBtn = node.querySelector('#block');
  blockBtn?.addEventListener('click', async () => {
    const next = !access.blocked;
    if (next && !await confirmDialog(
      `Заблокировать ${fullName(card)}? Бот перестанет отвечать, приложение покажет заглушку.`)) return;
    try {
      await post(`/api/admin/users/${card.id}/block`, { blocked: next });
      access.blocked = next;
      blockBtn.textContent = next ? 'Разблокировать' : 'Заблокировать';
      hapticNotify('success');
      toast(next ? 'Заблокирован' : 'Разблокирован');
    } catch (err) {
      toast(err.message);
    }
  });

  return node;
}

return {'default': adminScreen, 'adminUserScreen': adminUserScreen};
})();

/* ==== js\screens\campus.js ==== */
__mod['js/screens/campus.js'] = (function () {
// Инфраструктура кампуса: библиотека, столовая, общежития, спорт и прочее.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var contactRows = __mod['js/ui.js']['contactRows'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var lightbox = __mod['js/ui.js']['lightbox'];
var data = __mod['js/store.js']['data'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];

async function campusScreen() {
  const items = data.campus || [];
  const node = screen({
    title: 'Кампус',
    subtitle: 'Всё, что есть в университете',
    body: `<div class="stack">
        ${listCard(items.map(c => listRow({
      ico: c.icon, title: c.title, sub: c.sub,
      chevron: true, id: c.id, cls: 'tap',
    })))}
        <div class="section-head"><div class="section-title">Учёба</div></div>
        ${listCard([
      listRow({ ico: 'graduate', title: 'Институты', sub: `${(data.institutes || []).length} институтов и кафедр`, chevron: true, id: '@institutes', cls: 'tap' }),
      listRow({ ico: 'landmark', title: 'О МИЭТ', sub: 'История, контакты, реквизиты', chevron: true, id: '@about', cls: 'tap' }),
      listRow({ ico: 'link', title: 'Полезные ссылки', sub: 'Сервисы и разделы сайта', chevron: true, id: '@links', cls: 'tap' }),
      listRow({ ico: 'lifebuoy', title: 'Поддержка', sub: 'Автор приложения', chevron: true, id: '@support', cls: 'tap' }),
    ])}
      </div>`,
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('.list-row[data-id]');
    if (!row) return;
    const id = row.dataset.id;
    if (id === '@institutes') return go('institutes');
    if (id === '@about') return go('about');
    if (id === '@links') return go('links');
    if (id === '@support') return go('support');
    go('campusItem', { id });
  });
  return node;
}

/** Экран одного раздела кампуса. */
async function campusItemScreen({ id }) {
  const c = (data.campus || []).find(x => x.id === id);
  if (!c) return screen({ title: 'Раздел', body: emptyState('Раздел не найден', 'helpCircle') });

  const paragraphs = (c.text || '').split(/\n{2,}/).map(p => p.trim()).filter(Boolean);

  const node = screen({
    body: `
      ${c.photos?.[0] ? `<div class="hero">
        <img src="img/${esc(c.photos[0])}" alt="" decoding="async">
        <div class="hero-fade"></div>
      </div>` : ''}
      <div class="screen-top">
        <div>
          <h1 class="h1-page small">${esc(c.title)}</h1>
          <p class="subtitle-page">${esc(c.sub)}</p>
        </div>
      </div>

      ${paragraphs.length ? `<div class="article-text" style="font-size:15px">
        ${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}
      </div>` : ''}

      ${c.photos?.length > 1 ? `
        <div class="section-head"><div class="section-title">Фото</div></div>
        <div class="gallery">
          ${c.photos.slice(1).map(p => `<img src="img/${esc(p)}" data-full="img/${esc(p)}" alt="" loading="lazy" decoding="async">`).join('')}
        </div>` : ''}

      ${(c.lead || c.phone || c.email || c.room) ? `
        <div class="section-head"><div class="section-title">Контакты</div></div>
        ${contactRows(c)}` : ''}

      ${c.links?.length ? `
        <div class="section-head"><div class="section-title">Разделы на сайте</div></div>
        ${listCard(c.links.map((l, i) => listRow({
      title: l.title, chevron: true, id: `link${i}`, cls: 'tap',
    })))}` : ''}

      <div style="margin-top:20px">
        <button class="btn-primary" id="open">${icon('external', 18)} Открыть на miet.ru</button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(c.url));
  node.addEventListener('click', e => {
    const img = e.target.closest('[data-full]');
    if (img) return lightbox(img.dataset.full);
    const row = e.target.closest('.list-row[data-id^="link"]');
    if (row) {
      const i = +row.dataset.id.replace('link', '');
      openLink(c.links[i]?.url);
    }
  });
  return node;
}

return {'default': campusScreen, 'campusItemScreen': campusItemScreen};
})();

/* ==== js\screens\clubs.js ==== */
__mod['js/screens/clubs.js'] = (function () {
// Кружки, секции и студенческие объединения МИЭТ.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var contactRows = __mod['js/ui.js']['contactRows'];
var lightbox = __mod['js/ui.js']['lightbox'];
var toast = __mod['js/ui.js']['toast'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var data = __mod['js/store.js']['data'];
var toggleFavorite = __mod['js/store.js']['toggleFavorite'];
var isFavorite = __mod['js/store.js']['isFavorite'];
var settings = __mod['js/store.js']['settings'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var haptic = __mod['js/tg.js']['haptic'];
var screen = __mod['js/screens/common.js']['screen'];
var iconBtn = __mod['js/screens/common.js']['iconBtn'];

const CATS = ['Все', 'Спорт', 'Творчество', 'Медиа', 'Наука',
  'Добро', 'Досуг', 'Объединения', 'Избранное'];

const clubCard = c => `
  <div class="tile" data-club="${esc(c.id)}">
    ${c.photos?.[0] ? `<img class="tile-cover" src="img/${esc(c.photos[0])}" alt="" loading="lazy" decoding="async">` : ''}
    <div class="tile-body">
      <div class="tile-head">
        <span class="tile-icon">${icon(c.icon || 'sparkles', 17)}</span>
        <span class="tile-title">${esc(c.title)}</span>
        ${isFavorite(c.id) ? '<span style="color:var(--danger)">♥</span>' : ''}
      </div>
      ${c.tagline ? `<div class="tile-sub">${esc(c.tagline)}</div>` : ''}
      <div class="chip-row">
        <span class="chip">${esc(c.cat)}</span>
        ${c.place ? `<span class="chip">${icon('pin', 13)} ${esc(c.place)}</span>` : ''}
        ${c.free ? `<span class="chip free">${esc(c.free)}</span>` : ''}
      </div>
    </div>
  </div>`;

async function clubsScreen() {
  const all = data.clubs || [];
  let cat = 'Все';

  const node = screen({
    title: 'Кружки',
    subtitle: `${all.length} клубов, секций и объединений МИЭТ`,
    actions: iconBtn('search', 'search'),
    body: `
      <div class="pill-row" id="cats" style="margin-bottom:16px">
        ${CATS.map(c => `<button class="pill ${c === cat ? 'active' : ''}" data-cat="${esc(c)}">${esc(c)}</button>`).join('')}
      </div>
      <div class="stack" id="list"></div>

      <div class="section-head"><div class="section-title">Где всё происходит</div></div>
      <div class="list-card">
        <div class="list-row tap" data-campus="dk">
          <div class="icon-tile">${icon('drama', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">Дом культуры МИЭТ</div>
            <div class="row-subtitle">Зал на 640 мест, репетиционные</div>
          </div>
          <span class="chevron">${icon('chevronRight', 18)}</span>
        </div>
        <div class="list-row tap" data-campus="sport">
          <div class="icon-tile">${icon('stadium', 19)}</div>
          <div class="list-row-body">
            <div class="row-title">Спорткомплекс</div>
            <div class="row-subtitle">Бассейн, залы, стадион</div>
          </div>
          <span class="chevron">${icon('chevronRight', 18)}</span>
        </div>
      </div>`,
  });

  const list = node.querySelector('#list');
  const draw = () => {
    const items = cat === 'Все' ? all
      : cat === 'Избранное' ? all.filter(c => isFavorite(c.id))
        : all.filter(c => c.cat === cat);
    list.innerHTML = items.length
      ? items.map(clubCard).join('')
      : emptyState(cat === 'Избранное'
        ? 'Отметь кружок сердечком — он появится здесь'
        : 'В этой категории пока пусто', 'sparkles');
  };
  draw();

  node.querySelector('#cats').addEventListener('click', e => {
    const b = e.target.closest('[data-cat]');
    if (!b) return;
    cat = b.dataset.cat;
    node.querySelectorAll('#cats .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    draw();
  });

  node.addEventListener('click', e => {
    const c = e.target.closest('[data-club]');
    if (c) return go('club', { id: c.dataset.club });
    const s = e.target.closest('[data-campus]');
    if (s) return go('campusItem', { id: s.dataset.campus });
    if (e.target.closest('[data-action="search"]')) return go('search');
  });

  return node;
}

/** Экран одного кружка. */
async function clubScreen({ id }) {
  const c = (data.clubs || []).find(x => x.id === id);
  if (!c) return screen({ title: 'Кружок', body: emptyState('Не найдено', 'helpCircle') });

  const paragraphs = (c.about || '').split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
  const fav = isFavorite(c.id);

  const node = screen({
    body: `
      ${c.photos?.[0] ? `<div class="hero">
        <img src="img/${esc(c.photos[0])}" alt="" decoding="async">
        <div class="hero-fade"></div>
      </div>` : ''}
      <div class="screen-top">
        <div>
          <h1 class="h1-page small">${esc(c.title)}</h1>
          ${c.tagline ? `<p class="subtitle-page">${esc(c.tagline)}</p>` : ''}
        </div>
        <div class="header-actions">
          <button class="icon-btn" id="fav" style="color:${fav ? 'var(--danger)' : 'var(--text-tertiary)'}">
            ${icon('heart', 19)}
          </button>
        </div>
      </div>

      <div class="chip-row" style="margin:0 0 18px">
        <span class="chip">${esc(c.cat)}</span>
        ${c.place ? `<span class="chip">${icon('pin', 13)} ${esc(c.place)}</span>` : ''}
        ${c.free ? `<span class="chip free">${esc(c.free)}</span>` : ''}
      </div>

      ${paragraphs.length ? `<div class="article-text" style="font-size:15px">
        ${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}
      </div>` : ''}

      ${c.photos?.length > 1 ? `
        <div class="section-head"><div class="section-title">Фото</div></div>
        <div class="gallery">
          ${c.photos.slice(1).map(p => `<img src="img/${esc(p)}" data-full="img/${esc(p)}" alt="" loading="lazy" decoding="async">`).join('')}
        </div>` : ''}

      ${c.social?.length ? `
        <div class="section-head"><div class="section-title">Соцсети</div></div>
        ${listCard(c.social.map((s, i) => listRow({
      ico: s.label === 'Telegram' ? 'messageCircle' : s.label === 'YouTube' ? 'video' : 'globe',
      title: s.label, sub: s.url.replace(/^https?:\/\//, '').slice(0, 46),
      chevron: true, id: `soc${i}`, cls: 'tap',
    })))}` : ''}

      ${contactRows(c) ? `
        <div class="section-head"><div class="section-title">Контакты</div></div>
        ${contactRows(c)}` : ''}

      <div style="margin-top:20px">
        <button class="btn-primary" id="open">${icon('external', 18)} Страница на miet.ru</button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(c.url));
  node.querySelector('#fav').addEventListener('click', e => {
    const added = toggleFavorite(c.id);
    haptic('medium');
    e.currentTarget.style.color = added ? 'var(--danger)' : 'var(--text-tertiary)';
    toast(added ? 'Добавлено в избранное' : 'Убрано из избранного');
  });
  node.addEventListener('click', e => {
    const img = e.target.closest('[data-full]');
    if (img) return lightbox(img.dataset.full);
    const soc = e.target.closest('.list-row[data-id^="soc"]');
    if (soc) openLink(c.social[+soc.dataset.id.replace('soc', '')]?.url);
  });

  void settings;
  return node;
}

return {'default': clubsScreen, 'clubScreen': clubScreen};
})();

/* ==== js\screens\home.js ==== */
__mod['js/screens/home.js'] = (function () {
// Главная: что сейчас, расписание на сегодня, быстрые разделы, свежие новости.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var data = __mod['js/store.js']['data'];
var settings = __mod['js/store.js']['settings'];
var fetchSchedule = __mod['js/schedule.js']['fetchSchedule'];
var weekOfCycle = __mod['js/schedule.js']['weekOfCycle'];
var nowState = __mod['js/schedule.js']['nowState'];
var slotsOf = __mod['js/schedule.js']['slotsOf'];
var semesterStart = __mod['js/schedule.js']['semesterStart'];
var DAY_NAMES = __mod['js/schedule.js']['DAY_NAMES'];
var go = __mod['js/router.js']['go'];
var switchTab = __mod['js/router.js']['switchTab'];
var tgUser = __mod['js/tg.js']['tgUser'];
var openLink = __mod['js/tg.js']['openLink'];
var get = __mod['js/api.js']['get'];
var canTalk = __mod['js/api.js']['canTalk'];
var screen = __mod['js/screens/common.js']['screen'];
var pickGroup = __mod['js/screens/common.js']['pickGroup'];
var newsRow = __mod['js/screens/common.js']['newsRow'];
var humanDate = __mod['js/screens/common.js']['humanDate'];
var iconBtn = __mod['js/screens/common.js']['iconBtn'];
var dayRows = __mod['js/screens/schedule.js']['dayRows'];
var teacherOf = __mod['js/screens/schedule.js']['teacherOf'];
var feedRow = __mod['js/screens/feed.js']['feedRow'];
var flatten = __mod['js/screens/tasks.js']['flatten'];
var pendingOf = __mod['js/screens/tasks.js']['pendingOf'];
var subjectLook = __mod['js/screens/tasks.js']['subjectLook'];
var art = __mod['js/art.js']['art'];
var artState = __mod['js/art.js']['artState'];

// ОРИОКС и личный кабинет — внешние сервисы, но студенту они нужнее
// всего, поэтому стоят прямо на главной.
const QUICK = [
  { id: 'url:https://orioks.miet.ru/main/login', ico: 'chart', label: 'ОРИОКС' },
  { id: 'teachers', ico: 'teacher', label: 'Преподаватели' },
  { id: 'tasks', ico: 'backpack', label: 'Задания' },
  { id: 'url:https://account.miet.ru/', ico: 'key', label: 'Кабинет' },
  { id: 'campus:canteen', ico: 'utensils', label: 'Столовая' },
  { id: 'campus:library', ico: 'book', label: 'Библиотека' },
  { id: 'clubs', ico: 'sparkles', label: 'Кружки' },
  { id: 'useful-tab', ico: 'grid', label: 'Всё полезное' },
];

async function home() {
  const user = tgUser();
  const now = new Date();

  const node = screen({
    // Заголовок называет приложение, а не здоровается: «Привет, Дима»
    // человек читает один раз, а потом оно просто занимает верх экрана.
    // Имя осталось в приветственной карточке для тех, кто здесь впервые.
    title: 'НИУ МИЭТ',
    subtitle: 'Расписание, новости и жизнь университета',
    actions: iconBtn('search', 'search') + iconBtn('user', 'profile'),
    body: `
      <div id="hello-slot"></div>
      <div id="now-slot" class="stack"></div>
      <div id="study-slot"></div>

      <div class="section-head"><div class="section-title">Разделы</div></div>
      <div class="quick-grid">
        ${QUICK.map(q => `<button class="quick-item" data-quick="${q.id}">
            <span class="quick-icon">${icon(q.ico, 21)}</span>
            <span class="quick-label">${esc(q.label)}</span>
          </button>`).join('')}
      </div>

      <div class="section-head">
        <div class="section-title">Новости</div>
        <button class="section-link" data-go="news">Все</button>
      </div>
      <div class="list-card" id="fresh">
        ${(data.news || []).slice(0, 4).map(newsRow).join('')}
      </div>

      <div class="section-head"><div class="section-title">Университет</div></div>
      <div class="kpi-grid">
        ${(data.university?.facts || []).map(f =>
    `<div class="kpi-tile"><div class="kpi-number">${esc(f.k)}</div>
           <div class="kpi-label">${esc(f.v)}</div></div>`).join('')}
      </div>
      <div style="margin-top:10px">
        ${listCard([
      listRow({ ico: 'landmark', title: 'О МИЭТ', sub: 'История, факты, контакты', chevron: true, id: 'about', cls: 'tap' }),
      listRow({ ico: 'graduate', title: 'Институты', sub: `${(data.institutes || []).length} подразделений`, chevron: true, id: 'institutes', cls: 'tap' }),
      listRow({ ico: 'lifebuoy', title: 'Поддержка', sub: 'Автор приложения', chevron: true, id: 'support', cls: 'tap' }),
    ])}
      </div>

      <div class="fab-note">Данные с miet.ru · обновлено ${esc(data.meta?.generated || '')}</div>`,
  });

  // ── знакомство ──
  renderHello(node.querySelector('#hello-slot'), user);

  // ── карточка «сейчас» ──
  const slot = node.querySelector('#now-slot');
  renderNow(slot, now);

  // ── ближайшие дела из ОРИОКС ──
  renderStudy(node.querySelector('#study-slot'));

  // ── свежее из ленты ──
  // Пока сервер не ответил, на месте блока лежит архив из data/app.json:
  // он всегда под рукой и не оставляет главную пустой.
  renderFresh(node.querySelector('#fresh'));

  // ── обработчики ──
  node.querySelector('[data-action="search"]')?.addEventListener('click', () => go('search'));
  // Профиль перестал быть вкладкой, но с главной до него должно быть
  // одно нажатие: там группа, тема и всё своё.
  node.querySelector('[data-action="profile"]')?.addEventListener('click', () => go('profile'));
  node.addEventListener('click', e => {
    const q = e.target.closest('[data-quick]');
    if (q) {
      const raw = q.dataset.quick;
      if (raw.startsWith('url:')) return openLink(raw.slice(4));
      if (raw === 'useful-tab') return switchTab('useful');
      const [route, id] = raw.split(':');
      return go(route === 'campus' && id ? 'campusItem' : route, { id });
    }
    // Запись из ленты целиком читается там же — на главной только повод
    // туда заглянуть, поэтому ведём на вкладку, а не на отдельный экран.
    if (e.target.closest('[data-study]')) return go('tasks');
    if (e.target.closest('[data-feed]')) return switchTab('news');
    const n = e.target.closest('[data-news]');
    if (n) return go('article', { id: n.dataset.news });
    const g = e.target.closest('[data-go]');
    if (g) return switchTab(g.dataset.go);
    const row = e.target.closest('.list-row[data-id]');
    if (row) return go(row.dataset.id);
  });

  return node;
}

// Карточку «что это такое» человек читает один раз. Дальше она мешает:
// главная нужна, чтобы за две секунды увидеть свою пару.
const HELLO_KEY = 'miet-hello-seen';

/**
 * Короткий рассказ о приложении — только тем, кто здесь впервые, и
 * ровно до первого «Понятно».
 */
function renderHello(slot, user) {
  if (!slot) return;
  let seen = false;
  try {
    seen = localStorage.getItem(HELLO_KEY) === '1';
  } catch { /* приватный режим — покажем ещё раз, не страшно */ }
  if (seen) return;

  const name = user?.first_name ? `${user.first_name}, привет` : 'Привет';
  slot.innerHTML = `
    <div class="card hello">
      <div class="hello-title">${esc(name)}</div>
      <div class="hello-text">
        Это неофициальное приложение студентов МИЭТ. Здесь расписание твоей
        группы с живого сайта, лента новостей и объявлений, справочник
        преподавателей и аудиторий, кружки и всё, что обычно приходится
        искать по чатам.
      </div>
      <div class="hello-list">
        ${[
      ['calendar', 'Расписание', 'Пары на сегодня и всю неделю цикла'],
      ['news', 'Лента', 'Новости университета и объявления'],
      ['teacher', 'Преподаватели', 'Кто ведёт, где и с какими группами'],
      ['grid', 'Полезное', 'Баллы, кураторы, контакты, помощь с заданиями'],
    ].map(([ico, title, sub]) => `
          <div class="hello-row">
            <span class="hello-ico">${icon(ico, 17)}</span>
            <span><b>${esc(title)}</b> — ${esc(sub)}</span>
          </div>`).join('')}
      </div>
      <button class="btn-primary" id="hello-ok">Понятно</button>
    </div>`;

  slot.querySelector('#hello-ok').addEventListener('click', () => {
    try { localStorage.setItem(HELLO_KEY, '1'); } catch { /* не критично */ }
    slot.innerHTML = '';
  });
}

// Один обход ОРИОКС — это восемь запросов к серверу института, и идут
// они секундами. На главную возвращаются по десять раз за день, поэтому
// ответ живёт несколько минут: задания за это время не меняются, а
// институт не получает обход на каждое переключение вкладки.
let studyCache = null;
const STUDY_TTL = 5 * 60 * 1000;

const stillFresh = hit =>
  (hit && Date.now() - hit.at < STUDY_TTL ? hit.data : null);

/**
 * Ближайшие дела из ОРИОКС — три строки под расписанием.
 *
 * Экран «Задания» знает про них всё, но открывают его, когда про
 * задание и так вспомнили. Главную открывают просто так, по дороге на
 * пару, — и здесь ближайший срок стоит ровно там, где на него смотрят.
 *
 * Молча и последним: ОРИОКС отвечает секундами (обход всех дисциплин),
 * и задерживать из-за него расписание нельзя. Не подключён, не ответил,
 * нечего показать — блока просто нет, а звать подключаться на главной
 * незачем: для этого есть плитка «Задания».
 */
async function renderStudy(slot) {
  if (!slot || !canTalk || !settings.group) return;

  let data = stillFresh(studyCache);
  if (!data) {
    try {
      data = await get('/api/orioks', { timeout: 25000, retries: 0 });
    } catch { return; }
    studyCache = { at: Date.now(), data };
  }
  if (!data.linked || data.error || !data.tasks) return;

  let sched = null;
  let start = null;
  try {
    sched = await fetchSchedule(settings.group);
    start = semesterStart(sched.semestr);
  } catch { /* без расписания останутся недели вместо дней */ }

  // Три ближайших несданных. Больше — уже список дел, а он на своём
  // экране; здесь нужно только «что горит».
  const soon = pendingOf(flatten(data.tasks, sched, start, settings.weekShift))
    .slice(0, 3);
  if (!soon.length) return;

  slot.innerHTML = `
    <div class="section-head">
      <div class="section-title with-icon">${icon('backpack', 17)} Ближайшее</div>
      <button class="section-link" data-study="all">Все задания</button>
    </div>
    <div class="stack">${soon.map(studyRow).join('')}</div>`;
}

/** Строка дела: предмет виден значком, срок — словами, а не неделей. */
const studyRow = t => {
  const look = subjectLook(t.subject);
  const when = t.due
    ? `${WEEKDAYS_SHORT[t.due.getDay()]}, ${t.due.getDate()} ${MONTHS_SHORT[t.due.getMonth()]}`
    : `${t.week || '?'} нед`;
  const left = t.left === null ? ''
    : t.left < 0 ? 'просрочено'
      : t.left === 0 ? 'сегодня'
        : t.left === 1 ? 'завтра'
          : t.left < 7 ? `через ${t.left} дн`
            : `через ${Math.round(t.left / 7)} нед`;
  return `
    <button class="study-row ${esc(t.bucket)}" data-study="${t.idx}">
      <span class="study-badge tone-${look.tone}">${icon(look.glyph, 19)}</span>
      <span class="study-main">
        <span class="study-subject">${esc(t.subject)}</span>
        <span class="study-what">${esc(t.title.main)}</span>
      </span>
      <span class="study-when">
        <span class="study-day">${esc(when)}</span>
        <span class="study-left">${esc(left)}</span>
      </span>
    </button>`;
};

// Короткие подписи: в строку с предметом и сроком полные названия не
// влезают, а «ср, 10 сент» читается с одного взгляда.
const WEEKDAYS_SHORT = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
const MONTHS_SHORT = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн',
  'июл', 'авг', 'сент', 'окт', 'нояб', 'дек'];


/**
 * Свежее из ленты — четыре записи. Тоже асинхронно и молча: сервер здесь
 * необязателен, а падать главной из-за новостей незачем.
 */
async function renderFresh(slot) {
  if (!slot || !canTalk) return;
  try {
    const feed = await get('/api/feed?limit=4', { timeout: 6000, retries: 0 });
    if (feed.posts.length) slot.innerHTML = feed.posts.map(feedRow).join('');
  } catch { /* остаётся архив, который уже нарисован */ }
}

/** Рисует блок «что сейчас» — асинхронно, чтобы не задерживать экран. */
async function renderNow(slot, now) {
  if (!settings.group) {
    slot.innerHTML = `
      <div class="card has-art" style="padding:20px">
        <div class="has-art-body">
          <div class="now-kicker" style="color:var(--text-secondary)">Расписание</div>
          <div style="font-size:19px;font-weight:800;margin:8px 0 4px">Выбери свою группу</div>
          <div class="row-subtitle" style="margin-bottom:16px">
            Покажу пары на сегодня, ближайшую и всю неделю
          </div>
          <button class="btn-primary" id="pick">Выбрать группу</button>
        </div>
        ${art('group', 84, 'art-aside')}
      </div>`;
    slot.querySelector('#pick').addEventListener('click', () =>
      pickGroup(() => location.reload()));
    return;
  }

  slot.innerHTML = `<div class="skeleton" style="height:132px"></div>`;
  let sched;
  try {
    sched = await fetchSchedule(settings.group);
  } catch (err) {
    slot.innerHTML = `<div class="card">
        ${artState('offline', 'Расписание не загрузилось', err.message)}
      </div>`;
    return;
  }

  const week = weekOfCycle(now, sched.semestr, settings.weekShift);
  const { current, next, progress, day } = nowState(sched, week, now);
  const today = day <= 6 ? slotsOf(sched, week, day) : [];

  const card = current
    ? `<div class="now-card">
         <div class="now-kicker">Сейчас идёт</div>
         <div class="now-title">${esc(current.subject)}</div>
         <div class="now-meta">
           <span>${icon('clock', 15)} ${esc(current.from)}–${esc(current.to)}</span>
           ${current.room ? `<span>${icon('door', 15)} ${esc(current.room)}</span>` : ''}
           ${teacherOf(current) ? `<span>${icon('teacher', 15)} ${esc(teacherOf(current))}</span>` : ''}
         </div>
         <div class="now-progress"><i style="width:${Math.round(progress * 100)}%"></i></div>
       </div>`
    : next
      ? `<div class="now-card">
           <div class="now-kicker">Следующая пара</div>
           <div class="now-title">${esc(next.subject)}</div>
           <div class="now-meta">
             <span>${icon('clock', 15)} в ${esc(next.from)}</span>
             ${next.room ? `<span>${icon('door', 15)} ${esc(next.room)}</span>` : ''}
             ${teacherOf(next) ? `<span>${icon('teacher', 15)} ${esc(teacherOf(next))}</span>` : ''}
           </div>
         </div>`
      : `<div class="now-card rest has-art">
           <div class="has-art-body">
             <div class="now-kicker">${day > 6 ? 'Воскресенье' : 'На сегодня всё'}</div>
             <div class="now-title">Пар больше нет</div>
             <div class="now-meta muted">
               <span>${esc(settings.group)}</span><span>${week + 1}-я неделя цикла</span>
             </div>
           </div>
           ${art(day > 6 ? 'rest' : 'done', 76, 'art-aside')}
         </div>`;

  slot.innerHTML = `
    ${card}
    <div class="section-head" style="margin-top:6px">
      <div class="section-title">${day <= 6 ? DAY_NAMES[day] : 'Расписание'}, ${humanDate(now).split(', ')[1]}</div>
      <button class="section-link" data-go="schedule">Вся неделя</button>
    </div>
    ${today.length
      ? `<div class="stack">${dayRows(today, now)}</div>`
      : `<div class="card">${day > 6
        ? artState('rest', 'Воскресенье — выходной',
          'Расписание всей недели цикла — на своей вкладке')
        : artState('free', 'В этот день пар нет',
          'Свободно: можно закрыть хвосты или выдохнуть')}</div>`}`;
}

return {'default': home};
})();

/* ==== js\screens\institutes.js ==== */
__mod['js/screens/institutes.js'] = (function () {
// Институты МИЭТ: список и карточка института с кафедрами и контактами.

var icon = __mod['js/icons.js']['icon'];
var esc = __mod['js/ui.js']['esc'];
var emptyState = __mod['js/ui.js']['emptyState'];
var contactRows = __mod['js/ui.js']['contactRows'];
var listCard = __mod['js/ui.js']['listCard'];
var listRow = __mod['js/ui.js']['listRow'];
var data = __mod['js/store.js']['data'];
var go = __mod['js/router.js']['go'];
var openLink = __mod['js/tg.js']['openLink'];
var screen = __mod['js/screens/common.js']['screen'];
var plural = __mod['js/screens/schedule.js']['plural'];

async function institutesScreen() {
  const items = data.institutes || [];
  const node = screen({
    title: 'Институты',
    subtitle: `${items.length} ${plural(items.length, 'институт', 'института', 'институтов')} МИЭТ`,
    body: `<div class="stack">
      ${items.map(i => `
        <div class="tile" data-inst="${esc(i.id)}">
          ${i.photo ? `<img class="tile-cover" src="img/${esc(i.photo)}" alt="" loading="lazy" decoding="async">` : ''}
          <div class="tile-body">
            <div class="tile-head">
              <span class="tile-title">${esc(i.name)}</span>
              ${i.short ? `<span class="chip">${esc(i.short)}</span>` : ''}
            </div>
            ${i.director ? `<div class="tile-sub">${icon('teacher', 13)} ${esc(i.director)}</div>` : ''}
            ${i.departments?.length ? `<div class="chip-row">
              <span class="chip">${i.departments.length} ${plural(i.departments.length, 'подразделение', 'подразделения', 'подразделений')}</span>
              ${i.room ? `<span class="chip">${icon('door', 13)} ${esc(i.room)}</span>` : ''}
            </div>` : ''}
          </div>
        </div>`).join('')}
    </div>`,
  });

  node.addEventListener('click', e => {
    const t = e.target.closest('[data-inst]');
    if (t) go('institute', { id: t.dataset.inst });
  });
  return node;
}

async function instituteScreen({ id }) {
  const i = (data.institutes || []).find(x => x.id === id);
  if (!i) return screen({ title: 'Институт', body: emptyState('Институт не найден', 'helpCircle') });

  const node = screen({
    body: `
      ${i.photo ? `<div class="hero">
        <img src="img/${esc(i.photo)}" alt="" decoding="async">
        <div class="hero-fade"></div>
      </div>` : ''}
      <div class="screen-top">
        <div>
          <h1 class="h1-page small">${esc(i.name)}</h1>
          ${i.short ? `<p class="subtitle-page">${esc(i.short)}</p>` : ''}
        </div>
      </div>

      ${i.about ? `<div class="article-text" style="font-size:15px;margin-bottom:6px">
        <p>${esc(i.about)}</p></div>` : ''}

      <div class="section-head"><div class="section-title">Контакты</div></div>
      ${contactRows(i) || emptyState('Контакты — на сайте института', 'phone')}

      ${i.departments?.length ? `
        <div class="section-head"><div class="section-title">Кафедры и подразделения</div></div>
        ${listCard(i.departments.map(d => listRow({ title: d })))}` : ''}

      <div style="margin-top:20px">
        <button class="btn-primary" id="open">${icon('external', 18)} Открыть на miet.ru</button>
      </div>`,
  });

  node.querySelector('#open').addEventListener('click', () => openLink(i.url));
  return node;
}

return {'default': institutesScreen, 'instituteScreen': instituteScreen};
})();

/* ==== js\app.js ==== */
__mod['js/app.js'] = (function () {
// Точка входа: тема → Telegram → данные → роутер.

var initTelegram = __mod['js/tg.js']['initTelegram'];
var syncChrome = __mod['js/tg.js']['syncChrome'];
var guardTaps = __mod['js/tg.js']['guardTaps'];
var loadData = __mod['js/store.js']['loadData'];
var settings = __mod['js/store.js']['settings'];
var save = __mod['js/store.js']['save'];
var applyTheme = __mod['js/store.js']['applyTheme'];
var resolveTheme = __mod['js/store.js']['resolveTheme'];
var register = __mod['js/router.js']['register'];
var initRouter = __mod['js/router.js']['init'];
var switchTab = __mod['js/router.js']['switchTab'];
var refresh = __mod['js/router.js']['refresh'];
var loadMe = __mod['js/api.js']['loadMe'];
var account = __mod['js/api.js']['account'];
var track = __mod['js/api.js']['track'];
var syncGroup = __mod['js/api.js']['syncGroup'];

var home = __mod['js/screens/home.js']['default'];
var schedule = __mod['js/screens/schedule.js']['default'];
var articleScreen = __mod['js/screens/news.js']['articleScreen'];
var newsArchive = __mod['js/screens/news.js']['default'];
var moderationScreen = __mod['js/screens/feed.js']['moderationScreen'];
var feed = __mod['js/screens/feed.js']['default'];
var clubScreen = __mod['js/screens/clubs.js']['clubScreen'];
var clubs = __mod['js/screens/clubs.js']['default'];
var campusItemScreen = __mod['js/screens/campus.js']['campusItemScreen'];
var campus = __mod['js/screens/campus.js']['default'];
var instituteScreen = __mod['js/screens/institutes.js']['instituteScreen'];
var institutes = __mod['js/screens/institutes.js']['default'];
var profile = __mod['js/screens/profile.js']['default'];
var about = __mod['js/screens/about.js']['default'];
var search = __mod['js/screens/search.js']['default'];
var links = __mod['js/screens/links.js']['default'];
var support = __mod['js/screens/support.js']['default'];
var adminUserScreen = __mod['js/screens/admin.js']['adminUserScreen'];
var admin = __mod['js/screens/admin.js']['default'];
var useful = __mod['js/screens/useful.js']['default'];
var teacherScreen = __mod['js/screens/teachers.js']['teacherScreen'];
var roomScreen = __mod['js/screens/teachers.js']['roomScreen'];
var directory = __mod['js/screens/teachers.js']['default'];
var scoreScreen = __mod['js/screens/tools.js']['scoreScreen'];
var convertScreen = __mod['js/screens/tools.js']['convertScreen'];
var glossaryScreen = __mod['js/screens/guide.js']['glossaryScreen'];
var contactsScreen = __mod['js/screens/guide.js']['contactsScreen'];
var datesScreen = __mod['js/screens/guide.js']['datesScreen'];
var chatsScreen = __mod['js/screens/community.js']['chatsScreen'];
var curatorsScreen = __mod['js/screens/community.js']['curatorsScreen'];
var help = __mod['js/screens/help.js']['default'];
var dayScreen = __mod['js/screens/admin-days.js']['dayScreen'];
var adminDays = __mod['js/screens/admin-days.js']['default'];
var tasks = __mod['js/screens/tasks.js']['default'];

// Тему уже поставил маленький скрипт в index.html — до первой отрисовки,
// чтобы тёмный Telegram не мигал белым. Здесь она применяется ещё раз:
// разметку рисует уже этот код, и расходиться им нельзя.
// Прокрутка пальцем не должна считаться нажатием: без этого палец,
// ведущий главную вверх, «сам собой» открывал ленту — под ним там
// карточка, а WebView прощает смещение и всё равно шлёт click.
guardTaps();

const theme = resolveTheme();
applyTheme();
syncChrome(theme);
// Пока тема «как в Telegram», переключение в самом Telegram меняет и
// приложение — на ходу, не закрывая его. Выбранную руками не трогаем.
initTelegram(theme, () => {
  if (settings.theme !== 'auto') return;
  applyTheme();
  syncChrome(resolveTheme());
});

register('home', home);
register('schedule', schedule);
register('news', feed);              // вкладка «Новости» — живая лента
register('newsArchive', newsArchive); // архив из data/app.json
register('moderation', moderationScreen);
register('useful', useful);
register('teachers', directory);
register('teacher', teacherScreen);
register('room', roomScreen);
register('score', scoreScreen);
register('convert', convertScreen);
register('glossary', glossaryScreen);
register('contacts', contactsScreen);
register('dates', datesScreen);
register('chats', chatsScreen);
register('curators', curatorsScreen);
register('help', help);
register('tasks', tasks);
register('adminDays', adminDays);
register('adminDay', dayScreen);
register('article', articleScreen);
register('clubs', clubs);
register('club', clubScreen);
register('campus', campus);
register('campusItem', campusItemScreen);
register('institutes', institutes);
register('institute', instituteScreen);
register('profile', profile);
register('about', about);
register('search', search);
register('links', links);
register('support', support);
register('admin', admin);
register('adminUser', adminUserScreen);

const app = document.getElementById('app');
const nav = document.getElementById('nav');

const blockedScreen = () => `
  <div class="screen">
    <div class="empty-state">
      <div style="font-size:34px">🚪</div>
      <div style="font-weight:700;color:var(--text)">Доступ закрыт</div>
      <div style="max-width:280px">
        Приложение отключено для этого аккаунта. Если это ошибка — напишите
        автору в поддержку.
      </div>
    </div>
  </div>`;

/**
 * Группа знает два дома: localStorage приложения и база бота. Своя — та,
 * что выбрана здесь; серверную берём, только когда локальной ещё нет —
 * иначе выбор в приложении откатывался бы к старому значению из бота.
 */
function syncSettings() {
  if (settings.group) syncGroup(settings.group);
  else if (account.group) save({ group: account.group });
}

// Сервер спрашиваем сразу, но первый экран его не ждёт.
const whoAmI = loadMe();

/**
 * Запуск.
 *
 * Раньше приложение ждало и свои данные, и ответ сервера бота. Данные
 * лежат рядом и приходят быстро, а сервер — на бесплатном тарифе, и
 * после выкладки он полминуты поднимается: всё это время человек
 * смотрел на спиннер ради прав, которые на первом экране не нужны.
 *
 * Теперь ждём только `data/app.json`, а сервер догоняет: он приносит
 * права, группу из бота и признак блокировки — всё, чему можно
 * появиться секундой позже.
 *
 * И сам `app.json` больше не решает, откроется ли приложение: не
 * приехал — берётся вчерашняя копия, нет копии — работаем без
 * справочника. Расписание живёт на miet.ru и к этому файлу отношения
 * не имеет, а человек видел «Данные не загрузились» вместо своих пар.
 */
loadData()
  .then(() => {
    initRouter(app, nav);
    switchTab('home');
    return whoAmI;
  })
  .then(() => {
    if (account.blocked) {
      app.innerHTML = blockedScreen();
      nav.hidden = true;
      return;
    }
    track('open');
    // Группа могла приехать из бота, пока рисовалась главная: без неё
    // экран показывает «выбери группу», и оставлять его так нельзя.
    const had = settings.group;
    syncSettings();
    if (!had && settings.group) refresh();
  })
  .catch(err => {
    // Сюда попадаем, только если сломался сам запуск: справочник своё
    // отсутствие переживает молча.
    console.error(err);
    app.innerHTML = `
      <div class="screen">
        <div class="empty-state">
          <div style="font-size:34px">📡</div>
          <div style="font-weight:700;color:var(--text)">Приложение не открылось</div>
          <div style="max-width:280px">${err.message}</div>
          <div style="font-size:13px;margin-top:6px">
            Попробуй закрыть и открыть заново.
          </div>
        </div>
      </div>`;
  });

return {};
})();

window.__mietBooted = true;
