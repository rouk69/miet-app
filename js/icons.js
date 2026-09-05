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

  // ── расписание ──
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.2l3.2 2"/>',
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
  map: '<path d="m9 4 6 2.5L20.4 4a.6.6 0 0 1 .9.5v12.9a.6.6 0 0 1-.4.6L15 20l-6-2.5-5.4 2.5a.6.6 0 0 1-.9-.5V6.6a.6.6 0 0 1 .4-.6L9 4Z"/><path d="M9 4v13.5M15 6.5V20"/>',
};

/** Возвращает разметку иконки. size — в px, cls — дополнительный класс. */
export function icon(name, size = 22, cls = '') {
  const body = P[name] || P.info;
  return `<svg class="${cls}" width="${size}" height="${size}" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="1.75"
    stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${body}</svg>`;
}

export const hasIcon = name => Object.hasOwn(P, name);
export const iconNames = Object.keys(P);
