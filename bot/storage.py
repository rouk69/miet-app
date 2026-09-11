# -*- coding: utf-8 -*-
"""
Настройки пользователей: группа и поправка недели.
SQLite, а не JSON-файл: бот отвечает в нескольких потоках, и одновременная
перезапись файла рано или поздно съела бы чужие записи.

Схема и соединение переехали в db.py: та же таблица users хранит теперь и
профиль человека для админки, а два места, где она создаётся, однажды
разошлись бы в разные схемы.
"""
from __future__ import annotations

from .db import conn


def get_user(user_id: int) -> dict:
    row = conn().execute(
        "SELECT group_name, week_shift, shift_semestr FROM users WHERE user_id=?",
        (user_id,)).fetchone()
    if not row:
        return {"group": None, "shift": 0, "shift_semestr": None}
    return {"group": row[0], "shift": row[1] or 0, "shift_semestr": row[2]}


def shift_for(user_id: int, semestr: str) -> int:
    """
    Поправка недели, если она настраивалась для этого же семестра.

    Цикл в новом семестре начинается заново, и сдвиг, выставленный осенью,
    весной почти наверняка окажется другим. Молча применять старый нельзя —
    человек увидел бы не ту неделю и не понял почему. Поэтому при смене
    семестра поправка обнуляется.
    """
    u = get_user(user_id)
    if not u["shift"]:
        return 0
    if semestr and u["shift_semestr"] and u["shift_semestr"] != semestr:
        set_shift(user_id, 0, semestr)
        return 0
    return u["shift"]


def set_group(user_id: int, group: str, username: str | None = None) -> None:
    c = conn()
    # NULLIF: мини-приложение знает ник не всегда, и пустая строка оттуда не
    # должна стирать ник, добытый ботом.
    c.execute("""INSERT INTO users (user_id, group_name, username, updated_at)
                 VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(user_id) DO UPDATE SET
                   group_name=excluded.group_name,
                   username=COALESCE(NULLIF(excluded.username, ''), users.username),
                   updated_at=CURRENT_TIMESTAMP""",
              (user_id, group, username))
    c.commit()


def set_shift(user_id: int, shift: int, semestr: str | None = None) -> None:
    c = conn()
    c.execute("""INSERT INTO users (user_id, week_shift, shift_semestr, updated_at)
                 VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(user_id) DO UPDATE SET
                   week_shift=excluded.week_shift,
                   shift_semestr=excluded.shift_semestr,
                   updated_at=CURRENT_TIMESTAMP""",
              (user_id, shift % 4, semestr))
    c.commit()


def stats() -> dict:
    c = conn()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    with_group = c.execute(
        "SELECT COUNT(*) FROM users WHERE group_name IS NOT NULL").fetchone()[0]
    return {"users": total, "with_group": with_group}

def popular_groups(limit: int = 15) -> list[str]:
    """
    Группы, которые спрашивают чаще других.

    Нужны для прогрева: после перезапуска контейнера кеш расписания
    пуст, и первый же человек ждёт полторы секунды сетевого запроса.
    Пятнадцати групп хватает: у бота их несколько сотен, но обращаются
    в основном к своим.
    """
    rows = conn().execute(
        "SELECT group_name, COUNT(*) AS n FROM users "
        "WHERE group_name IS NOT NULL AND group_name<>'' "
        "GROUP BY group_name ORDER BY n DESC LIMIT ?", (limit,))
    return [r[0] for r in rows]

# ─────────────── утренняя карточка дня ───────────────

def morning_on(user_id: int) -> bool:
    row = conn().execute("SELECT morning FROM users WHERE user_id=?",
                         (user_id,)).fetchone()
    return bool(row and row[0])


def set_morning(user_id: int, on: bool) -> None:
    """Включает или выключает утреннюю рассылку для человека."""
    conn().execute(
        "INSERT INTO users (user_id, morning) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET morning=excluded.morning",
        (user_id, 1 if on else 0))


def morning_list() -> list:
    """
    Кому слать: подписанные, у кого выбрана группа.

    Без группы карточку не собрать, а звать выбирать её сообщением в
    половине восьмого — худшее, что можно сделать с утра.
    """
    return [(r[0], r[1], r[2] or "") for r in conn().execute(
        "SELECT user_id, group_name, morning_at FROM users "
        "WHERE COALESCE(morning, 0)=1 AND group_name IS NOT NULL "
        "AND group_name<>''")]


def morning_sent(user_id: int, day: str) -> None:
    """Помечает, что за этот день человеку уже написали."""
    conn().execute("UPDATE users SET morning_at=? WHERE user_id=?",
                   (day, user_id))
