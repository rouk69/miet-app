// «Полезное» — оглавление всего, что не расписание и не лента.
//
// Плитки, а не список: у карточки есть место на подпись, и по ней видно,
// что внутри, без открытия. Порядок задан не алфавитом, а частотой
// вопросов первокурсника: сначала «кто ведёт и где», потом «сколько у меня
// баллов», и только потом справочное.

import { icon } from '../icons.js';
import { esc } from '../ui.js';
import { data } from '../store.js';
import { account } from '../api.js';
import { go } from '../router.js';
import { openLink } from '../tg.js';
import { screen, iconBtn } from './common.js';

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
      { id: 'tasks', ico: 'backpack', tone: 'blue', title: 'Учёба',
        sub: 'Что задали, что сдать и файлы из ОРИОКС' },
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
      { id: 'curators', ico: 'handHeart', tone: 'blue', title: 'Кураторы',
        sub: 'Кто ведёт первый курс' },
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
    <span class="tile-ico">${icon(t.ico, 20)}</span>
    <span class="tile-name">${esc(t.title)}</span>
    <span class="tile-note">${esc(typeof t.sub === 'function' ? t.sub(data) : t.sub)}</span>
  </button>`;

export default async function usefulScreen() {
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
          <span class="tile-ico">${icon('shield', 20)}</span>
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
