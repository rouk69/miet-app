# -*- coding: utf-8 -*-
"""
Сборка клиента и метки версий: чтобы приложение открывалось быстро и
правка доходила до людей сразу.

Две беды решаются здесь.

**Тридцать два похода по сети.** Приложение написано ES-модулями без
сборщика — так его удобно править и читать, но браузер за это платит:
каждый модуль отдельным запросом, и на мобильном интернете это секунды
ожидания. Поэтому рядом с исходниками кладётся `js/bundle.js` — те же
модули одним файлом (`tools/bundle.py`), и страница грузит его. Если
сборка почему-то не выполнилась, через две секунды подключаются
исходные модули: белый экран хуже лишнего запроса.

**Кеш.** GitHub Pages отдаёт файлы с десятиминутным кешем, Telegram
держит их дольше и по своим правилам, а страницу мини-приложения
кеширует ещё и по адресу. Поэтому к файлам дописывается метка от
содержимого, а общая метка выкладки уходит в `webapp.version` (её бот
подставляет в адрес кнопки) и в `js/config.js` (её показывает профиль).

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bundle                                           # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = bundle.ROOT
INDEX = os.path.join(ROOT, "index.html")
CONFIG = os.path.join(ROOT, "js", "config.js")
VERSION = os.path.join(ROOT, "webapp.version")
BUILT = os.path.join(ROOT, "js", "bundle.js")

CSS_LINK = re.compile(r'(<link[^>]*href=")(css/[\w.-]+\.css)(\?v=[0-9a-f]+)?(")')
MAP_BLOCK = re.compile(
    r"[ \t]*<!-- карта модулей -->.*?<!-- /карта модулей -->\n", re.S)
BOOT_BLOCK = re.compile(
    r"[ \t]*<!-- точка входа -->.*?<!-- /точка входа -->\n", re.S)
BUILD_LINE = re.compile(r"(export const BUILD = ')([^']*)(';)")
# Метки в адресах: их вычёркиваем, когда считаем метку.
STAMP_IN_URL = re.compile(r"[?]v=[0-9a-f]+")


def body(path: str) -> bytes:
    """
    Содержимое файла для подсчёта метки — без самих меток.

    У `config.js` вычёркивается строка с версией, у `index.html` — все
    «?v=…»: иначе метка зависела бы от себя самой и не сошлась бы
    никогда. Сам `index.html` в подсчёт входит обязательно — правка в
    нём (подключение сборки, порядок скриптов) обязана менять метку,
    иначе Telegram отдаст страницу из кеша.
    """
    blob = io.open(path, "rb").read()
    name = os.path.normpath(path)
    if name == os.path.normpath(CONFIG):
        blob = BUILD_LINE.sub(r"\1dev\3", blob.decode("utf-8")).encode("utf-8")
    elif name == os.path.normpath(INDEX):
        text = blob.decode("utf-8")
        blob = STAMP_IN_URL.sub("", text).encode("utf-8")
    return blob


def digest_of(paths) -> str:
    h = hashlib.sha1()
    for path in sorted(paths):
        h.update(body(path))
    return h.hexdigest()[:8]


def write_if_changed(path: str, text: str) -> bool:
    old = io.open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old == text:
        return False
    io.open(path, "w", encoding="utf-8").write(text)
    return True


def main() -> int:
    mods = bundle.modules()
    styles = [os.path.join(ROOT, "css", n)
              for n in sorted(os.listdir(os.path.join(ROOT, "css")))
              if n.endswith(".css")]
    version = digest_of(styles + mods + [INDEX])
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

    # ── сборка: те же модули одним файлом
    built = bundle.build(
        "/* Собрано tools/stamp.py из js/*.js — не правьте здесь.\n"
        f"   Версия {version}. Исходники лежат рядом и остаются модулями. */")
    # Флаг говорит странице, что сборка выполнилась целиком: по нему
    # решается, не подключать ли исходные модули запасным путём.
    built += "\nwindow.__mietBooted = true;\n"
    if write_if_changed(BUILT, built):
        touched.append("js/bundle.js")

    # ── index.html: стилям свои метки, приложению — сборка
    html = io.open(INDEX, encoding="utf-8").read()

    def stamp_css(m):
        head, href, _, tail = m.groups()
        full = os.path.join(ROOT, href.replace("/", os.sep))
        if not os.path.exists(full):
            print(f"  ! нет файла {href}")
            return m.group(0)
        return f"{head}{href}?v={digest_of([full])}{tail}"

    html = CSS_LINK.sub(stamp_css, html)

    block = (
        "  <!-- карта модулей -->\n"
        "  <!-- Приложение собрано в один файл (tools/stamp.py): те же\n"
        "       модули, но одним походом по сети вместо тридцати двух.\n"
        "       Исходники лежат рядом и остаются модулями — правят их. -->\n"
        f'  <link rel="modulepreload" href="js/bundle.js?v={version}">\n'
        "  <!-- /карта модулей -->\n")

    boot = (
        "  <!-- точка входа -->\n"
        f'  <script type="module" src="js/bundle.js?v={version}"></script>\n'
        "  <!-- Сборка не выполнилась — подключаем исходные модули:\n"
        "       белый экран хуже лишнего запроса. -->\n"
        "  <script>\n"
        "    setTimeout(function () {\n"
        "      if (window.__mietBooted) return;\n"
        "      var s = document.createElement('script');\n"
        "      s.type = 'module';\n"
        f"      s.src = 'js/app.js?v={version}';\n"
        "      document.body.appendChild(s);\n"
        "    }, 2000);\n"
        "  </script>\n"
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
