// Свободные аудитории: где сесть с ноутбуком, доделать лабу, собраться
// впятером перед защитой.
//
// Экран отвечает на один вопрос — «куда идти прямо сейчас», и потому
// открывается на текущем дне и текущей паре, без единого нажатия. Всё
// управление сведено в одну строку-шапку: она же показывает, про какое
// время сейчас речь, и она же открывает выбор другого. Раньше здесь
// стояли три ряда — дни, восемь пар и поиск, — и экран начинался с
// настроек вместо ответа.
//
// Честность важнее полноты. «Свободна» значит ровно одно: в ней нет
// пары по расписанию. Открыта ли дверь, не идёт ли там пересдача или
// собрание кружка — расписание не знает, и экран говорит это прямо.
// Обещание, из-за которого человек привёл группу и уткнулся в замок,
// хуже отсутствующего раздела.

import { icon } from '../icons.js';
import { esc, emptyState, pillRow, bindChoice, skeleton, sheet, listCard,
  listRow } from '../ui.js';
import { get } from '../api.js';
import { settings } from '../store.js';
import { artState } from '../art.js';
import { screen } from './common.js';
import { go } from '../router.js';
import { haptic } from '../tg.js';
import { fetchSchedule, weekOfCycle, weekName, DAY_SHORT, DAY_NAMES } from '../schedule.js';

// Слоты звонков МИЭТ. Время нужно до первого ответа сервера: экран
// открывается на «сейчас», и вычислить текущую пару надо ещё до запроса.
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
 * потому, что все аудитории в этот момент пустуют, и полезен как раз
 * следующий слот. Поздно вечером и до начала дня — первую.
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
 * По какой цифре начинается номер. Ею и фильтруем.
 *
 * Раньше список делился заголовками «3xxx», и это ничего не объясняло:
 * что означает первая цифра в нумерации МИЭТ, нигде не написано, а
 * выдуманное «третий корпус» было бы уверенным враньём. Фильтр честнее
 * заголовка: он не обещает смысла, а просто сокращает список до тех
 * номеров, которые человек и так ищет глазами.
 */
export const blockOf = name => (/^\d/.test(name) ? name[0] : '#');

/** Какие фильтры вообще показывать — только те, что есть в ответе. */
export function blocksOf(free) {
  const seen = [...new Set(free.map(r => blockOf(r.name)))];
  return seen.sort((a, b) => (a === '#') - (b === '#') || a.localeCompare(b, 'ru'));
}

/** «до 14:20» или «до конца дня» — то, что реально спрашивают. */
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
  // Воскресенье в расписании пустое, и список «свободно всё» бесполезен.
  if (day > 6) day = 1;
  let pair = params.pair || pairNow(now);
  let block = 'all';
  let query = '';
  let data = null;
  let week = 0;
  let weekKnown = false;

  const node = screen({
    title: 'Свободные аудитории',
    subtitle: 'Где никого нет по расписанию',
    body: '<div id="fbody">' + skeleton(150) + '</div>',
  });
  const body = node.querySelector('#fbody');

  const atNow = () => day === dayNow(now) && pair === pairNow(now);

  /** Шапка: сколько свободно и когда. Она же — кнопка выбора времени. */
  const headCard = free => {
    const slot = BELLS.find(b => b.pair === pair) || {};
    return `
      <button class="free-when" data-act="when">
        <div class="free-when-main">
          <div class="free-when-num">${free.length}</div>
          <div class="free-when-text">
            <div class="free-when-title">
              ${free.length === 1 ? 'аудитория свободна'
    : free.length >= 2 && free.length <= 4 ? 'аудитории свободны' : 'аудиторий свободно'}
            </div>
            <div class="free-when-sub">
              ${atNow() ? 'сейчас' : DAY_NAMES[day]} ·
              ${pair}-я пара ${esc(slot.from || '')}–${esc(slot.to || '')}
              ${weekKnown ? ` · ${weekName(week)}` : ''}
            </div>
          </div>
        </div>
        <span class="free-when-go">${icon('clock', 15)} другое время</span>
      </button>`;
  };

  const draw = () => {
    if (!data) return;
    if (!data.total) {
      // Индекс собирается раз в сутки и через пять минут после старта
      // контейнера: пустой он не «сломан», а ещё не построен.
      body.innerHTML = artState('offline', 'Расписание вуза ещё не собрано',
        'Бот обходит все 346 групп раз в сутки. Загляни через десять минут');
      return;
    }

    const needle = query.trim().toLowerCase();
    const all = data.free;
    const shown = all.filter(r =>
      (block === 'all' || blockOf(r.name) === block)
      && (!needle || r.name.toLowerCase().includes(needle)));
    const blocks = blocksOf(all);

    body.innerHTML = `
      ${headCard(all)}
      ${blocks.length > 1 ? pillRow(
    [{ id: 'all', label: 'Все' },
      ...blocks.map(b => ({ id: b, label: b === '#' ? 'Прочие' : `${b}…` }))],
    block, 'fblock') : ''}
      <div class="search-box" style="margin-top:10px">
        ${icon('search', 19, 'muted')}
        <input id="fq" type="search" placeholder="Номер аудитории" value="${esc(query)}"
               autocomplete="off" enterkeyhint="search" spellcheck="false">
      </div>
      <div class="free-grid" id="fgrid">${shown.map(roomCard).join('')}</div>
      ${shown.length ? '' : emptyState(needle
    ? 'Такой аудитории нет или она занята'
    : 'В этот слот здесь всё занято', 'door')}
      <p class="free-fineprint">
        «Свободна» значит, что в ней нет пары по расписанию. Пересдачи,
        консультации и собрания кружков в расписание не попадают, а дверь
        может быть просто закрыта.
      </p>`;

    bindChoice(node, 'fblock', id => { block = id; draw(); });
    const input = body.querySelector('#fq');
    input.addEventListener('input', e => {
      query = e.target.value;
      // Перерисовываем только сетку: полная перерисовка забирала бы
      // фокус у поля на каждой букве.
      const list = data.free.filter(r =>
        (block === 'all' || blockOf(r.name) === block)
        && r.name.toLowerCase().includes(query.trim().toLowerCase()));
      body.querySelector('#fgrid').innerHTML = list.map(roomCard).join('');
    });
  };

  // Неделя цикла нужна, чтобы спросить верный слот, а семестр знает
  // только расписание. Берём его у своей группы — оно почти всегда уже
  // в кеше, его грузила главная.
  const findWeek = async () => {
    if (weekKnown || !settings.group) return;
    try {
      const sched = await fetchSchedule(settings.group);
      week = weekOfCycle(now, sched.semestr, settings.weekShift);
      weekKnown = true;
    } catch { /* без расписания остаёмся на первой неделе */ }
  };

  const load = async () => {
    body.innerHTML = skeleton(150);
    await findWeek();
    try {
      data = await get(`/api/directory/free?week=${week}&day=${day}&pair=${pair}`);
      draw();
    } catch (err) {
      body.innerHTML = emptyState(err.message, 'door');
    }
  };

  /** Выбор дня и пары — в шторке, а не рядами на экране. */
  const pickWhen = () => {
    sheet({
      title: 'Когда',
      body: `
        <div class="week-strip" id="wdays">
          ${[1, 2, 3, 4, 5, 6].map(d => `
            <button class="week-day ${d === day ? 'active' : ''} ${d === dayNow(now) ? 'today' : ''}"
                    data-wday="${d}">
              <span class="week-day-name">${DAY_SHORT[d]}</span>
            </button>`).join('')}
        </div>
        <div class="sheet-list" style="margin-top:12px">
          ${listCard(BELLS.map(b => listRow({
    title: `${b.pair}-я пара`,
    sub: `${b.from}–${b.to}`,
    id: String(b.pair),
    cls: 'tap',
    value: b.pair === pair ? '✓' : '',
  })))}
        </div>`,
      onMount(root, close) {
        root.querySelector('#wdays').addEventListener('click', e => {
          const b = e.target.closest('[data-wday]');
          if (!b) return;
          day = +b.dataset.wday;
          root.querySelectorAll('[data-wday]').forEach(x =>
            x.classList.toggle('active', +x.dataset.wday === day));
          haptic('light');
          // Грузим сразу, не дожидаясь выбора пары: иначе человек,
          // сменивший день и закрывший шторку, не увидел бы никакой
          // разницы — и решил бы, что кнопка не работает.
          load();
        });
        root.addEventListener('click', e => {
          const row = e.target.closest('[data-id]');
          if (!row) return;
          pair = +row.dataset.id;
          haptic('medium');
          close();
          load();
        });
      },
    });
  };

  node.addEventListener('click', e => {
    if (e.target.closest('[data-act="when"]')) {
      haptic('light');
      pickWhen();
      return;
    }
    const room = e.target.closest('[data-room]');
    if (!room) return;
    haptic('light');
    // Карточка аудитории уже есть в справочнике — там весь её день, а не
    // одна пара. Второй такой экран был бы тем же самым.
    go('room', { name: room.dataset.room });
  });

  load();
  return node;
}
