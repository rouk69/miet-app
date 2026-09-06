// Лента: посты, написанные людьми, и свежие новости с miet.ru.
//
// Экран целиком серверный. Архив новостей, собранный в data/app.json,
// показывается отдельным экраном — он статичен и живёт своей жизнью.
//
// Без сервера (обычный браузер, отладка) лента просто не показывается:
// приложение остаётся рабочим, как и всё остальное здесь.

import { icon } from '../icons.js';
import { esc, emptyState, toast, sheet, lightbox } from '../ui.js';
import { get, post, account, canTalk } from '../api.js';
import { API_BASE } from '../config.js';
import { data, settings } from '../store.js';
import { go, refresh } from '../router.js';
import { haptic, hapticNotify, confirmDialog, openLink } from '../tg.js';
import { screen, pickGroup } from './common.js';

const mediaUrl = name => `${API_BASE}/media/${encodeURIComponent(name)}`;

/** Время с сервера приходит в UTC — без Z браузер прочтёт его как местное. */
const parseTs = ts => new Date(String(ts || '').replace(' ', 'T') + 'Z');

function ago(ts) {
  const min = Math.floor((Date.now() - parseTs(ts).getTime()) / 60000);
  if (min < 1) return 'только что';
  if (min < 60) return `${min} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const d = Math.floor(h / 24);
  if (d === 1) return 'вчера';
  if (d < 7) return `${d} дн назад`;
  return parseTs(ts).toLocaleDateString('ru-RU');
}

/** Абзацы поста. Текст пользовательский, поэтому экранируется весь. */
const paragraphs = text => (text || '')
  .split(/\n{2,}/).map(p => p.trim()).filter(Boolean)
  .map(p => `<p>${esc(p)}</p>`).join('');

// ─────────────── карточка ───────────────

function pollBlock(p) {
  if (!p.poll) return '';
  const voted = p.poll.my_option != null;
  return `
    <div class="poll">
      ${p.poll.options.map(o => `
        <button class="poll-option ${o.id === p.poll.my_option ? 'mine' : ''}"
                data-vote="${o.id}" ${voted ? 'data-voted="1"' : ''}>
          <span class="poll-fill" style="width:${voted ? o.share : 0}%"></span>
          <span class="poll-text">${esc(o.text)}</span>
          <span class="poll-share">${voted ? o.share + '%' : ''}</span>
        </button>`).join('')}
      <div class="poll-total">
        ${p.poll.total ? `${p.poll.total} ${plural(p.poll.total, 'голос', 'голоса', 'голосов')}`
    : 'Голосов пока нет'}
      </div>
    </div>`;
}

const plural = (n, one, few, many) => {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return few;
  return many;
};

function reactionsBlock(p, all) {
  return `
    <div class="reaction-row">
      ${all.map(e => {
    const found = p.reactions.find(r => r.emoji === e);
    const mine = p.my_reaction === e;
    return `<button class="reaction ${mine ? 'mine' : ''}" data-react="${esc(e)}">
              <span>${e}</span>${found ? `<b>${found.count}</b>` : ''}
            </button>`;
  }).join('')}
    </div>`;
}

export function postCard(p, reactions) {
  const closed = p.audience === 'groups';
  return `
    <article class="card post" data-post="${p.id}">
      ${p.pinned ? `<div class="post-flag">${icon('flag', 14)} Закреплено</div>` : ''}
      ${p.media ? `<img class="post-media" src="${mediaUrl(p.media)}" alt=""
                        data-full="${mediaUrl(p.media)}" loading="lazy">` : ''}
      <div class="post-body">
        ${p.title ? `<div class="post-title">${esc(p.title)}</div>` : ''}
        <div class="post-text">${paragraphs(p.text)}</div>
        ${closed ? `<div class="post-audience">${icon('users', 14)}
          Только для: ${p.groups.map(esc).join(', ')}</div>` : ''}
        ${pollBlock(p)}
        ${reactionsBlock(p, reactions)}
        <div class="post-foot">
          <span class="post-author">${esc(p.author_label || 'МИЭТ')}</span>
          <span>·</span>
          <span>${esc(ago(p.published_at))}</span>
          <span class="post-reads">${icon('eye', 14)} ${p.reads}</span>
          ${p.kind === 'news' && p.url
      ? `<button class="post-link" data-open="${esc(p.url)}">на miet.ru</button>` : ''}
          ${(p.mine || account.can_delete || account.can_pin)
      ? `<button class="post-menu" data-menu="${p.id}">${icon('sliders', 16)}</button>` : ''}
        </div>
      </div>
    </article>`;
}

// ─────────────── экран ───────────────

export default async function feedScreen() {
  if (!canTalk) {
    return screen({
      title: 'Лента',
      body: emptyState('Лента работает внутри Telegram', 'inbox'),
    });
  }

  let feed;
  try {
    feed = await get('/api/feed?limit=30');
  } catch (err) {
    return screen({
      title: 'Лента',
      body: `<div class="card" style="padding:18px">
        <div class="row-title" style="margin-bottom:6px">Лента не загрузилась</div>
        <div class="row-subtitle">${esc(err.message)}</div>
      </div>`,
    });
  }

  const archive = (data.news || []).length;
  const node = screen({
    title: 'Лента',
    subtitle: 'Новости университета и объявления',
    body: `
      ${account.can_write ? `
        <button class="btn-primary compose-btn" id="write">
          ${icon('edit', 18)} Написать
        </button>` : ''}
      ${account.can_moderate ? `
        <button class="btn-secondary" id="moderation" style="margin-top:10px">
          Модерация постов
        </button>` : ''}
      <div class="stack" id="list" style="margin-top:14px">
        ${feed.posts.length
    ? feed.posts.map(p => postCard(p, feed.reactions)).join('')
    : emptyState('Пока пусто. Здесь появятся объявления и новости', 'inbox')}
      </div>
      ${archive ? `
        <button class="btn-secondary" id="archive" style="margin-top:14px">
          Архив новостей miet.ru · ${archive}
        </button>` : ''}`,
  });

  const known = new Map(feed.posts.map(p => [p.id, p]));

  node.querySelector('#write')?.addEventListener('click', () => composer());
  node.querySelector('#moderation')?.addEventListener('click', () => go('moderation'));
  node.querySelector('#archive')?.addEventListener('click', () => go('newsArchive'));

  node.addEventListener('click', async e => {
    const card = e.target.closest('[data-post]');
    const id = card && +card.dataset.post;

    const img = e.target.closest('[data-full]');
    if (img) return lightbox(img.dataset.full);

    const link = e.target.closest('[data-open]');
    if (link) return openLink(link.dataset.open);

    const vote = e.target.closest('[data-vote]');
    if (vote) {
      haptic('light');
      try {
        const r = await post(`/api/posts/${id}/vote`, { option: +vote.dataset.vote });
        known.set(id, r.post);
        card.outerHTML = postCard(r.post, feed.reactions);
      } catch (err) { toast(err.message); }
      return;
    }

    const react = e.target.closest('[data-react]');
    if (react) {
      haptic('light');
      try {
        const r = await post(`/api/posts/${id}/react`, { emoji: react.dataset.react });
        known.set(id, r.post);
        card.outerHTML = postCard(r.post, feed.reactions);
      } catch (err) { toast(err.message); }
      return;
    }

    const menu = e.target.closest('[data-menu]');
    if (menu) return cardMenu(known.get(id));
  });

  // Прочтение отмечается, когда карточка действительно побывала на экране:
  // «прочитал» — это увидел, а не «лента загрузилась в фоне».
  watchReads(node, known);
  return node;
}

function watchReads(node, known) {
  if (!('IntersectionObserver' in window)) return;
  const seen = new Set();
  const io = new IntersectionObserver(entries => {
    for (const en of entries) {
      const id = +en.target.dataset.post;
      if (!en.isIntersecting || seen.has(id)) continue;
      const p = known.get(id);
      seen.add(id);
      io.unobserve(en.target);
      if (p && !p.read) post(`/api/posts/${id}/read`, {}).catch(() => { });
    }
  }, { threshold: 0.6 });
  node.querySelectorAll('[data-post]').forEach(el => io.observe(el));
}

async function cardMenu(p) {
  if (!p) return;
  const rows = [];
  if (account.can_pin) rows.push(p.pinned ? 'unpin' : 'pin');
  if (p.mine || account.can_delete) rows.push('delete');
  if (!rows.length) return;

  sheet({
    title: 'Что сделать с постом',
    body: `
      <div class="stack">
        ${rows.includes('pin') ? '<button class="btn-secondary" data-do="pin">Закрепить сверху</button>' : ''}
        ${rows.includes('unpin') ? '<button class="btn-secondary" data-do="unpin">Открепить</button>' : ''}
        ${rows.includes('delete') ? '<button class="btn-secondary danger-btn" data-do="delete">Удалить</button>' : ''}
      </div>`,
    onMount(root, close) {
      root.addEventListener('click', async e => {
        const b = e.target.closest('[data-do]');
        if (!b) return;
        try {
          if (b.dataset.do === 'delete') {
            if (!await confirmDialog('Удалить пост? Это навсегда.')) return;
            await post(`/api/posts/${p.id}/delete`, {});
          } else {
            await post(`/api/posts/${p.id}/pin`, { pinned: b.dataset.do === 'pin' });
          }
          hapticNotify('success');
          close();
          refresh();
        } catch (err) { toast(err.message); }
      });
    },
  });
}

// ─────────────── редактор поста ───────────────

function composer() {
  let groups = [];
  let image = '';
  let anon = false;

  sheet({
    title: 'Новый пост',
    height: '78vh',
    body: `
      <div class="field-group">
        <div class="field-label">Текст</div>
        <textarea class="field-input" id="text" rows="5"
                  placeholder="Что рассказать?"></textarea>
      </div>

      <div class="field-group">
        <div class="field-label">Опрос — по желанию</div>
        <input class="field-input" id="o1" placeholder="Вариант 1">
        <input class="field-input" id="o2" placeholder="Вариант 2" style="margin-top:8px">
        <input class="field-input" id="o3" placeholder="Вариант 3" style="margin-top:8px">
      </div>

      <div class="field-group">
        <div class="field-label">Картинка</div>
        <input type="file" id="file" accept="image/*" class="field-input">
        <div class="row-subtitle" id="imgnote" style="margin-top:6px"></div>
      </div>

      <div class="field-group">
        <div class="field-label">Кому видно</div>
        <div class="list-card">
          <div class="list-row tap" id="pick">
            <div class="list-row-body">
              <div class="row-title">Группы</div>
              <div class="row-subtitle" id="aud">Всем</div>
            </div>
            <span class="chevron">${icon('chevronRight', 18)}</span>
          </div>
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">Анонимно</div>
              <div class="row-subtitle">${account.can_anon
    ? 'Подпись «Анонимно», публикуется сразу'
    : 'Появится в ленте после одобрения'}</div>
            </div>
            <div class="toggle" data-toggle="anon"><div class="toggle-knob"></div></div>
          </div>
        </div>
      </div>

      <button class="btn-primary" id="send">Опубликовать</button>`,
    onMount(root, close) {
      const aud = root.querySelector('#aud');

      root.querySelector('#pick').addEventListener('click', () => {
        pickGroups(groups, picked => {
          groups = picked;
          aud.textContent = groups.length ? groups.join(', ') : 'Всем';
        });
      });

      root.querySelector('[data-toggle="anon"]').addEventListener('click', e => {
        anon = !anon;
        e.currentTarget.classList.toggle('on', anon);
        haptic('light');
      });

      root.querySelector('#file').addEventListener('change', e => {
        const f = e.target.files?.[0];
        const note = root.querySelector('#imgnote');
        if (!f) { image = ''; note.textContent = ''; return; }
        if (f.size > 5 * 1024 * 1024) {
          image = '';
          note.textContent = 'Слишком большая — нужно меньше 5 МБ';
          return;
        }
        const reader = new FileReader();
        reader.onload = () => { image = reader.result; note.textContent = f.name; };
        reader.readAsDataURL(f);
      });

      root.querySelector('#send').addEventListener('click', async () => {
        const text = root.querySelector('#text').value.trim();
        const options = ['o1', 'o2', 'o3']
          .map(id => root.querySelector('#' + id).value.trim()).filter(Boolean);
        if (!text) return toast('Напиши текст');
        if (options.length === 1) return toast('В опросе нужно минимум два варианта');
        const btn = root.querySelector('#send');
        btn.disabled = true;
        btn.textContent = 'Публикую…';
        try {
          const r = await post('/api/posts', { text, options, groups, anon, image });
          hapticNotify('success');
          close();
          toast(r.pending ? 'Отправлено на одобрение' : 'Опубликовано');
          refresh();
        } catch (err) {
          toast(err.message);
          btn.disabled = false;
          btn.textContent = 'Опубликовать';
        }
      });
    },
  });
}

/** Выбор групп-получателей: тот же список, что и в настройках, но с галочками. */
function pickGroups(current, onDone) {
  const all = data.groups || [];
  const picked = new Set(current);
  sheet({
    title: 'Кому показать',
    body: `
      <div class="row-subtitle" style="margin-bottom:12px">
        Ничего не выбрано — пост увидят все. Выбранные группы увидят только они.
      </div>
      <div class="search-box" style="margin-bottom:12px">
        ${icon('search', 19, 'muted')}
        <input id="gq" type="search" placeholder="Например, ПИН-31" autocomplete="off">
      </div>
      <div class="sheet-list" id="glist"></div>
      <button class="btn-primary" id="done" style="margin-top:12px">Готово</button>`,
    onMount(root, close) {
      const list = root.querySelector('#glist');
      const draw = q => {
        const needle = q.trim().toLowerCase().replace(/\s+/g, '');
        const found = (needle
          ? all.filter(g => g.toLowerCase().replace(/\s+/g, '').includes(needle))
          : [...picked, ...all.filter(g => !picked.has(g))]).slice(0, 120);
        list.innerHTML = `<div class="list-card">${found.map(g => `
          <div class="list-row tap" data-g="${esc(g)}">
            <div class="list-row-body"><div class="row-title">${esc(g)}</div></div>
            ${picked.has(g) ? `<span class="chevron">${icon('check', 18)}</span>` : ''}
          </div>`).join('')}</div>`;
      };
      draw('');
      root.querySelector('#gq').addEventListener('input', e => draw(e.target.value));
      list.addEventListener('click', e => {
        const row = e.target.closest('[data-g]');
        if (!row) return;
        const g = row.dataset.g;
        picked.has(g) ? picked.delete(g) : picked.add(g);
        haptic('light');
        draw(root.querySelector('#gq').value);
      });
      root.querySelector('#done').addEventListener('click', () => {
        onDone([...picked]);
        close();
      });
    },
  });
}

// ─────────────── очередь модерации ───────────────

export async function moderationScreen() {
  let queue;
  try {
    queue = await get('/api/admin/moderation');
  } catch (err) {
    return screen({ title: 'Модерация', body: `<div class="card" style="padding:18px">
      <div class="row-subtitle">${esc(err.message)}</div></div>` });
  }

  const node = screen({
    title: 'Модерация',
    subtitle: 'Анонимные посты ждут разрешения',
    body: queue.posts.length ? `<div class="stack">${queue.posts.map(p => `
      <div class="card post" data-post="${p.id}">
        ${p.media ? `<img class="post-media" src="${mediaUrl(p.media)}" alt="">` : ''}
        <div class="post-body">
          <div class="post-text">${paragraphs(p.text)}</div>
          <div class="post-foot">
            <span class="post-author">Автор: id ${p.author_id}</span>
            <span>·</span><span>${esc(ago(p.created_at))}</span>
          </div>
          <div class="stack" style="margin-top:12px">
            <button class="btn-primary" data-ok="${p.id}">Опубликовать</button>
            <button class="btn-secondary danger-btn" data-no="${p.id}">Отклонить</button>
          </div>
        </div>
      </div>`).join('')}</div>`
      : emptyState('Очередь пуста', 'check'),
  });

  node.addEventListener('click', async e => {
    const ok = e.target.closest('[data-ok]');
    const no = e.target.closest('[data-no]');
    if (!ok && !no) return;
    const id = (ok || no).dataset.ok || (ok || no).dataset.no;
    try {
      await post(`/api/admin/posts/${id}/${ok ? 'approve' : 'reject'}`, {});
      hapticNotify('success');
      toast(ok ? 'Опубликовано' : 'Отклонено');
      refresh();
    } catch (err) { toast(err.message); }
  });

  return node;
}

void settings;
