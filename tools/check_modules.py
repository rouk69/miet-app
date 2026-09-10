# -*- coding: utf-8 -*-
"""Сверка импортов и экспортов между ES-модулями: движка JS в системе нет."""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

files = []
for base, _, names in os.walk(os.path.join(ROOT, "js")):
    for n in names:
        # bundle.js собран из этих же модулей — проверять его отдельно
        # значит ругаться на них дважды.
        if n.endswith(".js") and n != "bundle.js":
            files.append(os.path.join(base, n))

src = {f: io.open(f, encoding="utf-8").read() for f in files}

EXPORT_NAMED = re.compile(r"^export\s+(?:async\s+)?(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)", re.M)
EXPORT_LIST = re.compile(r"^export\s*\{([^}]*)\}", re.M)
EXPORT_DEFAULT = re.compile(r"^export\s+default\b", re.M)
IMPORT = re.compile(r"^import\s+(.+?)\s+from\s+['\"](.+?)['\"]", re.M | re.S)

exports = {}
for f, s in src.items():
    names = set(EXPORT_NAMED.findall(s))
    for chunk in EXPORT_LIST.findall(s):
        for part in chunk.split(","):
            part = part.strip()
            if not part:
                continue
            names.add(part.split(" as ")[-1].strip())
    if EXPORT_DEFAULT.search(s):
        names.add("default")
    exports[os.path.normpath(f)] = names

problems = []
for f, s in src.items():
    for clause, target in IMPORT.findall(s):
        path = os.path.normpath(os.path.join(os.path.dirname(f), target))
        if path not in exports:
            problems.append(f"{os.path.relpath(f, ROOT)}: нет файла {target}")
            continue
        wanted = set()
        m = re.search(r"\{([^}]*)\}", clause)
        if m:
            for part in m.group(1).split(","):
                part = part.strip()
                if part:
                    wanted.add(part.split(" as ")[0].strip())
        if re.match(r"^[A-Za-z_$][\w$]*\s*(,|$)", clause.strip()):
            wanted.add("default")
        missing = wanted - exports[path]
        for name in sorted(missing):
            problems.append(
                f"{os.path.relpath(f, ROOT)}: {target} не экспортирует «{name}»")

# Имена иконок должны существовать: опечатка рисует пустое место молча.
icons_src = src[os.path.normpath(os.path.join(ROOT, "js", "icons.js"))]
known = set(re.findall(r"^\s{2}([A-Za-z][\w$]*):", icons_src, re.M))
for f, s in src.items():
    if f.endswith("icons.js"):
        continue
    for name in re.findall(r"icon\(\s*'([A-Za-z][\w$]*)'", s):
        if name not in known:
            problems.append(f"{os.path.relpath(f, ROOT)}: нет иконки «{name}»")

# То же для иллюстраций: опечатка в имени сцены рисует стопку книг
# вместо кружки — молча и на самом видном месте, на пустом экране.
art_src = src[os.path.normpath(os.path.join(ROOT, "js", "art.js"))]
scenes = set(re.findall(r"^  ([a-zA-Z][\w$]*):", art_src, re.M))
for f, s in src.items():
    if f.endswith("art.js"):
        continue
    for name in re.findall(r"art(?:State)?\(\s*'([a-zA-Z][\w$]*)'", s):
        if name not in scenes:
            problems.append(f"{os.path.relpath(f, ROOT)}: нет иллюстрации «{name}»")

# И сама сцена должна быть целой разметкой: незакрытый тег браузер
# починит по-своему, и картинка поедет молча.
import xml.etree.ElementTree as ET                                  # noqa: E402

for name, svg in re.findall(r"^  ([a-zA-Z]+): `(.*?)`,", art_src, re.S | re.M):
    try:
        ET.fromstring("<svg>" + svg + "</svg>")
    except ET.ParseError as e:
        problems.append(f"js/art.js: сцена «{name}» — битая разметка ({e})")

# Каждый класс из разметки должен быть в CSS. Проверяем все модули, а
# не избранные: опечатка в классе не роняет ничего — просто блок теряет
# вид, и увидеть это можно только глазами, которых в этой среде нет.
css = "".join(io.open(os.path.join(ROOT, "css", n), encoding="utf-8").read()
              for n in ("tokens.css", "app.css"))
for f, js in sorted(src.items()):
    short = os.path.relpath(f, os.path.join(ROOT, "js"))
    for cls in sorted(set(re.findall(r'class="([^"$]+)"', js))):
        for one in cls.split():
            if one and "." + one not in css:
                problems.append(f"{short}: класс «{one}» не описан в CSS")

# Один класс — одно место. Два блока с одинаковым селектором означают,
# что второй молча перекрывает первый: так карточка объявления ОРИОКС
# однажды переопределила карточку новости, и лента новостей поехала —
# ничего не сломав и ничего не сообщив.
#
# Селектор берётся целиком, вместе с перенесёнными строками: «.a img,
# .a-stub» и «.a-stub» — разные правила, и общий кусок в них законен.
SELECTOR = re.compile(r"(?ms)^([.#][^{@}]+?)\s*\{")
seen = {}
for name in ("tokens.css", "app.css"):
    text = io.open(os.path.join(ROOT, "css", name), encoding="utf-8").read()
    for m in SELECTOR.finditer(text):
        sel = re.sub(r"\s+", " ", m.group(1).strip())
        where = f"{name}:{text[:m.start()].count(chr(10)) + 1}"
        if sel in seen:
            problems.append(
                f"css: «{sel}» описан дважды — {seen[sel]} и {where}")
        else:
            seen[sel] = where

# Сборка должна быть свежее исходников: она уезжает на Pages вместо
# них, и забытый stamp.py означал бы, что люди открывают вчерашний код.
built = os.path.join(ROOT, "js", "bundle.js")
if not os.path.exists(built):
    problems.append("js/bundle.js не собран — прогони tools/stamp.py")
else:
    # Сравниваем содержимое, а не время файлов: время сбивается от
    # любого касания, а разойтись сборка может только по содержимому.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bundle                                                  # noqa: E402
    if bundle.build() not in io.open(built, encoding="utf-8").read():
        problems.append(
            "js/bundle.js разошёлся с исходниками — прогони tools/stamp.py")


SHARED = {
    "esc", "el", "icon", "listCard", "listRow", "emptyState", "toast", "sheet",
    "lightbox", "segmented", "bindChoice", "toggle", "kpi", "skeleton",
    "iconTile", "pillRow", "contactRows", "screen", "pickGroup", "newsCard",
    "newsRow", "humanDate", "shortDate", "iconBtn", "go", "switchTab",
    "refresh", "register", "current", "depth", "isTab", "TABS", "data",
    "settings", "save", "loadData", "applyTheme", "markRead", "toggleFavorite",
    "isFavorite", "account", "canTalk", "get", "post", "track", "syncGroup",
    "loadMe", "flush", "API_BASE", "tg", "tgUser", "inTelegram", "haptic",
    "hapticSelect", "hapticNotify", "openLink", "confirmDialog", "alertDialog",
    "BackButton", "initTelegram", "syncChrome", "fetchSchedule", "weekOfCycle",
    "semesterStart", "nowState", "slotsOf", "lessonsOf", "dayCounts",
    "DAY_NAMES", "DAY_SHORT", "weekDates", "parseSubject", "shortSemestr",
    "mondayOf", "lessonRow", "postCard", "feedRow", "excerpt", "hoursStrip",
    "plural", "dayLabel", "weekdayOf", "KIND_NAMES", "TAB_NAMES",
    "moderationScreen", "articleScreen", "clubScreen", "campusItemScreen",
    "instituteScreen", "adminUserScreen", "teacherScreen", "roomScreen",
    "scoreScreen", "convertScreen", "glossaryScreen", "contactsScreen",
    "datesScreen", "chatsScreen", "curatorsScreen", "dayScreen",
}

IMPORT_NAMES = re.compile(r"^import\s+([\s\S]*?)\s+from", re.M)
DECLARED = re.compile(
    r"\b(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)")


def module_names(src: str):
    """Что модуль получает извне и что объявляет сам."""
    known = set()
    for clause in IMPORT_NAMES.findall(src):
        inside = re.search(r"\{([^}]*)\}", clause)
        if inside:
            for part in inside.group(1).split(","):
                part = part.strip()
                if part:
                    known.add(part.split(" as ")[-1].strip())
        head = clause.strip().split(",")[0].strip()
        if head and not head.startswith("{"):
            known.add(head)
    known |= set(DECLARED.findall(src))
    return known



def check_free_names(src_map, problems):
    """
    Имена, которые модуль использует, но нигде не берёт.

    Сверка импортов проверяет обратное — что импортируемое имя кем-то
    экспортировано. Забытый импорт она не видит, а в браузере это
    ReferenceError и пустой экран.
    """
    for path, text in src_map.items():
        known = module_names(text)
        used = set(re.findall(r"(?<![.\w$])([A-Za-z_$][\w$]*)\s*\(", text))
        used |= set(re.findall(r"(?<![.\w$])([A-Z][\w$]*)", text))
        for n in sorted((used & SHARED) - known):
            problems.append(
                f"{os.path.relpath(path, ROOT)}: «{n}» используется, "
                "но не импортирован")


check_free_names(src, problems)

if problems:
    print("НАЙДЕНО:")
    for p in problems:
        print("  ! " + p)
    sys.exit(1)
print(f"импорты, иконки и классы сходятся ({len(files)} модулей)")
