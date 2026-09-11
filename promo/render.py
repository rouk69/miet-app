# -*- coding: utf-8 -*-
"""
Рендер промо-карточки в PNG через headless Chrome (или Edge).

    python promo/render.py                 → promo/mietapp-card.png
    python promo/render.py card.html x.png → свои пути

Шрифты вшиваются в копию страницы base64: Chrome по file:// считает
каждый файл отдельным источником и молча отказывает @font-face в
загрузке соседних файлов — карточка вышла бы системным шрифтом.
Картинка снимается с двукратной плотностью, 2160×2700: Telegram ужмёт
её до своих 2560 по длинной стороне, и текст останется чётким.
"""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

# Консоль Windows по умолчанию в cp1251 и падает на «×» в итоговой строке.
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, SCALE = 1080, 1350, 2
SLACK = 200   # запас по высоте окна Chrome, см. main()

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def find_browser() -> str:
    for b in BROWSERS:
        if os.path.isfile(b) or shutil.which(b):
            return b if os.path.isfile(b) else shutil.which(b)
    sys.exit("Не нашёл Chrome или Edge — поставь любой из них.")


def inline_fonts(html: str, base: str) -> str:
    def repl(m: re.Match) -> str:
        path = os.path.normpath(os.path.join(base, m.group(1)))
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"url('data:font/woff2;base64,{data}')"
    return re.sub(r"url\('([^']+\.woff2)'\)", repl, html)


def main() -> None:
    src = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "card.html")
    out = os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else "mietapp-card.png")

    html = inline_fonts(open(src, encoding="utf-8").read(), os.path.dirname(src))
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "card.html")
        shot = os.path.join(tmp, "shot.png")
        open(page, "w", encoding="utf-8").write(html)
        # Новый headless Chrome отдаёт странице окно примерно на 80 px ниже
        # заявленного: снимок нужного размера, а низ в нём не нарисован —
        # кнопка внизу карточки выходила срезанной пополам. Поэтому снимаем
        # с запасом по высоте и отрезаем ровно карточку.
        subprocess.run([
            find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--force-device-scale-factor={SCALE}", f"--window-size={W},{H + SLACK}",
            "--virtual-time-budget=3000", f"--screenshot={shot}",
            "file:///" + page.replace("\\", "/"),
        ], check=True, capture_output=True, timeout=90)
        Image.open(shot).crop((0, 0, W * SCALE, H * SCALE)).save(out, optimize=True)

    size = os.path.getsize(out) / 1024
    print(f"готово: {out} — {W * SCALE}×{H * SCALE}, {size:.0f} КБ")


if __name__ == "__main__":
    main()
