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

import { esc } from './ui.js';

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
export function art(name, size = 96, cls = '') {
  const body = S[name] || S.empty;
  return `<svg class="art ${cls}" width="${size}" height="${size}"
    viewBox="0 0 100 100" fill="none" stroke="currentColor"
    stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${body}</svg>`;
}

export const hasArt = name => Object.hasOwn(S, name);
export const artNames = Object.keys(S);

/** Пустое состояние с иллюстрацией — для экранов, а не для строк списка. */
export const artState = (name, title, note = '') => `
  <div class="art-state">
    ${art(name, 104)}
    <div class="art-title">${esc(title)}</div>
    ${note ? `<div class="art-note">${esc(note)}</div>` : ''}
  </div>`;
