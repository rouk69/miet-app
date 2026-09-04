# -*- coding: utf-8 -*-
"""
Настройки пользователей: группа и поправка недели.
SQLite, а не JSON-файл: бот отвечает в нескольких потоках, и одновременная
перезапись файла рано или поздно съела бы чужие записи.
"""
from __future__ import annotations

import os
import sqlite3
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
_local = threading.local()


def _conn() -> sqlite3.Connection:
    # У sqlite соединение нельзя делить между потоками, поэтому своё на поток.
    if not hasattr(_local, "conn"):
        c = sqlite3.connect(DB_PATH, timeout=10)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY,
            group_name TEXT,
            week_shift INTEGER DEFAULT 0,
            username   TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.commit()
        _local.conn = c
    return _local.conn


def get_user(user_id: int) -> dict:
    row = _conn().execute(
        "SELECT group_name, week_shift FROM users WHERE user_id=?",
        (user_id,)).fetchone()
    if not row:
        return {"group": None, "shift": 0}
    return {"group": row[0], "shift": row[1] or 0}


def set_group(user_id: int, group: str, username: str | None = None) -> None:
    c = _conn()
    c.execute("""INSERT INTO users (user_id, group_name, username, updated_at)
                 VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(user_id) DO UPDATE SET
                   group_name=excluded.group_name,
                   username=excluded.username,
                   updated_at=CURRENT_TIMESTAMP""",
              (user_id, group, username))
    c.commit()


def set_shift(user_id: int, shift: int) -> None:
    c = _conn()
    c.execute("""INSERT INTO users (user_id, week_shift, updated_at)
                 VALUES (?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(user_id) DO UPDATE SET
                   week_shift=excluded.week_shift,
                   updated_at=CURRENT_TIMESTAMP""",
              (user_id, shift % 4))
    c.commit()


def stats() -> dict:
    c = _conn()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    with_group = c.execute(
        "SELECT COUNT(*) FROM users WHERE group_name IS NOT NULL").fetchone()[0]
    return {"users": total, "with_group": with_group}
