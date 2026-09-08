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
]


# Модули в сборке завёрнуты, глобальных имён нет: достаём нужное из
# таблицы экспортов и раскладываем по коротким именам.
PRELUDE = ("var _t = __mod['js/screens/tasks.js'];"
           "var subjectLook = _t.subjectLook, newsDate = _t.newsDate,"
           "    linkify = _t.linkify, NUMBERED = _t.NUMBERED;")


def check_logic(bundle: str) -> int:
    """Гоняет функции экрана заданий на живом движке."""
    bad = 0
    for name, expr, want in CASES:
        try:
            got = dukpy.evaljs(bundle + PRELUDE + "\nString(" + expr + ");")
        except Exception as e:                          # noqa: BLE001
            print(f"  ✗ {name}: {str(e)[:200]}")
            bad += 1
            continue
        if str(got) != want:
            print(f"  ✗ {name}: получили {got!r}, ждали {want!r}")
            bad += 1
    if bad:
        print(f"логика экрана заданий: провалено {bad} из {len(CASES)}")
        return 1
    print(f"логика экрана заданий: {len(CASES)} проверок сошлись")
    return 0


if __name__ == "__main__":
    sys.exit(main())
