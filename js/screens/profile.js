// Профиль: группа, тема, поправка недели, избранное, обслуживание кеша.

import { icon } from '../icons.js';
import { esc, listCard, listRow, toast, sheet, emptyState } from '../ui.js';
import { data, settings, save, applyTheme } from '../store.js';
import { fetchSchedule, weekOfCycle } from '../schedule.js';
import { go, refresh } from '../router.js';
import { tgUser, openLink, syncChrome, haptic, confirmDialog } from '../tg.js';
import { screen, pickGroup } from './common.js';

export default async function profileScreen() {
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
        ? `<img class="avatar-lg" src="${esc(user.photo_url)}" alt="">`
        : `<div class="avatar-lg">${esc(initials)}</div>`}
        <div style="min-width:0">
          <div style="font-size:22px;font-weight:800;letter-spacing:-.02em">${esc(name)}</div>
          <div class="row-subtitle">${user?.username ? '@' + esc(user.username) : 'НИУ МИЭТ'}</div>
        </div>
      </div>

      <div class="section-head" style="margin-top:0"><div class="section-title">Учёба</div></div>
      ${listCard([
      listRow({ ico: 'users', title: 'Группа', value: settings.group || 'не выбрана', chevron: true, id: 'group', cls: 'tap' }),
      listRow({ ico: 'calendar', title: 'Текущая неделя', value: weekLabel, chevron: true, id: 'week', cls: 'tap' }),
      listRow({ ico: 'heart', title: 'Избранные кружки', value: String(favCount), chevron: true, id: 'fav', cls: 'tap' }),
    ])}

      <div class="section-head"><div class="section-title">Оформление</div></div>
      <div class="card" style="padding:14px 16px">
        <div class="field-label" style="margin-bottom:9px">Тема</div>
        <div class="segmented" id="theme">
          <button class="segmented-item ${settings.theme === 'light' ? 'active' : ''}" data-theme="light">Светлая</button>
          <button class="segmented-item ${settings.theme === 'dark' ? 'active' : ''}" data-theme="dark">Тёмная</button>
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
        Новости и справочная информация собраны ${esc(data.meta?.generated || '')}.
      </div>`,
  });

  node.querySelector('#theme').addEventListener('click', e => {
    const b = e.target.closest('[data-theme]');
    if (!b) return;
    const theme = b.dataset.theme;
    save({ theme });
    applyTheme(theme);
    syncChrome(theme);
    haptic('light');
    node.querySelectorAll('#theme .segmented-item').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
  });

  node.addEventListener('click', async e => {
    const row = e.target.closest('.list-row[data-id]');
    if (!row) return;
    switch (row.dataset.id) {
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
