// Поддержка: кто сделал приложение и куда писать, если что-то не так.

import { icon } from '../icons.js';
import { esc, listCard, listRow } from '../ui.js';
import { data } from '../store.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

export const OWNER = 'xxxddsm';

export default async function supportScreen() {
  const meta = data.meta || {};

  const node = screen({
    title: 'Поддержка',
    subtitle: 'Приложение сделано студентом для студентов',
    small: true,
    body: `
      <div class="card owner-card">
        <div class="owner-avatar">${icon('user', 30)}</div>
        <div style="min-width:0">
          <div class="owner-name">@${esc(OWNER)}</div>
          <div class="row-subtitle">Автор и поддержка</div>
        </div>
      </div>

      <div style="margin-top:14px">
        <button class="btn-primary" id="write">
          ${icon('messageCircle', 18)} Написать в Telegram
        </button>
      </div>

      <div class="section-head"><div class="section-title">Что писать</div></div>
      ${listCard([
      listRow({ ico: 'info', title: 'Расписание показывает не то', sub: 'Проверь поправку недели в профиле — цикл мог сдвинуться' }),
      listRow({ ico: 'refresh', title: 'Данные устарели', sub: 'Новости и разделы обновляются вручную, напомни' }),
      listRow({ ico: 'sparkles', title: 'Хочется новой функции', sub: 'Предлагай — приложение делается для вас' }),
    ])}

      <div class="section-head"><div class="section-title">Об источниках</div></div>
      ${listCard([
      listRow({ ico: 'calendar', title: 'Расписание', sub: 'Тянется с miet.ru при каждом открытии', value: 'живое' }),
      listRow({ ico: 'news', title: 'Новости и разделы', sub: `Собраны ${esc(meta.generated || '—')}` }),
      listRow({ ico: 'globe', title: 'Источник', sub: 'miet.ru', chevron: true, id: 'site', cls: 'tap' }),
    ])}

      <div class="fab-note">
        Приложение неофициальное. Вся информация и фотографии принадлежат
        НИУ МИЭТ.
      </div>`,
  });

  const write = () => openLink(`https://t.me/${OWNER}`);
  node.querySelector('#write').addEventListener('click', write);
  node.addEventListener('click', e => {
    const row = e.target.closest('.list-row[data-id="site"]');
    if (row) openLink('https://www.miet.ru');
  });
  return node;
}
