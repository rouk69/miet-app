# -*- coding: utf-8 -*-
"""
Прогоняет модули приложения в движке JS с заглушками браузера.

Проверки синтаксиса и имён ловят опечатки, но не ловят то, из-за чего
мини-апп встаёт совсем: ошибку при выполнении верхнего уровня модуля или
несостыковку экспортов. Здесь модули собираются в один скрипт в порядке
зависимостей и выполняются по-настоящему.

DOM тут игрушечный: цель — не отрисовать приложение, а дойти до конца
загрузки без исключения.
"""
import io
import os
import re
import sys
import tempfile

import dukpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

IMPORT = re.compile(
    r"^import\s+([\s\S]*?)\s+from\s*['\"](\.[^'\"]+)['\"]\s*;?", re.M)

SHIM = """
var __mod = {};
var window = this;
var localStorage = {
  _d: {},
  getItem: function (k) { return this._d[k] === undefined ? null : this._d[k]; },
  setItem: function (k, v) { this._d[k] = String(v); },
  removeItem: function (k) { delete this._d[k]; },
};
var __listeners = [];
function __el() {
  return {
    innerHTML: '', textContent: '', value: '', hidden: false, disabled: false,
    dataset: {}, style: { setProperty: function () {} },
    classList: { add: function () {}, remove: function () {},
                 toggle: function () {}, contains: function () { return false; } },
    appendChild: function () {}, append: function () {}, remove: function () {},
    addEventListener: function () {}, removeEventListener: function () {},
    querySelector: function () { return __el(); },
    querySelectorAll: function () { return []; },
    closest: function () { return null; },
    insertAdjacentHTML: function () {},
    replaceWith: function () {}, scrollIntoView: function () {},
    setAttribute: function () {}, focus: function () {},
    getContext: function () { return null; },
    content: { firstElementChild: null },
  };
}
var document = {
  documentElement: __el(),
  body: __el(),
  createElement: function () { return __el(); },
  getElementById: function () { return __el(); },
  querySelector: function () { return __el(); },
  querySelectorAll: function () { return []; },
  addEventListener: function (n, f) { __listeners.push(n); },
  visibilityState: 'visible',
};
window.addEventListener = function () {};
window.scrollTo = function () {};
window.open = function () {};
window.confirm = function () { return true; };
window.alert = function () {};
var history = { pushState: function () {}, back: function () {} };
var location = { search: '', reload: function () {} };
var navigator = { userAgent: 'test' };
var setTimeout = function (f) { return 0; };
var clearTimeout = function () {};
var requestAnimationFrame = function (f) { return 0; };
var IntersectionObserver = function () {
  return { observe: function () {}, unobserve: function () {} };
};
var AbortController = function () { this.signal = {}; this.abort = function () {}; };
var fetch = function () {
  return { then: function () { return this; }, catch: function () { return this; },
           finally: function () { return this; } };
};
var Telegram = undefined;
var console = { log: function () {}, warn: function () {}, error: function () {} };
"""


def order(files):
    """Топологический порядок: сначала то, от чего зависят остальные."""
    deps = {}
    for path in files:
        src = io.open(path, encoding="utf-8").read()
        here = os.path.dirname(path)
        deps[path] = {os.path.normpath(os.path.join(here, m[1]))
                      for m in IMPORT.findall(src)}
    done, out = set(), []
    while len(out) < len(files):
        moved = False
        for path in files:
            if path in done:
                continue
            if deps[path] <= done:
                out.append(path)
                done.add(path)
                moved = True
        if not moved:                       # цикл импортов
            rest = [os.path.relpath(p, ROOT) for p in files if p not in done]
            print("ЦИКЛ ИМПОРТОВ между:", ", ".join(rest))
            out.extend(p for p in files if p not in done)
            break
    return out


def translate(path: str, src: str) -> str:
    """ES-модуль → кусок общего скрипта с ручной таблицей экспортов."""
    key = os.path.relpath(path, ROOT).replace("\\", "/")
    here = os.path.dirname(path)
    body = src
    for clause, rel in IMPORT.findall(src):
        target = os.path.relpath(os.path.normpath(os.path.join(here, rel)),
                                 ROOT).replace("\\", "/")
        names = re.search(r"\{([^}]*)\}", clause)
        lines = []
        if names:
            for part in names.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                src_name, _, alias = part.partition(" as ")
                alias = (alias or src_name).strip()
                lines.append(f"var {alias} = __mod['{target}']"
                             f"['{src_name.strip()}'];")
        head = clause.strip().split(",")[0].strip()
        if head and not head.startswith("{"):
            lines.append(f"var {head} = __mod['{target}']['default'];")
        body = body.replace(
            re.search(re.escape(clause) + r"\s+from\s*['\"]"
                      + re.escape(rel) + r"['\"]\s*;?", body).group(0)
            if False else "", "")
        body = re.sub(r"^import\s+" + re.escape(clause) + r"\s+from\s*['\"]"
                      + re.escape(rel) + r"['\"]\s*;?",
                      "\n".join(lines), body, count=1, flags=re.M)

    exports = []
    for m in re.finditer(r"^export\s+default\s+(?:async\s+)?function\s+"
                         r"([A-Za-z_$][\w$]*)", body, re.M):
        exports.append(("default", m.group(1)))
    body = re.sub(r"^export\s+default\s+", "", body, flags=re.M)

    for m in re.finditer(r"^export\s+(?:async\s+)?(?:const|let|var|function"
                         r"|class)\s+([A-Za-z_$][\w$]*)", body, re.M):
        exports.append((m.group(1), m.group(1)))
    for m in re.finditer(r"^export\s*\{([^}]*)\}", body, re.M):
        for part in m.group(1).split(","):
            part = part.strip()
            if part:
                a, _, b = part.partition(" as ")
                exports.append(((b or a).strip(), a.strip()))
    body = re.sub(r"^export\s*\{[^}]*\}\s*;?", "", body, flags=re.M)
    body = re.sub(r"^export\s+", "", body, flags=re.M)

    table = ", ".join(f"'{name}': {local}" for name, local in exports)
    return (f"__mod['{key}'] = (function () {{\n{body}\n"
            f"return {{{table}}};\n}})();\n")


def main() -> int:
    files = []
    for base, _, names in os.walk(os.path.join(ROOT, "js")):
        for n in sorted(names):
            if n.endswith(".js"):
                files.append(os.path.join(base, n))

    bundle = [SHIM]
    for path in order(files):
        src = io.open(path, encoding="utf-8").read()
        bundle.append(f"/* ==== {os.path.relpath(path, ROOT)} ==== */")
        bundle.append(translate(path, src))
    bundle.append("'ok';")

    code = "\n".join(bundle)
    # Сборку кладём во временную папку: она нужна только чтобы посмотреть
    # на строку из сообщения об ошибке, и в репозитории ей не место.
    dump = os.path.join(tempfile.gettempdir(), "miet-bundle.js")
    io.open(dump, "w", encoding="utf-8").write(code)
    try:
        dukpy.evaljs(code)
    except Exception as e:                              # noqa: BLE001
        print("ОШИБКА ПРИ ЗАГРУЗКЕ:")
        print(str(e)[:1500])
        print()
        print("собранный скрипт лежит в " + dump
              + " — номер строки из сообщения указывает на него")
        return 1
    print(f"все {len(files)} модулей загрузились без ошибок")
    return check_logic(code)


# Чистые функции, которые ломаются молча: неверный значок или «6 дн.
# назад» вместо «вчера» не роняют приложение, их видно только глазами —
# а глаз тут ни у кого нет.
CASES = [
    ("значок физики", "subjectLook('Физика. Механика').glyph", "atom"),
    ("значок матанализа", "subjectLook('Математический анализ').glyph", "sigma"),
    ("значок истории", "subjectLook('История России').glyph", "landmark"),
    ("значок языка", "subjectLook('Иностранный язык').glyph", "languages"),
    ("значок информатики", "subjectLook('Информатика').glyph", "code"),
    ("незнакомый предмет получает свой",
     "subjectLook('Начерталка').glyph", "bookOpen"),
    ("цвет предмета постоянный",
     "String(subjectLook('Начерталка').tone === subjectLook('Начерталка').tone)",
     "true"),
    ("пустая дата не ломает разбор", "newsDate('').text", ""),
    ("кривая дата отдаётся как есть", "newsDate('позавчера').text", "позавчера"),
    ("пункт перечня распознан", "String(NUMBERED.test('1. Теории'))", "true"),
    ("буквенный пункт распознан", "String(NUMBERED.test('А) Княжение'))", "true"),
    ("обычный абзац не пункт",
     "String(NUMBERED.test('Подготовить доклады'))", "false"),
    ("ссылка становится ссылкой",
     "String(linkify('см. https://a.ru/x').indexOf('data-url=') > 0)", "true"),
    ("разметка в тексте экранирована",
     "String(linkify('<b>тут</b>').indexOf('&lt;b&gt;') >= 0)", "true"),
    ("вложение-PDF узнано",
     "fileLook('Задание', 'https://orioks.miet.ru/x/dz.pdf').label", "PDF"),
    ("вложение-документ узнано",
     "fileLook('Деловое письмо.docx', '').label", "DOC"),
    ("ссылка на ресурс узнана",
     "fileLook('Ссылки на лекции', 'https://vk.com/x').label", "Ссылка"),
    ("незнакомое вложение без подписи",
     "fileLook('Материал', '/storage/d/1/abc').label", ""),

    # 1 сентября 2026 — вторник. Вторая учебная неделя обязана начаться
    # 7-го, как её считает сам ОРИОКС, а не 8-го: иначе лаба, которая
    # завтра, показывалась сроком «14 сентября».
    ("вторая неделя начинается с понедельника",
     "weekMonday(new Date(2026, 8, 1), 2).getDate()", "7"),
    ("первая неделя — понедельник до 1 сентября",
     "weekMonday(new Date(2026, 8, 1), 1).getDate()", "31"),
    ("без номера недели даты нет",
     "String(weekMonday(new Date(2026, 8, 1), 0))", "null"),

    ("предмет узнаётся по длинным словам",
     "subjectKey('Физика. Механика. Термодинамика')", "физика механика"),
    ("предмет ОРИОКС и расписания сходится",
     "String(subjectKey('Линейная алгебра и аналитическая геометрия')"
     " === subjectKey('Линейная алгебра, аналитическая геометрия'))", "true"),

    # Лабораторную ищем среди лабораторных, а не среди любых пар этого
    # предмета: лекция по физике в тот же день сроком сдачи не является.
    ("день лабораторной берётся из расписания",
     "lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Лабораторная работа' }, 'Физика. Механика', 0)"
     ".date.getDate()", "10"),
    ("вид пары совпал с видом работы",
     "String(lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Лабораторная работа' }, 'Физика. Механика', 0)"
     ".exact)", "true"),
    ("без своей пары берём любую по предмету",
     "lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Реферат' }, 'Физика. Механика', 0).date.getDate()",
     "11"),
    ("чужого предмета в расписании нет",
     "String(lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Лабораторная работа' }, 'Философия', 0))", "null"),

    # Отказ сети не должен превращаться в «данных нет»: расписание
    # меняется раз в семестр, и вчерашняя копия — то же расписание.
    ("копия отдаётся, когда сеть молчит", "__stale.lessons.length", "2"),
    ("и помечена как сохранённая", "String(__stale.stale)", "true"),
    ("без копии — человеческое сообщение",
     "String(__failed.indexOf('miet.ru') > 0 || __failed.indexOf('МИЭТ') > 0)",
     "true"),

    # День без пар — обычное дело: у ИКТ-12 такой четверг всегда. Он
    # обязан выглядеть свободным днём, а не отказом загрузки.
    ("пустой день отдаёт пустой список",
     "slotsOf(NO_THURSDAY, 0, 4).length", "0"),
    ("день с парами отдаёт пары", "slotsOf(NO_THURSDAY, 0, 1).length", "1"),
    ("счётчик дней знает про пустой четверг",
     "String(dayCounts(NO_THURSDAY, 0)[4] || 0)", "0"),
    ("счётчик дней знает про занятый понедельник",
     "String(dayCounts(NO_THURSDAY, 0)[1])", "1"),
    ("в пустой день ничего не идёт и не падает",
     "String(nowState(NO_THURSDAY, 0, new Date(2026, 8, 10, 12, 0)).current)",
     "null"),
    ("и следующей пары в нём тоже нет",
     "String(nowState(NO_THURSDAY, 0, new Date(2026, 8, 10, 12, 0)).next)",
     "null"),

    # Картинка поста занимает место по своим пропорциям: единое
    # соотношение резало пополам скриншоты расписания.
    ("размеры читаются из имени",
     "mediaSize('abc-1200x800.jpg').w", "1200"),
    ("у старого имени размеров нет",
     "String(mediaSize('abc.jpg'))", "null"),
    ("пропорции попадают в разметку",
     "String(mediaTag('abc-1200x800.jpg').indexOf('aspect-ratio:1200/800') > 0)",
     "true"),
    ("высокой картинке отводится своё место",
     "String(mediaTag('abc-800x1600.jpg').indexOf('aspect-ratio:4/5') > 0)",
     "true"),
    ("высокая вписывается целиком",
     "String(mediaTag('abc-800x1600.jpg').indexOf('tall') > 0)", "true"),
    ("без размеров картинка помечена",
     "String(mediaTag('abc.jpg').indexOf('unsized') > 0)", "true"),

    # Иллюстрации: сцена обязана быть настоящим svg, а незнакомое имя —
    # не пустотой на пол-экрана, а хоть чем-то.
    ("сцена рисуется", "String(art('free').indexOf('<svg') === 0)", "true"),
    ("сцена знает свой размер",
     "String(art('rest', 64).indexOf('width=\"64\"') > 0)", "true"),
    ("незнакомая сцена не оставляет дыру",
     "String(art('такой-нет').length > 100)", "true"),
    ("пустое состояние подписано",
     "String(artState('free', 'Пар нет').indexOf('Пар нет') > 0)", "true"),
    ("подпись экранирована",
     "String(artState('free', '<b>x</b>').indexOf('&lt;b&gt;') > 0)", "true"),

    # Разбор ведомости общий у экрана заданий и главной: если он начнёт
    # считать делами посещаемость, это увидят оба сразу.
    ("ведомость разворачивается целиком", "PLAN.length", "4"),
    ("в делах только настоящее задание", "TODO.length", "1"),
    ("сданное делом не считается",
     "String(TODO.every(function (t) { return !t.done; }))", "true"),
    ("формальности и сессия отсеяны", "TODO[0].name", "ЛР.2"),
    ("у дела есть срок и предмет",
     "String(TODO[0].due instanceof Date && TODO[0].subject.length > 0)",
     "true"),
]


# Модули в сборке завёрнуты, глобальных имён нет: достаём нужное из
# таблицы экспортов и раскладываем по коротким именам.
PRELUDE = """
var _t = __mod['js/screens/tasks.js'];
var subjectLook = _t.subjectLook, newsDate = _t.newsDate,
    linkify = _t.linkify, NUMBERED = _t.NUMBERED, fileLook = _t.fileLook,
    weekMonday = _t.weekMonday, subjectKey = _t.subjectKey,
    lessonDay = _t.lessonDay, flatten = _t.flatten, pendingOf = _t.pendingOf;
var _a = __mod['js/art.js'];
var art = _a.art, artState = _a.artState;
var _f = __mod['js/screens/feed.js'];
var mediaSize = _f.mediaSize, mediaTag = _f.mediaTag;

var _sc = __mod['js/schedule.js'];
var slotsOf = _sc.slotsOf, dayCounts = _sc.dayCounts, nowState = _sc.nowState;

// Сеть отвалилась, а копия в хранилище есть: экран обязан показать её,
// а не ошибку. Второй случай — копии нет, и тогда сообщение должно
// называть виновника, а не «Failed to fetch».
var __stale = null, __failed = '';
(function () {
  var copy = { at: 0, data: { semestr: 'Осенний семестр 2026/2027', times: [],
    lessons: [{ week: 0, day: 1 }, { week: 0, day: 2 }] } };
  localStorage.setItem('miet-sched:Г-1', JSON.stringify(copy));
  fetch = function () { return Promise.reject(new Error('нет сети')); };
  _sc.fetchSchedule('Г-1').then(function (s) { __stale = s; });
  _sc.fetchSchedule('Г-2').catch(function (e) { __failed = e.message; });
})();

// Расписание группы, у которой в четверг пар нет вовсе (так живёт
// ИКТ-12): пустой день обязан оставаться пустым днём, а не поломкой.
var NO_THURSDAY = { semestr: 'Осенний семестр 2026/2027', times: [], lessons: [
  { week: 0, day: 1, pair: 1, from: '09:00', to: '10:20',
    subject: 'Физика', kind: 'Лекция', kindCls: 'lek', flags: [], room: '1201' },
  { week: 0, day: 5, pair: 2, from: '10:30', to: '11:50',
    subject: 'Физика', kind: 'Лабораторная', kindCls: 'lab', flags: [], room: '3229' }
] };

var SCHED = { semestr: 'Осенний семестр 2026/2027', lessons: [
  { week: 1, day: 4, pair: 3, subject: 'Физика. Механика',
    kindCls: 'lab', from: '12:00', room: '3229' },
  { week: 1, day: 5, pair: 2, subject: 'Физика. Механика',
    kindCls: 'lek', from: '10:30', room: '1201' }
] };

// Ведомость в том виде, в каком её отдаёт сервер: задание, сданное
// задание, экзамен и формальность. Из четырёх записей делом является
// ровно одна.
var VEDOMOST = { disciplines: [{ name: 'Физика. Механика', events: [
  { name: 'ЛР.2', type: 'Лабораторная работа', week: 10, max_grade: 10,
    grade: null, done: false, task: true, session: false },
  { name: 'ЛР.1', type: 'Лабораторная работа', week: 2, max_grade: 10,
    grade: 8, done: true, task: true, session: false },
  { name: 'Экзамен', type: 'Экзамен', week: 17, max_grade: 30,
    done: false, task: false, session: true },
  { name: 'А/П', type: 'Активность/Посещаемость', week: 8, max_grade: 24,
    done: false, task: false, session: false }
] }] };

var PLAN = flatten(VEDOMOST, SCHED, new Date(2026, 8, 1), 0);
var TODO = pendingOf(PLAN);
"""


def check_logic(bundle: str) -> int:
    """
    Гоняет чистые функции клиента на живом движке.

    Контекст один на все проверки, а не по одному на каждую: часть
    подготовки — обещания (загрузка расписания с подменённой сетью), а
    они разрешаются не сразу. Между подготовкой и проверками очередь
    прокручивается вхолостую — иначе обещание так и осталось бы
    висящим, а проверка сравнивала бы пустоту.
    """
    try:
        js = dukpy.JSInterpreter()
        js.evaljs(bundle + PRELUDE + "\n'готово';")
        for _ in range(50):
            js.evaljs("0;")
    except Exception as e:                              # noqa: BLE001
        print(f"  ✗ подготовка не выполнилась: {str(e)[:300]}")
        return 1

    bad = 0
    for name, expr, want in CASES:
        try:
            got = js.evaljs("String(" + expr + ");")
        except Exception as e:                          # noqa: BLE001
            print(f"  ✗ {name}: {str(e)[:200]}")
            bad += 1
            continue
        if str(got) != want:
            print(f"  ✗ {name}: получили {got!r}, ждали {want!r}")
            bad += 1
    if bad:
        print(f"логика клиента: провалено {bad} из {len(CASES)}")
        return 1
    print(f"логика клиента: {len(CASES)} проверок сошлись")
    return 0


if __name__ == "__main__":
    sys.exit(main())
