#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полное обновление данных приложения с miet.ru.

    pip install requests beautifulsoup4 pillow
    python tools/update.py

Порядок шагов важен: harvest и clubs складывают сырьё в tools/_raw,
build_data сжимает фото и собирает из сырья data/app.json.
Занимает 12–15 минут — сайт отвечает небыстро.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("harvest.py", "новости, институты, разделы кампуса"),
    ("clubs.py", "секции при ДК и спорткомплексе"),
    ("student_clubs.py", "студенческие сообщества (22 клуба)"),
    ("build_data.py", "сжатие фото и сборка data/app.json"),
]


def main():
    t0 = time.time()
    for script, what in STEPS:
        print(f"\n{'=' * 60}\n▶ {script} — {what}\n{'=' * 60}")
        r = subprocess.run([sys.executable, os.path.join(HERE, script)])
        if r.returncode != 0:
            sys.exit(f"Шаг {script} завершился с ошибкой {r.returncode}")
    print(f"\nГотово за {time.time() - t0:.0f} с. Обновлены data/app.json и img/.")


if __name__ == "__main__":
    main()
