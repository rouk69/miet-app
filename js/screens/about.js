// О университете: факты, описание, реквизиты и контакты.

import { icon } from '../icons.js';
import { esc, listCard, listRow, contactRows } from '../ui.js';
import { data } from '../store.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

export default async function aboutScreen() {
  const u = data.university || {};
  const paragraphs = (u.about || '').split(/\n{2,}/).map(p => p.trim()).filter(Boolean);

  const node = screen({
    title: u.short || 'МИЭТ',
    subtitle: u.name,
    small: true,
    body: `
      <div class="kpi-grid" style="margin-bottom:18px">
        ${(u.facts || []).map(f => `
          <div class="kpi-tile">
            <div class="kpi-number">${esc(f.k)}</div>
            <div class="kpi-label">${esc(f.v)}</div>
          </div>`).join('')}
      </div>

      ${paragraphs.length ? `<div class="article-text" style="font-size:15px">
        ${paragraphs.map(p => `<p>${esc(p)}</p>`).join('')}
      </div>` : ''}

      <div class="section-head"><div class="section-title">Контакты</div></div>
      ${contactRows({ phone: u.phone, email: u.email, address: u.address })}

      <div class="section-head"><div class="section-title">Реквизиты</div></div>
      ${listCard([
      listRow({ title: 'Полное наименование', sub: u.full }),
      listRow({ title: 'Дата создания', value: u.founded }),
    ])}

      <div class="section-head"><div class="section-title">Ссылки</div></div>
      ${listCard([
      listRow({ ico: 'globe', title: 'miet.ru', sub: 'Официальный сайт', chevron: true, id: 'https://www.miet.ru', cls: 'tap' }),
      listRow({ ico: 'calendar', title: 'Расписание занятий', sub: 'miet.ru/schedule', chevron: true, id: 'https://miet.ru/schedule', cls: 'tap' }),
      listRow({ ico: 'news', title: 'Новости', sub: 'miet.ru/news', chevron: true, id: 'https://www.miet.ru/news/', cls: 'tap' }),
      listRow({ ico: 'clipboard', title: 'Сведения об образовательной организации', chevron: true, id: 'https://miet.ru/sveden/', cls: 'tap' }),
      listRow({ ico: 'key', title: 'Личный кабинет', sub: 'account.miet.ru', chevron: true, id: 'https://account.miet.ru/', cls: 'tap' }),
    ])}

      <div class="fab-note">
        Неофициальное приложение. Вся информация — с miet.ru.
      </div>`,
  });

  node.addEventListener('click', e => {
    const row = e.target.closest('.list-row[data-id^="http"]');
    if (row) openLink(row.dataset.id);
  });
  void icon;
  return node;
}
