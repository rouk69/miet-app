# -*- coding: utf-8 -*-
"""
Где бот хранит своё: базу пользователей и кеш расписания.

Локально это папка bot/ рядом с кодом. В облаке файлы рядом с кодом
переживают только до следующей выкладки — постоянное хранилище там
монтируется отдельным каталогом, поэтому путь берётся из DATA_DIR.
На Amvera это /data, он и стоит по умолчанию в amvera.yml.
"""
import os

DATA_DIR = os.environ.get("DATA_DIR") or os.path.dirname(os.path.abspath(__file__))


# Версия выложенного клиента. Её пишет tools/stamp.py рядом с кодом
# (не в DATA_DIR: это часть выкладки, а не накопленные данные).
VERSION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "webapp.version")


def webapp_version() -> str:
    """
    Метка выложенного мини-приложения — она уходит в адрес кнопки.

    Telegram кеширует страницу мини-приложения по адресу и держит её
    заметно дольше, чем просит HTTP: человек открывает приложение и
    видит вчерашний вид, а выкладка выглядит несделанной. Другой адрес
    — другая страница, и кеш обходится сам собой.

    Файла нет (запуск из чужой копии, старая выкладка) — работаем без
    метки: адрес без неё рабочий, просто обновится позже.
    """
    try:
        return open(VERSION_FILE, encoding="utf-8").read().strip()[:16]
    except OSError:
        return ""


def path(*parts: str) -> str:
    """Путь внутри хранилища; недостающие каталоги создаются сами."""
    p = os.path.join(DATA_DIR, *parts)
    os.makedirs(os.path.dirname(p) or DATA_DIR, exist_ok=True)
    return p
