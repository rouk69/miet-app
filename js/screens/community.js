// Чаты, сообщества и кураторы.
//
// Все ссылки здесь проверены вручную: открыты, подтверждены как
// официальные (по описанию канала) и записаны с указанием, откуда взяты.
// Выдуманная ссылка в таком разделе хуже, чем его отсутствие: человек
// уйдёт по ней в чужой чат и решит, что это университетский.
//
// Сообщества конкретных кружков не дублируются: они уже лежат в карточке
// каждого кружка вместе с контактами руководителя.

import { icon } from '../icons.js';
import { esc } from '../ui.js';
import { data } from '../store.js';
import { go } from '../router.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

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

export async function chatsScreen() {
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

export async function curatorsScreen() {
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
