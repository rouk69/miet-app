# -*- coding: utf-8 -*-
"""
Метка версии на статике: чтобы правка доходила до людей сразу.

GitHub Pages отдаёт файлы с десятиминутным кешем, Telegram держит их
дольше и по своим правилам, а страницу мини-приложения кеширует ещё и
по адресу. После выкладки человек открывает приложение и видит
вчерашний вид — правка выглядит так, будто её не делали.

Лечится адресом: другой адрес — другой файл, значит запросить заново.
Метка считается от содержимого и меняется ровно тогда, когда менялись
файлы. Скрипт проставляет её в трёх местах:

- **стилям** — каждому свою (`app.css?v=3f2a1b`), они правятся порознь;
- **модулям** — общую, через карту импортов в `index.html`. Приписать
  версию к `<script src="js/app.js">` мало: модули тянут друг друга
  своими путями, и вышла бы каша из нового app.js и вчерашнего ui.js.
  Точка входа подключается инлайновым `import './js/app.js'` — он тоже
  проходит через карту. Браузер без importmap (iOS до 16.4) возьмёт всё
  дерево по старым адресам: не свежо, зато согласованно;
- **всей выкладке** — в `webapp.version` (её бот подставляет в адрес
  кнопки) и в `js/config.js` (её показывает профиль, чтобы «ничего не
  поменялось» перестало быть спором на слово).

Своя же метка внутри `config.js` в подсчёт не идёт: иначе каждый прогон
менял бы файл, файл менял бы метку, и та никогда бы не сошлась.

    python tools/stamp.py

Гонять перед выкладкой клиента — вместе с check_modules и check_app.
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
CONFIG = os.path.join(ROOT, "js", "config.js")
VERSION = os.path.join(ROOT, "webapp.version")

CSS_LINK = re.compile(r'(<link[^>]*href=")(css/[\w.-]+\.css)(\?v=[0-9a-f]+)?(")')
MAP_BLOCK = re.compile(
    r"[ \t]*<!-- карта модулей -->.*?<!-- /карта модулей -->\n", re.S)
BOOT_BLOCK = re.compile(
    r"[ \t]*<!-- точка входа -->.*?<!-- /точка входа -->\n", re.S)
BUILD_LINE = re.compile(r"(export const BUILD = ')([^']*)(';)")

PRELOAD = [
    "js/app.js", "js/router.js", "js/store.js", "js/ui.js", "js/icons.js",
    "js/tg.js", "js/api.js", "js/config.js", "js/schedule.js",
    "js/screens/common.js", "js/screens/home.js", "js/screens/schedule.js",
    "js/screens/feed.js",
]


def body(path: str) -> bytes:
    """Содержимое файла — у config.js без собственной метки."""
    blob = io.open(path, "rb").read()
    if os.path.normpath(path) == os.path.normpath(CONFIG):
        text = blob.decode("utf-8")
        blob = BUILD_LINE.sub(r"\1dev\3", text).encode("utf-8")
    return blob


def digest_of(paths) -> str:
    h = hashlib.sha1()
    for path in sorted(paths):
        h.update(body(path))
    return h.hexdigest()[:8]


def modules() -> list:
    """Все модули приложения — путями, какими их видит браузер."""
    out = []
    for base, _, names in os.walk(os.path.join(ROOT, "js")):
        for n in sorted(names):
            if n.endswith(".js"):
                full = os.path.join(base, n)
                out.append((full, os.path.relpath(full, ROOT).replace(os.sep, "/")))
    return sorted(out, key=lambda x: x[1])


def write_if_changed(path: str, text: str) -> bool:
    old = io.open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old == text:
        return False
    io.open(path, "w", encoding="utf-8").write(text)
    return True


def main() -> int:
    mods = modules()
    styles = [os.path.join(ROOT, "css", n)
              for n in sorted(os.listdir(os.path.join(ROOT, "css")))
              if n.endswith(".css")]
    version = digest_of(styles + [full for full, _ in mods])
    touched = []

    # ── метка внутрь клиента и рядом с ним
    config = io.open(CONFIG, encoding="utf-8").read()
    if not BUILD_LINE.search(config):
        print("  ! в js/config.js нет строки export const BUILD")
        return 1
    if write_if_changed(CONFIG, BUILD_LINE.sub(rf"\g<1>{version}\3", config)):
        touched.append("js/config.js")
    if write_if_changed(VERSION, version + chr(10)):
        touched.append("webapp.version")

    # ── index.html: стилям свои метки, модулям общая
    html = io.open(INDEX, encoding="utf-8").read()

    def stamp_css(m):
        head, href, _, tail = m.groups()
        full = os.path.join(ROOT, href.replace("/", os.sep))
        if not os.path.exists(full):
            print(f"  ! нет файла {href}")
            return m.group(0)
        return f"{head}{href}?v={digest_of([full])}{tail}"

    html = CSS_LINK.sub(stamp_css, html)

    imports = ",\n".join(
        f'      "./{href}": "./{href}?v={version}"' for _, href in mods)
    preload = "\n".join(
        f'  <link rel="modulepreload" href="{p}?v={version}">' for p in PRELOAD)

    block = (
        "  <!-- карта модулей -->\n"
        "  <!-- Собрано tools/stamp.py: подменяет адрес каждому модулю разом,\n"
        "       чтобы выкладка доходила до людей, а не лежала в кеше. -->\n"
        '  <script type="importmap">\n'
        "  {\n"
        '    "imports": {\n'
        f"{imports}\n"
        "    }\n"
        "  }\n"
        "  </script>\n\n"
        "  <!-- Модули без сборки грузятся каскадом: app.js → экраны → ui и\n"
        "       icons, и каждая ступень стоит целого круга по сети.\n"
        "       Предзагрузка ставит весь горячий путь в одну волну. -->\n"
        f"{preload}\n"
        "  <!-- /карта модулей -->\n")

    boot = (
        "  <!-- точка входа -->\n"
        "  <!-- Через import, а не src: так адрес точки входа тоже проходит\n"
        "       через карту выше и обновляется вместе со всем деревом. -->\n"
        '  <script type="module">import \'./js/app.js\';</script>\n'
        "  <!-- /точка входа -->\n")

    if not MAP_BLOCK.search(html) or not BOOT_BLOCK.search(html):
        print("  ! в index.html нет меток «карта модулей» и «точка входа»")
        return 1
    html = MAP_BLOCK.sub(block, html)
    html = BOOT_BLOCK.sub(boot, html)
    if write_if_changed(INDEX, html):
        touched.append("index.html")

    if touched:
        print(f"версия {version}, обновлено: {', '.join(touched)}")
    else:
        print(f"версия {version} — метки на месте")
    return 0


if __name__ == "__main__":
    sys.exit(main())
