// Два счётных инструмента: баллы БРС и конвертер величин.
//
// Оба считают на месте и без сети. Оценки из ОРИОКС сюда не тянутся —
// доступа к чужому личному кабинету у приложения нет и быть не должно;
// баллы человек вводит сам, глядя в ОРИОКС, а приложение отвечает на
// вопрос, ради которого туда и лезут: сколько осталось набрать.

import { icon } from '../icons.js';
import { esc } from '../ui.js';
import { openLink } from '../tg.js';
import { screen } from './common.js';

// ─────────────── баллы ───────────────

// Шкала МИЭТ: 100 баллов за семестр, из них экзамен — отдельная часть.
// Пороги взяты из общей практики БРС и подписаны как ориентир: у разных
// дисциплин вес контрольных точек свой, и выдавать это за точный расчёт
// нельзя.
const GRADES = [
  { from: 86, label: 'Отлично', tone: 'success' },
  { from: 69, label: 'Хорошо', tone: 'primary' },
  { from: 50, label: 'Удовлетворительно', tone: 'warning' },
  { from: 0, label: 'Не сдано', tone: 'danger' },
];

const gradeOf = n => GRADES.find(g => n >= g.from);

export async function scoreScreen() {
  const node = screen({
    title: 'Баллы и БРС',
    subtitle: 'Посчитать, сколько осталось набрать',
    body: `
      <div class="card" style="padding:16px">
        <div class="field-label" style="margin-bottom:10px">
          Баллы за контрольные точки
        </div>
        <div id="kts" class="stack"></div>
        <button class="btn-secondary" id="add" style="margin-top:10px">
          Добавить точку
        </button>
      </div>

      <div class="card" style="padding:16px;margin-top:12px">
        <div class="field-label" style="margin-bottom:8px">
          Сколько даёт экзамен или зачёт
        </div>
        <input class="field-input" id="exam" type="number" inputmode="numeric"
               value="30" min="0" max="100">
        <div class="row-subtitle" style="margin-top:6px">
          В МИЭТе это обычно 30 из 100, но у каждой дисциплины свой вес —
          посмотри в ОРИОКС.
        </div>
      </div>

      <div id="out" style="margin-top:14px"></div>

      <button class="btn-primary" id="orioks" style="margin-top:14px">
        ${icon('external', 17)} Открыть ОРИОКС
      </button>
      <div class="fab-note">
        Приложение не знает твои настоящие баллы: доступа к личному кабинету
        у него нет. Введи то, что видишь в ОРИОКС, — и оно посчитает остаток.
      </div>`,
  });

  const kts = node.querySelector('#kts');
  const out = node.querySelector('#out');

  const row = (i, value = '') => `
    <div class="kt-row" data-kt="${i}">
      <span class="kt-label">КТ${i + 1}</span>
      <input class="field-input" type="number" inputmode="numeric"
             placeholder="баллы" value="${value}" min="0" max="100">
      <button class="kt-drop" data-drop="${i}">${icon('x', 16)}</button>
    </div>`;

  let count = 3;
  const render = () => {
    const values = [...kts.querySelectorAll('input')].map(i => i.value);
    kts.innerHTML = Array.from({ length: count },
      (_, i) => row(i, values[i] ?? '')).join('');
    recount();
  };

  function recount() {
    const got = [...kts.querySelectorAll('input')]
      .map(i => Number(i.value) || 0)
      .reduce((a, b) => a + b, 0);
    const exam = Number(node.querySelector('#exam').value) || 0;
    const max = got + exam;
    const grade = gradeOf(got);

    // Сколько нужно на экзамене до каждой ступени — это и есть ответ,
    // ради которого считают: «мне хватит тройки или надо стараться».
    const need = GRADES.slice(0, 3).map(g => ({
      label: g.label,
      need: Math.max(0, g.from - got),
      real: g.from - got <= exam,
    }));

    out.innerHTML = `
      <div class="kpi-grid">
        <div class="kpi-tile">
          <div class="kpi-number">${got}</div>
          <div class="kpi-label">Набрано сейчас</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-number">${max}</div>
          <div class="kpi-label">Максимум с экзаменом</div>
        </div>
      </div>
      <div class="card" style="padding:16px;margin-top:12px">
        <div class="row-title" style="color:var(--${grade.tone})">
          Сейчас: ${esc(grade.label)}
        </div>
        <div class="stack" style="margin-top:12px">
          ${need.map(n => `
            <div class="need-row ${n.real ? '' : 'unreal'}">
              <span>${esc(n.label)}</span>
              <b>${n.need === 0 ? 'уже есть'
    : n.real ? `нужно ещё ${n.need}` : 'уже не набрать'}</b>
            </div>`).join('')}
        </div>
      </div>`;
  }

  render();

  kts.addEventListener('input', recount);
  node.querySelector('#exam').addEventListener('input', recount);
  node.querySelector('#add').addEventListener('click', () => {
    if (count < 8) { count++; render(); }
  });
  kts.addEventListener('click', e => {
    const drop = e.target.closest('[data-drop]');
    if (drop && count > 1) { count--; render(); }
  });
  node.querySelector('#orioks').addEventListener('click',
    () => openLink('https://orioks.miet.ru/main/login'));

  return node;
}

// ─────────────── конвертер ───────────────

// Всё через коэффициент к базовой единице: так добавление величины —
// одна строка, а не новая формула перевода в каждую сторону.
const UNITS = {
  Длина: { m: 1, км: 1000, см: 0.01, мм: 0.001, мкм: 1e-6, нм: 1e-9,
    дюйм: 0.0254, фут: 0.3048 },
  Масса: { кг: 1, г: 0.001, мг: 1e-6, т: 1000, фунт: 0.45359237 },
  Время: { с: 1, мс: 0.001, мкс: 1e-6, мин: 60, ч: 3600, сут: 86400 },
  Информация: { Б: 1, КБ: 1024, МБ: 1024 ** 2, ГБ: 1024 ** 3, ТБ: 1024 ** 4,
    бит: 0.125 },
  Энергия: { Дж: 1, кДж: 1000, кВт·ч: 3.6e6, эВ: 1.602176634e-19,
    кал: 4.184 },
  Давление: { Па: 1, кПа: 1000, МПа: 1e6, бар: 1e5, атм: 101325,
    'мм рт. ст.': 133.322 },
  Напряжение: { В: 1, мВ: 0.001, мкВ: 1e-6, кВ: 1000 },
  Сопротивление: { Ом: 1, мОм: 0.001, кОм: 1000, МОм: 1e6 },
  Ёмкость: { Ф: 1, мкФ: 1e-6, нФ: 1e-9, пФ: 1e-12 },
  Частота: { Гц: 1, кГц: 1000, МГц: 1e6, ГГц: 1e9 },
};

// Константы, которые в электронике спрашивают чаще всего. Значения — по
// системе СИ 2019 года, где часть из них определена точно.
const CONSTANTS = [
  ['Заряд электрона', 'e', '1,602176634·10⁻¹⁹ Кл'],
  ['Постоянная Планка', 'h', '6,62607015·10⁻³⁴ Дж·с'],
  ['Постоянная Больцмана', 'k', '1,380649·10⁻²³ Дж/К'],
  ['Скорость света', 'c', '299 792 458 м/с'],
  ['Число Авогадро', 'Nₐ', '6,02214076·10²³ 1/моль'],
  ['Тепловой потенциал при 300 K', 'kT/e', '≈ 25,85 мВ'],
  ['Диэлектрическая проницаемость кремния', 'ε(Si)', '≈ 11,7'],
  ['Ширина запрещённой зоны кремния', 'Eg(Si)', '≈ 1,12 эВ при 300 K'],
];

export async function convertScreen() {
  let kind = 'Длина';

  const node = screen({
    title: 'Конвертер',
    subtitle: 'Единицы, которые нужны на парах',
    body: `
      <div class="pill-row" id="kinds">
        ${Object.keys(UNITS).map(k => `
          <button class="pill ${k === kind ? 'active' : ''}" data-kind="${esc(k)}">
            ${esc(k)}
          </button>`).join('')}
      </div>

      <div class="card" style="padding:16px;margin-top:14px">
        <div class="convert-row">
          <input class="field-input" id="val" type="number" inputmode="decimal" value="1">
          <select class="field-input" id="from"></select>
        </div>
        <div class="convert-eq">${icon('shuffle', 18)}</div>
        <div class="convert-row">
          <input class="field-input" id="res" readonly>
          <select class="field-input" id="to"></select>
        </div>
      </div>

      <div id="all" class="list-card" style="margin-top:12px"></div>

      <div class="section-head"><div class="section-title">Константы</div></div>
      <p class="section-note">Те, что чаще всего нужны в задачах по электронике.</p>
      <div class="list-card">
        ${CONSTANTS.map(([name, sign, value]) => `
          <div class="list-row">
            <div class="list-row-body">
              <div class="row-title">${esc(name)}</div>
              <div class="row-subtitle">${esc(sign)}</div>
            </div>
            <div class="list-row-value tnum">${esc(value)}</div>
          </div>`).join('')}
      </div>`,
  });

  const val = node.querySelector('#val');
  const from = node.querySelector('#from');
  const to = node.querySelector('#to');
  const res = node.querySelector('#res');
  const all = node.querySelector('#all');

  const fillUnits = () => {
    const names = Object.keys(UNITS[kind]);
    const options = names.map(u => `<option>${esc(u)}</option>`).join('');
    from.innerHTML = options;
    to.innerHTML = options;
    from.value = names[0];
    to.value = names[1] || names[0];
    recount();
  };

  function pretty(n) {
    if (!isFinite(n)) return '—';
    if (n !== 0 && (Math.abs(n) < 1e-4 || Math.abs(n) >= 1e9)) {
      return n.toExponential(4).replace('e', '·10^');
    }
    // Округляем до разумного: у конвертера нет задачи показать
    // шестнадцать знаков после запятой.
    return String(Math.round(n * 1e6) / 1e6);
  }

  function recount() {
    const table = UNITS[kind];
    const base = (Number(val.value) || 0) * table[from.value];
    res.value = pretty(base / table[to.value]);
    all.innerHTML = Object.keys(table).map(u => `
      <div class="list-row">
        <div class="list-row-body"><div class="row-title">${esc(u)}</div></div>
        <div class="list-row-value tnum">${esc(pretty(base / table[u]))}</div>
      </div>`).join('');
  }

  fillUnits();

  node.querySelector('#kinds').addEventListener('click', e => {
    const b = e.target.closest('[data-kind]');
    if (!b) return;
    kind = b.dataset.kind;
    node.querySelectorAll('#kinds .pill').forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    fillUnits();
  });

  [val, from, to].forEach(el => el.addEventListener('input', recount));
  return node;
}
