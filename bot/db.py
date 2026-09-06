# -*- coding: utf-8 -*-
"""
Соединение с SQLite и вся схема в одном месте.

Раньше единственную таблицу заводил storage.py прямо в своём _conn(). С
появлением админки данных стало больше: кроме группы и сдвига недели база
держит профиль человека, поток событий и роли. Схема, размазанная по
модулям, рано или поздно расходится — поэтому все CREATE TABLE и миграции
собраны здесь, а модули пишут только запросы.

Соединение своё на поток: sqlite не разрешает делить одно между потоками, а
их тут много — telebot работает threaded, плюс отдельный поток HTTP-сервера.

Время в базе всегда UTC (CURRENT_TIMESTAMP, datetime('now')), потому что в
облаке часовой пояс контейнера UTC, а на ноутбуке — московский, и хранить
«местное» значило бы получить базу с двумя разными шкалами. Для показа и
группировки по дням прибавляем MSK — иначе сутки в отчёте резались бы в
три часа ночи.
"""
from __future__ import annotations

import sqlite3
import threading

from . import paths

DB_PATH = paths.path("users.db")

# Сдвиг московского времени для SQL-функций дат. Города МИЭТа — Зеленоград,
# отчёты смотрят по местному времени, а не по UTC.
MSK = "+3 hours"

_local = threading.local()

SCHEMA = [
    # Настройки и профиль человека. Строка появляется, как только он написал
    # боту или открыл мини-приложение, — то есть это же и список «юзеров».
    """CREATE TABLE IF NOT EXISTS users (
        user_id    INTEGER PRIMARY KEY,
        group_name TEXT,
        week_shift INTEGER DEFAULT 0,
        username   TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    # Поток событий: заходы в приложение, открытия вкладок и экранов,
    # команды боту. Из него считается вся статистика.
    """CREATE TABLE IF NOT EXISTS events (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        kind    TEXT NOT NULL,
        name    TEXT,
        ts      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS events_ts ON events(ts)",
    "CREATE INDEX IF NOT EXISTS events_user ON events(user_id, ts)",
    "CREATE INDEX IF NOT EXISTS events_kind ON events(kind, ts)",
    # Роли и доступы. Отдельной таблицей, а не столбцами в users: строка
    # здесь есть только у тех, кому что-то выдали, — их единицы.
    """CREATE TABLE IF NOT EXISTS roles (
        user_id    INTEGER PRIMARY KEY,
        role       TEXT NOT NULL DEFAULT 'none',
        perms      TEXT NOT NULL DEFAULT '[]',
        sections   TEXT NOT NULL DEFAULT '[]',
        blocked    INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
]

# Столбцы, доросшие к users позже. У баз, созданных до админки, их нет —
# ALTER TABLE ADD COLUMN дешёвый и на живой базе безопасен.
ADDED_COLUMNS = [
    ("shift_semestr", "TEXT"),
    ("first_name", "TEXT"),
    ("last_name", "TEXT"),
    ("photo_url", "TEXT"),
    ("language", "TEXT"),
    ("is_premium", "INTEGER DEFAULT 0"),
    ("first_seen", "TEXT"),
    ("last_seen", "TEXT"),
    ("opens", "INTEGER DEFAULT 0"),
    ("seen_bot", "INTEGER DEFAULT 0"),
    ("seen_app", "INTEGER DEFAULT 0"),
]


def conn() -> sqlite3.Connection:
    """Соединение текущего потока; схема доводится до актуальной при первом."""
    c = getattr(_local, "conn", None)
    if c is not None:
        return c
    c = sqlite3.connect(DB_PATH, timeout=10)
    # WAL: читатели (HTTP-сервер) не ждут писателей (бот) и наоборот.
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=10000")
    for stmt in SCHEMA:
        c.execute(stmt)
    have = {r[1] for r in c.execute("PRAGMA table_info(users)")}
    for name, decl in ADDED_COLUMNS:
        if name not in have:
            c.execute(f"ALTER TABLE users ADD COLUMN {name} {decl}")
    c.commit()
    _local.conn = c
    return c


def reset_for_tests(path: str) -> None:
    """
    Переключает модуль на другую базу. Нужен только тестам: они не должны
    писать в живую users.db, иначе прогон испортит настоящую статистику.
    """
    global DB_PATH
    DB_PATH = path
    if hasattr(_local, "conn"):
        _local.conn.close()
        del _local.conn
