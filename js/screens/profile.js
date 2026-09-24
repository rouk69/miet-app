// Профиль: группа, тема, поправка недели, избранное, обслуживание кеша.

import { icon } from '../icons.js';
import { esc, listCard, listRow, toast, sheet, emptyState, toggle, SHORTCUT_STEPS, stepsHtml } from '../ui.js';
import { data, settings, save, applyTheme, resolveTheme } from '../store.js';
import { BUILD } from '../config.js';
import { fetchSchedule, weekOfCycle, weekName, setLunch } from '../schedule.js';
import { go, refresh } from '../router.js';
import { tgUser, openLink, syncChrome, haptic, hapticNotify, confirmDialog,
  canAddToHome, addToHome, homeStatus, onHomeAdded }
  from '../tg.js';
import { account, canTalk, post } from '../api.js';
import { screen, pickGroup } from './common.js';

export default async function profileScreen() {
  const user = tgUser();
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || 'Студент МИЭТ';
  const initials = (user?.first_name?.[0] || 'М') + (user?.last_name?.[0] || '');
  const favCount = settings.favorites.length;

  // Есть ли ярлык на рабочем столе — клиент отвечает быстро или никак
  // (тогда через полторы секунды считаем «неизвестно»).
  const home = await homeStatus();

  let weekLabel = '—';
  let baseWeek = null;   // неделя цикла без поправки — от неё считает окно поправки
  if (settings.group) {
    try {
      const s = await fetchSchedule(settings.group);
      baseWeek = weekOfCycle(new Date(), s.semestr, 0);
      weekLabel = weekName(baseWeek + settings.weekShift);
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
      ...(settings.group ? [listRow({ ico: 'utensils', title: 'Обед группы', value: LUNCH_LABEL[(settings.lunch || {})[settings.group]] || 'не указан',
        chevron: true, id: 'lunch', cls: 'tap' })] : []),
      listRow({ ico: 'heart', title: 'Избранные кружки', value: String(favCount), chevron: true, id: 'fav', cls: 'tap' }),
    ])}

      <div class="section-head"><div class="section-title">Быстрый доступ</div></div>
      ${listCard([listRow({ ico: 'zap', title: 'Ярлык на рабочий стол', sub: 'Открывать приложение в один тап',
    value: home === 'added' ? 'добавлен' : '', chevron: true, id: 'shortcut', cls: 'tap' })])}

      ${canTalk ? `
        <div class="section-head"><div class="section-title">Утро</div></div>
        <div class="list-card">
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">Расписание по утрам</div>
              <div class="row-subtitle">
                В 7:30 бот присылает пары на сегодня: во сколько первая,
                где идут, какие окна. В выходные и дни без пар молчит.
                Отключить можно и кнопкой под самим сообщением.
              </div>
            </div>
            ${toggle(account.morning !== false, 'morning')}
          </div>
        </div>` : ''}

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

  node.querySelector('[data-toggle="morning"]')?.addEventListener('click', async e => {
    const t = e.currentTarget;
    const on = !t.classList.contains('on');
    // Переключаем сразу, откатываем при отказе: ждать ответа сервера,
    // глядя на неподвижный тумблер, незачем.
    t.classList.toggle('on', on);
    haptic('light');
    try {
      await post('/api/morning', { on });
      account.morning = on;
      hapticNotify('success');
    } catch (err) {
      toast(err.message);
      t.classList.toggle('on', !on);
    }
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
      case 'week': return weekShiftSheet(baseWeek);
      case 'lunch': return lunchSheet();
      case 'shortcut': return shortcutSheet(home);
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
/**
 * Ярлык на рабочий стол: кнопка, которая сама открывает окно Telegram,
 * и пошаговая инструкция на случай, если кнопка недоступна (компьютер,
 * старый клиент) или человеку проще руками.
 */
function shortcutSheet(status) {
  const can = canAddToHome() && status !== 'added';
  sheet({
    title: 'Ярлык на рабочий стол',
    cancel: 'Закрыть',
    body: `
      <div class="row-subtitle" style="margin-bottom:14px;line-height:1.5">
        Иконка MIET на рабочем столе телефона открывает приложение сразу —
        без чата с ботом и лишних нажатий.
      </div>
      ${status === 'added' ? `<div class="ok-note">${icon('check', 16)} Ярлык уже на рабочем столе</div>` : ''}
      ${can ? `<button class="btn-primary" id="add-home">${icon('zap', 18)} Добавить ярлык</button>
        <div class="field-label" style="margin:18px 2px 10px">Или вручную</div>` : `
        <div class="field-label" style="margin:4px 2px 10px">Как добавить</div>`}
      ${stepsHtml(SHORTCUT_STEPS)}
      <div class="row-subtitle" style="margin-top:12px;line-height:1.5">
        Это для телефона: на компьютере ярлыков нет. Если такого пункта в меню
        нет — обнови Telegram.
      </div>`,
    onMount(root, close) {
      root.querySelector('#add-home')?.addEventListener('click', () => {
        haptic('medium');
        if (!addToHome()) toast('Не получилось — добавь по шагам ниже');
      });
      onHomeAdded(() => { hapticNotify('success'); toast('Ярлык добавлен'); close(); refresh(); });
    },
  });
}

const LUNCH_LABEL = { after2: 'после 2-й пары', after3: 'после 3-й пары' };

/**
 * Когда у группы обед. От этого зависит только 3-я пара: 12:00–13:20,
 * если обед после неё, и 12:30–13:50, если перед ней. Сайт МИЭТ этого
 * не сообщает, поэтому выбирает человек — для каждой группы отдельно.
 */
function lunchSheet() {
  const cur = (settings.lunch || {})[settings.group] || '';
  const opt = (id, title, sub) => `
    <button class="list-row tap" data-l="${id}" style="width:100%;text-align:left">
      <div class="list-row-body"><div class="row-title">${title}</div><div class="row-subtitle">${sub}</div></div>
      ${cur === id ? icon('check', 20) : ''}
    </button>`;
  sheet({
    title: 'Обед группы',
    body: `
      <div class="row-subtitle" style="margin-bottom:12px;line-height:1.5">
        Обед в МИЭТ — 40 минут: после 2-й пары (11:50) или после 3-й (13:20).
        От этого зависит, во сколько начинается 3-я пара.
      </div>
      <div class="list-card">
        ${opt('after3', 'После 3-й пары', '3-я пара в 12:00–13:20')}
        ${opt('after2', 'После 2-й пары', '3-я пара в 12:30–13:50')}
        ${opt('', 'Не знаю', 'показывать оба времени')}
      </div>`,
    onMount(root, close) {
      root.addEventListener('click', e => {
        const b = e.target.closest('[data-l]');
        if (!b) return;
        setLunch(settings.group, b.dataset.l || null);
        haptic('medium');
        close();
        refresh();
      });
    },
  });
}

function weekShiftSheet(base) {
  // Зная неделю без поправки, спрашиваем по-человечески: «какая неделя
  // сейчас?» — названиями из официального расписания, а не «+1, +2».
  const known = base !== null && base !== undefined;
  sheet({
    title: 'Поправка недели',
    body: `
      <div class="row-subtitle" style="margin-bottom:14px;line-height:1.5">
        ${known
    ? 'Неделя считается от начала семестра. Если в официальном расписании сейчас другая — выбери её.'
    : 'Неделя цикла считается от начала семестра. Если приложение показывает не ту неделю, что деканат, — сдвинь на нужное число.'}
      </div>
      <div class="pill-row" id="shift" style="flex-wrap:wrap">
        ${[0, 1, 2, 3].map(i => {
    // С известной неделей кнопки идут по порядку недель (1-й числитель…),
    // и каждая несёт сдвиг, который к ней приводит.
    const s = known ? (i - base + 4) % 4 : i;
    return `
          <button class="pill ${settings.weekShift === s ? 'active' : ''}" data-shift="${s}">
            ${known ? weekName(i) : s === 0 ? 'без сдвига' : `+${s}`}
          </button>`;
  }).join('')}
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
