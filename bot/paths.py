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


def path(*parts: str) -> str:
    """Путь внутри хранилища; недостающие каталоги создаются сами."""
    p = os.path.join(DATA_DIR, *parts)
    os.makedirs(os.path.dirname(p) or DATA_DIR, exist_ok=True)
    return p
