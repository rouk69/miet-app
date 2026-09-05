// Точка входа: тема → Telegram → данные → роутер.

import { initTelegram, syncChrome } from './tg.js';
import { loadData, settings, applyTheme } from './store.js';
import { register, init as initRouter, switchTab } from './router.js';

import home from './screens/home.js';
import schedule from './screens/schedule.js';
import news, { articleScreen } from './screens/news.js';
import clubs, { clubScreen } from './screens/clubs.js';
import campus, { campusItemScreen } from './screens/campus.js';
import institutes, { instituteScreen } from './screens/institutes.js';
import profile from './screens/profile.js';
import about from './screens/about.js';
import search from './screens/search.js';
import links from './screens/links.js';
import support from './screens/support.js';

applyTheme(settings.theme);
initTelegram(settings.theme);
syncChrome(settings.theme);

register('home', home);
register('schedule', schedule);
register('news', news);
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

const app = document.getElementById('app');
const nav = document.getElementById('nav');

loadData()
  .then(() => {
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
