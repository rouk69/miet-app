# -*- coding: utf-8 -*-
"""
Метка версии на статике: чтобы правка доходила до людей сразу.

GitHub Pages отдаёт файлы с десятиминутным кешем, а Telegram держит их
дольше и по своим правилам. После выкладки человек открывает
мини-приложение и видит вчерашний вид — правка выглядит так, будто её
не делали.

Лечится адресом: `app.css?v=3f2a1b` — другой адрес, значит другой файл,
значит запросить заново. Метка считается от содержимого и меняется
ровно тогда, когда менялись файлы.

**Модулям адрес меняет карта импортов.** Приписать версию к
`<script src="js/app.js">` мало: внутри модули тянут друг друга своими
путями, и те останутся кешированными — получилась бы каша из нового
app.js и вчерашнего ui.js. Поэтому здесь генерируется importmap,
которая подменяет адрес каждому модулю разом, а точка входа
подключается инлайновым `import './js/app.js'` — он тоже проходит
через карту. Браузер без поддержки importmap (iOS до 16.4) возьмёт всё
дерево по старым адресам: не свежо, зато согласованно.

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

CSS_LINK = re.compile(r'(<link[^>]*href=")(css/[\w.-]+\.css)(\?v=[0-9a-f]+)?(")')
MAP_BLOCK = re.compile(
    r"[ \t]*<!-- карта модулей -->.*?<!-- /карта модулей -->\n", re.S)
BOOT_BLOCK = re.compile(
    r"[ \t]*<!-- точка входа -->.*?<!-- /точка входа -->\n", re.S)


def digest_of(paths) -> str:
    h = hashlib.sha1()
    for path in sorted(paths):
        h.update(io.open(path, "rb").read())
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


def main() -> int:
    html = io.open(INDEX, encoding="utf-8").read()
    before = html

    # ── стили: у каждого своя метка, они правятся порознь
    def stamp_css(m):
        head, href, _, tail = m.groups()
        full = os.path.join(ROOT, href.replace("/", os.sep))
        if not os.path.exists(full):
            print(f"  ! нет файла {href}")
            return m.group(0)
        return f"{head}{href}?v={digest_of([full])}{tail}"

    html = CSS_LINK.sub(stamp_css, html)

    # ── модули: метка общая, потому что рвутся они тоже вместе
    mods = modules()
    version = digest_of([full for full, _ in mods])
    imports = ",\n".join(
        f'    "./{href}": "./{href}?v={version}"' for _, href in mods)

    preload = [
        "js/app.js", "js/router.js", "js/store.js", "js/ui.js", "js/icons.js",
        "js/tg.js", "js/api.js", "js/config.js", "js/schedule.js",
        "js/screens/common.js", "js/screens/home.js", "js/screens/schedule.js",
        "js/screens/feed.js",
    ]
    lines = "\n".join(
        f'  <link rel="modulepreload" href="{p}?v={version}">' for p in preload)

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
        f"{lines}\n"
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

    # Метка всей выкладки — она уходит в адрес кнопки мини-приложения.
    # Telegram кеширует страницу по адресу и держит её дольше, чем просит
    # HTTP: без другого адреса человек открывает вчерашний вид, и правка
    # выглядит несделанной. Считается по стилям и модулям разом — вид
    # правится чаще логики, а обновиться должно и то и другое.
    css = [os.path.join(ROOT, "css", n)
           for n in sorted(os.listdir(os.path.join(ROOT, "css")))
           if n.endswith(".css")]
    whole = digest_of(css + [full for full, _ in mods])
    stamp_file = os.path.join(ROOT, "webapp.version")
    was = ""
    if os.path.exists(stamp_file):
        was = io.open(stamp_file, encoding="utf-8").read().strip()
    if was != whole:
        io.open(stamp_file, "w", encoding="utf-8").write(whole + chr(10))
        print(f"версия выкладки: {was or '(не было)'} → {whole}")

    if html == before:
        print("метки в index.html на месте")
        return 0
    io.open(INDEX, "w", encoding="utf-8").write(html)
    print(f"метки обновлены: модулей {len(mods)}, версия модулей {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
