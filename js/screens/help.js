// Помощь в заданиях: доска «нужна помощь» и «могу помочь».
//
// Смысл раздела — свести двух людей, поэтому ник автора виден всем, кто
// открыл объявление. Экран обязан сказать об этом до публикации, а не
// после: человек должен понимать, что оставляет контакт.

import { icon } from '../icons.js';
import { esc, emptyState, toast, sheet } from '../ui.js';
import { get, post, account, canTalk } from '../api.js';
import { refresh } from '../router.js';
import { haptic, hapticNotify, confirmDialog, openLink } from '../tg.js';
import { screen } from './common.js';

let kind = 'need';   // какую сторону доски показываем

const parseTs = ts => new Date(String(ts || '').replace(' ', 'T') + 'Z');

function ago(ts) {
  const min = Math.floor((Date.now() - parseTs(ts).getTime()) / 60000);
  if (min < 60) return `${Math.max(1, min)} мин назад`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h} ч назад`;
  const d = Math.floor(h / 24);
  return d === 1 ? 'вчера' : `${d} дн назад`;
}

const card = (o, me) => `
  <div class="card offer ${o.status === 'closed' ? 'closed' : ''}" data-offer="${o.id}">
    <div class="offer-head">
      <span class="offer-kind ${o.kind}">
        ${o.kind === 'need' ? 'Нужна помощь' : 'Могу помочь'}
      </span>
      ${o.price === 'deal' ? '<span class="chip">по договорённости</span>'
    : '<span class="chip">бесплатно</span>'}
      ${o.status === 'closed' ? '<span class="chip">закрыто</span>' : ''}
    </div>
    <div class="offer-subject">${esc(o.subject)}</div>
    ${o.text ? `<div class="offer-text">${esc(o.text)}</div>` : ''}
    <div class="offer-foot">
      <span>${esc(o.author_name)}${o.group ? ` · ${esc(o.group)}` : ''}</span>
      <span>·</span>
      <span>${esc(ago(o.created_at))}</span>
    </div>
    <div class="offer-actions">
      ${o.author_id === me.id ? `
        <button class="btn-secondary" data-do="${o.status === 'open' ? 'close' : 'reopen'}"
                data-id="${o.id}">
          ${o.status === 'open' ? 'Вопрос решён' : 'Открыть снова'}
        </button>
        <button class="btn-secondary danger-btn" data-do="delete" data-id="${o.id}">
          Удалить
        </button>`
    : o.username ? `
        <button class="btn-primary" data-write="${esc(o.username)}">
          ${icon('messageCircle', 17)} Написать
        </button>`
      : `<div class="row-subtitle">У автора нет ника в Telegram —
           напиши в комментариях к ленте или найди его в группе</div>`}
      ${me.can_manage && o.author_id !== me.id ? `
        <button class="btn-secondary danger-btn" data-do="delete" data-id="${o.id}">
          Убрать
        </button>` : ''}
    </div>
  </div>`;

export default async function helpScreen() {
  if (!canTalk) {
    return screen({
      title: 'Помощь в заданиях',
      body: emptyState('Раздел работает внутри Telegram', 'handHeart'),
    });
  }

  let board;
  try {
    board = await get(`/api/help?kind=${kind}`);
  } catch (err) {
    return screen({
      title: 'Помощь в заданиях',
      body: `<div class="card" style="padding:18px">
        <div class="row-subtitle">${esc(err.message)}</div></div>`,
    });
  }

  // Свой id приходит из /api/me — по нему и отличаем своё объявление от
  // чужого: у своего кнопки «решено» и «удалить», у чужого — «написать».
  const me = { id: account.id, can_manage: board.can_manage };

  const node = screen({
    title: 'Помощь в заданиях',
    subtitle: 'Найди старшекурсника или помоги сам',
    body: `
      <div class="segmented" id="side">
        <button class="segmented-item ${kind === 'need' ? 'active' : ''}"
                data-kind="need">Нужна помощь · ${board.need}</button>
        <button class="segmented-item ${kind === 'offer' ? 'active' : ''}"
                data-kind="offer">Могу помочь · ${board.offer}</button>
      </div>

      <div class="search-box" style="margin:12px 0">
        ${icon('search', 19, 'muted')}
        <input id="hq" type="search" placeholder="Предмет или тема" autocomplete="off">
      </div>

      <button class="btn-primary compose-btn" id="add">
        ${icon('edit', 18)} Разместить объявление
      </button>

      <div class="stack" id="hlist" style="margin-top:14px"></div>

      ${board.mine.length ? `
        <div class="section-head"><div class="section-title">Мои объявления</div></div>
        <div class="stack">${board.mine.map(o => card(o, me)).join('')}</div>`
    : ''}`,
  });

  const list = node.querySelector('#hlist');
  const draw = offers => {
    list.innerHTML = offers.length
      ? offers.map(o => card(o, me)).join('')
      : emptyState(kind === 'need'
        ? 'Никто пока не просил помощи'
        : 'Никто пока не предлагал помощь', 'handHeart');
  };
  draw(board.offers);

  node.querySelector('#side').addEventListener('click', e => {
    const b = e.target.closest('[data-kind]');
    if (!b || b.dataset.kind === kind) return;
    kind = b.dataset.kind;
    haptic('light');
    refresh();
  });

  let timer = null;
  node.querySelector('#hq').addEventListener('input', e => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    timer = setTimeout(async () => {
      try {
        const r = await get(`/api/help?kind=${kind}&q=${encodeURIComponent(q)}`);
        draw(r.offers);
      } catch (err) { toast(err.message); }
    }, 250);
  });

  node.querySelector('#add').addEventListener('click', () => composer(kind));

  node.addEventListener('click', async e => {
    const write = e.target.closest('[data-write]');
    if (write) return openLink(`https://t.me/${write.dataset.write}`);

    const act = e.target.closest('[data-do]');
    if (!act) return;
    const what = act.dataset.do;
    if (what === 'delete' && !await confirmDialog('Удалить объявление?')) return;
    try {
      await post(`/api/help/${act.dataset.id}/${what}`, {});
      hapticNotify('success');
      refresh();
    } catch (err) { toast(err.message); }
  });

  return node;
}

function composer(startKind) {
  let side = startKind;
  let price = 'free';

  sheet({
    title: 'Новое объявление',
    height: '72vh',
    body: `
      <div class="field-group">
        <div class="field-label">Что именно</div>
        <div class="segmented" id="ckind">
          <button class="segmented-item ${side === 'need' ? 'active' : ''}"
                  data-k="need">Нужна помощь</button>
          <button class="segmented-item ${side === 'offer' ? 'active' : ''}"
                  data-k="offer">Могу помочь</button>
        </div>
      </div>

      <div class="field-group">
        <div class="field-label">Предмет</div>
        <input class="field-input" id="subj" maxlength="80"
               placeholder="Например, матанализ">
      </div>

      <div class="field-group">
        <div class="field-label">Подробности — по желанию</div>
        <textarea class="field-input" id="text" rows="4" maxlength="600"
                  placeholder="С чем именно нужна помощь"></textarea>
      </div>

      <div class="field-group">
        <div class="field-label">Условия</div>
        <div class="segmented" id="cprice">
          <button class="segmented-item active" data-p="free">Бесплатно</button>
          <button class="segmented-item" data-p="deal">По договорённости</button>
        </div>
      </div>

      <div class="warn-note">
        ${icon('info', 16)}
        Твой ник в Telegram увидят все, кто откроет объявление — иначе с
        тобой не свяжутся. Закрыть его можно кнопкой «Вопрос решён».
      </div>

      <button class="btn-primary" id="send" style="margin-top:12px">
        Разместить
      </button>`,
    onMount(root, close) {
      root.querySelector('#ckind').addEventListener('click', e => {
        const b = e.target.closest('[data-k]');
        if (!b) return;
        side = b.dataset.k;
        root.querySelectorAll('#ckind .segmented-item')
          .forEach(x => x.classList.remove('active'));
        b.classList.add('active');
      });
      root.querySelector('#cprice').addEventListener('click', e => {
        const b = e.target.closest('[data-p]');
        if (!b) return;
        price = b.dataset.p;
        root.querySelectorAll('#cprice .segmented-item')
          .forEach(x => x.classList.remove('active'));
        b.classList.add('active');
      });

      root.querySelector('#send').addEventListener('click', async () => {
        const subject = root.querySelector('#subj').value.trim();
        if (!subject) return toast('Укажи предмет');
        const btn = root.querySelector('#send');
        btn.disabled = true;
        try {
          await post('/api/help', {
            kind: side, subject, price,
            text: root.querySelector('#text').value.trim(),
          });
          hapticNotify('success');
          close();
          toast('Объявление размещено');
          kind = side;
          refresh();
        } catch (err) {
          toast(err.message);
          btn.disabled = false;
        }
      });
    },
  });
}

