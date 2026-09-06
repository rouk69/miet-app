// Точка входа: тема → Telegram → данные → роутер.

import { initTelegram, syncChrome } from './tg.js';
import { loadData, settings, save, applyTheme } from './store.js';
import { register, init as initRouter, switchTab } from './router.js';
import { loadMe, account, track, syncGroup } from './api.js';

import home from './screens/home.js';
import schedule from './screens/schedule.js';
import newsArchive, { articleScreen } from './screens/news.js';
import feed, { moderationScreen } from './screens/feed.js';
import clubs, { clubScreen } from './screens/clubs.js';
import campus, { campusItemScreen } from './screens/campus.js';
import institutes, { instituteScreen } from './screens/institutes.js';
import profile from './screens/profile.js';
import about from './screens/about.js';
import search from './screens/search.js';
import links from './screens/links.js';
import support from './screens/support.js';
import admin, { adminUserScreen } from './screens/admin.js';

applyTheme(settings.theme);
initTelegram(settings.theme);
syncChrome(settings.theme);

register('home', home);
register('schedule', schedule);
register('news', feed);              // вкладка «Новости» — живая лента
register('newsArchive', newsArchive); // архив из data/app.json
register('moderation', moderationScreen);
register('article', articleScreen);
register('clubs', clubs);
register('club', clubScreen);
register('campus', campus);
register('campusItem', campusItemScreen);
register('institutes', institutes);
register('institute', instituteScreen);
register('profile', profile);
register('about', about);
register('search', search);
register('links', links);
register('support', support);
register('admin', admin);
register('adminUser', adminUserScreen);

const app = document.getElementById('app');
const nav = document.getElementById('nav');

const blockedScreen = () => `
  <div class="screen">
    <div class="empty-state">
      <div style="font-size:34px">🚪</div>
      <div style="font-weight:700;color:var(--text)">Доступ закрыт</div>
      <div style="max-width:280px">
        Приложение отключено для этого аккаунта. Если это ошибка — напишите
        автору в поддержку.
      </div>
    </div>
  </div>`;

/**
 * Группа знает два дома: localStorage приложения и база бота. Своя — та,
 * что выбрана здесь; серверную берём, только когда локальной ещё нет —
 * иначе выбор в приложении откатывался бы к старому значению из бота.
 */
function syncSettings() {
  if (settings.group) syncGroup(settings.group);
  else if (account.group) save({ group: account.group });
}

Promise.all([loadData(), loadMe()])
  .then(() => {
    if (account.blocked) {
      app.innerHTML = blockedScreen();
      return;
    }
    syncSettings();
    track('open');
    initRouter(app, nav);
    switchTab('home');
  })
  .catch(err => {
    console.error(err);
    app.innerHTML = `
      <div class="screen">
        <div class="empty-state">
          <div style="font-size:34px">📡</div>
          <div style="font-weight:700;color:var(--text)">Данные не загрузились</div>
          <div style="max-width:280px">${err.message}</div>
          <div style="font-size:13px;margin-top:6px">
            Открой приложение через веб-сервер, а не файлом с диска.
          </div>
        </div>
      </div>`;
  });
