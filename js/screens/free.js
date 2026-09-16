// Свободные аудитории: где сесть с ноутбуком, доделать лабу, собраться
// впятером перед защитой.
//
// Экран отвечает на вопрос «куда идти прямо сейчас», поэтому открывается
// на текущем слоте звонков и текущем дне — без единого нажатия. Выбор
// дня и пары есть, но он второй: планируют реже, чем ищут место сейчас.
//
// Честность важнее полноты. «Свободна» здесь значит ровно одно: в ней
// нет пары по расписанию. Открыта ли дверь, не идёт ли там пересдача или
// собрание кружка — расписание не знает, и экран говорит это прямо.
// Обещание, из-за которого человек привёл группу и уткнулся в замок,
// хуже отсутствующего раздела.

import { icon } from '../icons.js';
import { esc, emptyState, pillRow, bindChoice, skeleton, toast } from '../ui.js';
import { get } from '../api.js';
import { settings } from '../store.js';
import { artState } from '../art.js';
import { screen } from './common.js';
import { go } from '../router.js';
import { haptic } from '../tg.js';
import { fetchSchedule, weekOfCycle, DAY_SHORT, DAY_NAMES } from '../schedule.js';

// Слоты звонков МИЭТ. Время нужно до первого ответа сервера: экран
// открывается на «сейчас», и вычислить текущую пару надо ещё до запроса.
// Тот же список лежит у бота (`schedule_api`) — меняются вместе.
export const BELLS = [
  { pair: 1, from: '9:00', to: '10:30' },
  { pair: 2, from: '10:40', to: '12:10' },
  { pair: 3, from: '12:20', to: '13:50' },
  { pair: 4, from: '14:20', to: '15:50' },
  { pair: 5, from: '16:00', to: '17:30' },
  { pair: 6, from: '17:40', to: '19:10' },
  { pair: 7, from: '19:20', to: '20:50' },
  { pair: 8, from: '21:00', to: '22:30' },
];

const mins = t => {
  const [h, m] = String(t || '0:0').split(':').map(Number);
  return h * 60 + m;
};

/**
 * Какую пару показывать при открытии.
 *
 * Идёт пара — её. Перерыв — следующую: сидеть между парами негде именно
 * потому, что все аудитории сейчас пустуют, и полезен как раз следующий
 * слот. После последней пары или до начала дня — первую: планировать с
 * конца дня бессмысленно.
 */
export function pairNow(now = new Date()) {
  const m = now.getHours() * 60 + now.getMinutes();
  for (const b of BELLS) {
    if (m < mins(b.from)) return b.pair;
    if (m < mins(b.to)) return b.pair;
  }
  return 1;
}

/** День недели в номерах расписания: 1 — понедельник, 7 — воскресенье. */
export const dayNow = (now = new Date()) => ((now.getDay() + 6) % 7) + 1;

/**
 * Аудитории одного корпуса вместе: номер начинается с его цифры.
 *
 * Подпись нейтральная («3xxx»), а не «третий корпус»: нумерация МИЭТ
 * нигде не описана, и выдумывать ей смысл — значит уверенно наврать.
 * Группировка всё равно помогает: в списке из двухсот номеров подряд не
 * найти ничего.
 */
export function byBlock(free) {
  const groups = new Map();
  for (const room of free) {
    const head = /^\d/.test(room.name) ? `${room.name[0]}xxx` : 'Другие';
    if (!groups.has(head)) groups.set(head, []);
    groups.get(head).push(room);
  }
  return [...groups.entries()]
    .sort((a, b) => (a[0] === 'Другие') - (b[0] === 'Другие')
      || a[0].localeCompare(b[0], 'ru'));
}

/** «Свободна до 14:20» или «до конца дня» — то, что реально спрашивают. */
export function untilText(room) {
  if (!room.until_pair) return 'до конца дня';
  return room.until_time ? `до ${room.until_time}` : `до ${room.until_pair}-й пары`;
}

const roomCard = r => `
  <button class="free-room" data-room="${esc(r.name)}">
    <span class="free-room-name">${esc(r.name)}</span>
    <span class="free-room-until">${esc(untilText(r))}</span>
  </button>`;

export default async function freeRoomsScreen(params = {}) {
  const now = new Date();
  let day = params.day || dayNow(now);
  // Воскресенье в расписании пустое, и список «всё свободно» бесполезен.
  if (day > 6) day = 1;
  let pair = params.pair || pairNow(now);
  let query = '';

  const node = screen({
    title: 'Свободные аудитории',
    subtitle: 'Где никого нет по расписанию',
    body: `
      <div class="free-pick">
        <div class="week-strip" id="fdays">
          ${[1, 2, 3, 4, 5, 6].map(d => `
            <button class="week-day ${d === day ? 'active' : ''} ${d === dayNow(now) ? 'today' : ''}"
                    data-fday="${d}">
              <span class="week-day-name">${DAY_SHORT[d]}</span>
            </button>`).join('')}
        </div>
        ${pillRow(BELLS.map(b => ({ id: String(b.pair), label: `${b.pair} · ${b.from}` })),
    String(pair), 'fpair')}
      </div>
      <div class="search-box" style="margin-top:12px">
        ${icon('search', 19, 'muted')}
        <input id="fq" type="search" placeholder="Номер аудитории"
               autocomplete="off" enterkeyhint="search" spellcheck="false">
      </div>
      <div id="fbody" style="margin-top:14px">${skeleton(120)}</div>`,
  });

  const body = node.querySelector('#fbody');
  let data = null;

  const draw = () => {
    if (!data) return;
    const needle = query.trim().toLowerCase();
    const free = needle
      ? data.free.filter(r => r.name.toLowerCase().includes(needle))
      : data.free;

    if (!data.total) {
      // Индекс собирается раз в сутки и через пять минут после старта
      // контейнера: пустой он не «сломан», а ещё не построен.
      body.innerHTML = artState('offline', 'Расписание вуза ещё не собрано',
        'Бот обходит все 346 групп раз в сутки. Загляни через десять минут');
      return;
    }
    if (!free.length) {
      body.innerHTML = emptyState(needle
        ? 'Такой аудитории нет или она занята'
        : 'В этот слот свободных аудиторий не нашлось', 'door');
      return;
    }

    const slot = BELLS.find(b => b.pair === pair);
    body.innerHTML = `
      <div class="free-head">
        <div>
          <div class="free-head-title">${DAY_NAMES[day]}, ${pair}-я пара</div>
          <div class="free-head-note">
            ${esc(slot ? `${slot.from}–${slot.to}` : '')} ·
            ${weekKnown ? `${week + 1}-я неделя цикла · ` : ''}свободно
            ${free.length} из ${data.total}
          </div>
        </div>
        <div class="free-head-num">${free.length}</div>
      </div>
      ${byBlock(free).map(([head, list]) => `
        <div class="section-head"><div class="section-title">${esc(head)}</div>
          <span class="section-link">${list.length}</span></div>
        <div class="free-grid">${list.map(roomCard).join('')}</div>`).join('')}
      <p class="free-fineprint">
        «Свободна» значит, что в ней нет пары по расписанию. Пересдачи,
        консультации и собрания кружков в расписание не попадают, а дверь
        может быть просто закрыта.
      </p>`;
  };

  // Неделя цикла нужна, чтобы спросить верный слот, а знает семестр
  // только расписание. Берём его у своей группы — оно почти всегда уже
  // в кеше, его грузила главная. Нет группы — считаем первую неделю и
  // честно пишем об этом в подписи.
  let week = 0;
  let weekKnown = false;
  const findWeek = async () => {
    if (weekKnown || !settings.group) return;
    try {
      const sched = await fetchSchedule(settings.group);
      week = weekOfCycle(now, sched.semestr, settings.weekShift);
      weekKnown = true;
    } catch { /* без расписания остаёмся на первой неделе */ }
  };

  const load = async () => {
    body.innerHTML = skeleton(120);
    await findWeek();
    try {
      data = await get(`/api/directory/free?week=${week}&day=${day}&pair=${pair}`);
      draw();
    } catch (err) {
      body.innerHTML = emptyState(err.message, 'door');
    }
  };

  node.querySelector('#fdays').addEventListener('click', e => {
    const b = e.target.closest('[data-fday]');
    if (!b) return;
    day = +b.dataset.fday;
    node.querySelectorAll('[data-fday]').forEach(x =>
      x.classList.toggle('active', +x.dataset.fday === day));
    haptic('light');
    load();
  });

  bindChoice(node, 'fpair', id => { pair = +id; load(); });

  node.querySelector('#fq').addEventListener('input', e => {
    query = e.target.value;
    draw();
  });

  node.addEventListener('click', e => {
    const b = e.target.closest('[data-room]');
    if (!b) return;
    haptic('light');
    // Карточка аудитории уже есть в справочнике — там весь её день, а не
    // одна пара. Второй такой экран был бы тем же самым.
    go('room', { name: b.dataset.room });
  });

  load();
  return node;
}
