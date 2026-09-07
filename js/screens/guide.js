// Справочные экраны: словарь первокурсника, контакты и ключевые даты.
//
// Всё, что здесь написано про МИЭТ, взято из данных приложения или из
// расписания. Там, где точной информации нет — сроки сессии, правила
// конкретной кафедры, — стоит ссылка на официальный источник, а не
// придуманная дата: неверная дата хуже её отсутствия.

import { icon } from '../icons.js';
import { esc, emptyState } from '../ui.js';
import { data, settings } from '../store.js';
import { fetchSchedule, weekOfCycle, semesterStart } from '../schedule.js';
import { go } from '../router.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

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

export async function glossaryScreen() {
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

export async function contactsScreen() {
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

export async function datesScreen() {
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
