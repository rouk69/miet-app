// Расписание. Данные берутся живьём с miet.ru — эндпоинт отдаёт
// Access-Control-Allow-Origin: *, поэтому запрос идёт прямо из браузера,
// без своего бэкенда. Ответ кладём в localStorage на сутки.

const API = 'https://miet.ru/schedule/data';
const CACHE_KEY = g => `miet-sched:${g}`;
const TTL = 24 * 60 * 60 * 1000;

export const DAY_NAMES = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
export const DAY_SHORT = ['', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

/** Ставит дату на понедельник её недели (воскресенье относим к прошедшей). */
export function mondayOf(date) {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const shift = (d.getDay() + 6) % 7;   // Пн=0 … Вс=6
  d.setDate(d.getDate() - shift);
  return d;
}

/**
 * Начало семестра по строке вида «Осенний семестр 2026/2027».
 * Осенний считаем с 1 сентября, весенний — с 9 февраля.
 */
export function semesterStart(semestr) {
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
export function weekOfCycle(date, semestr, shift = 0) {
  const start = mondayOf(semesterStart(semestr));
  const cur = mondayOf(date);
  const weeks = Math.round((cur - start) / (7 * 86400000));
  return (((weeks + shift) % 4) + 4) % 4;
}

/** Разбирает «[ФТД] [ДСТ] Быстрые алгоритмы [Лек]» на части. */
export function parseSubject(raw) {
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
export function shortSemestr(s) {
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

/** Загружает расписание группы. force=true обходит кеш. */
export async function fetchSchedule(group, { force = false } = {}) {
  const key = CACHE_KEY(group);
  if (!force) {
    try {
      const hit = JSON.parse(localStorage.getItem(key) || 'null');
      if (hit && Date.now() - hit.at < TTL) return { ...hit.data, cached: true };
    } catch { /* битый кеш — просто перезапросим */ }
  }
  const url = `${API}?group=${encodeURIComponent(group)}`;
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Расписание недоступно (${res.status})`);
  const data = normalize(await res.json());
  try {
    localStorage.setItem(key, JSON.stringify({ at: Date.now(), data }));
  } catch { /* переполнение хранилища — работаем без кеша */ }
  return { ...data, cached: false };
}

/** Все записи расписания на конкретный день конкретной недели цикла. */
export const lessonsOf = (sched, week, day) =>
  (sched?.lessons || []).filter(l => l.week === week && l.day === day);

/**
 * Пары дня — по одной на слот звонков.
 *
 * В одном слоте у группы может стоять несколько занятий: язык и
 * физкультура делятся на подгруппы, и МИЭТ отдаёт их отдельными записями
 * с одинаковым временем. Без сборки они выглядели бы как две пары подряд
 * с одним и тем же временем, а счётчик показывал бы на одну больше.
 */
export function slotsOf(sched, week, day) {
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

/** Сколько пар в каждый день выбранной недели — для точек под датами. */
export function dayCounts(sched, week) {
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
export function nowState(sched, week, now = new Date()) {
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
export function weekDates(base = new Date()) {
  const mon = mondayOf(base);
  return Array.from({ length: 6 }, (_, i) => {
    const d = new Date(mon);
    d.setDate(mon.getDate() + i);
    return d;
  });
}
