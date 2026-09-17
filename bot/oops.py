# -*- coding: utf-8 -*-
"""
Поломки на стороне клиента: что у людей упало и на каком экране.

До этого модуля любая ошибка в приложении была видна ровно одному
человеку — тому, у кого она случилась. Белый экран, не нажимающаяся
кнопка, пустая лента: он закрывал приложение и уходил, а мы узнавали об
этом, только если он писал в поддержку. За всё время так нашлись
несколько багов, и каждый — случайно.

Браузера в среде разработки нет, глазами клиент не проверить, поэтому
единственный честный способ узнать о поломке — попросить сам клиент
рассказать.

**Ошибки складываются по отпечатку, а не по одной.** Одна и та же
поломка у двухсот человек — это одна строка со счётчиком, а не двести
строк: иначе первая же мелочь вытеснит из таблицы всё остальное, и
читать её станет невозможно.

Что НЕ пишется: ничего личного. Текст ошибки, экран, версия сборки и
платформа. Идентификатор человека хранится только последний — чтобы
можно было спросить «у тебя сейчас открывалось?», а не чтобы вести
досье.
"""
from __future__ import annotations

import logging
import re

from .db import conn

log = logging.getLogger("miet.oops")

MAX_MESSAGE = 300
MAX_STACK = 1200
MAX_FIELD = 64

# Сколько разных поломок помним. Больше — это уже не список ошибок, а
# свалка: всё равно чинится то, что вверху по счётчику.
KEEP = 300


def _clean(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def fingerprint(message: str, source: str, line) -> str:
    """
    Чем одна поломка отличается от другой.

    Номера в тексте выбрасываются: «Не удалось загрузить пост 412» и
    «...пост 987» — одна и та же ошибка, и держать их порознь значит
    потерять счётчик, ради которого всё затевалось.
    """
    body = re.sub(r"\d+", "#", _clean(message, MAX_MESSAGE).lower())
    where = _clean(source, MAX_FIELD).rsplit("/", 1)[-1]
    return f"{body}|{where}|{line or ''}"


def report(user_id: int, data: dict) -> dict:
    """
    Записать поломку. Возвращает {ok, count} — сколько раз её уже видели.

    Ничего не поднимает наружу: отчёт об ошибке, сам падающий с ошибкой,
    — это худшее, что может случиться с этим маршрутом.
    """
    try:
        message = _clean(data.get("message"), MAX_MESSAGE)
        if not message:
            return {"ok": False}
        source = _clean(data.get("source"), MAX_FIELD)
        line = data.get("line")
        line = int(line) if str(line or "").lstrip("-").isdigit() else None
        key = fingerprint(message, source, line)
        c = conn()
        c.execute(
            """INSERT INTO client_errors
                   (fingerprint, message, source, line, stack, build,
                    screen, platform, version, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(fingerprint) DO UPDATE SET
                 count = count + 1,
                 last_at = CURRENT_TIMESTAMP,
                 screen = excluded.screen,
                 build = excluded.build,
                 user_id = excluded.user_id""",
            (key, message, source, line,
             _clean(data.get("stack"), MAX_STACK),
             _clean(data.get("build"), MAX_FIELD),
             _clean(data.get("screen"), MAX_FIELD),
             _clean(data.get("platform"), MAX_FIELD),
             _clean(data.get("version"), MAX_FIELD),
             int(user_id or 0)))
        row = c.execute("SELECT count FROM client_errors WHERE fingerprint=?",
                        (key,)).fetchone()
        _trim()
        return {"ok": True, "count": int(row[0]) if row else 1}
    except Exception:                                       # noqa: BLE001
        log.exception("отчёт о поломке не записался")
        return {"ok": False}


def _trim() -> None:
    """Держим список коротким: лишнее — самое старое по последней встрече."""
    conn().execute(
        """DELETE FROM client_errors WHERE id NOT IN (
               SELECT id FROM client_errors ORDER BY last_at DESC LIMIT ?)""",
        (KEEP,))


def recent(limit: int = 50) -> list:
    """
    Поломки: свежие сверху, но с числом повторов — чинить надо частое.

    Сортировка именно по последней встрече, а не по счётчику: ошибка,
    которую уже починили, остаётся в таблице с большим числом, и наверху
    она бы всех обманывала.
    """
    rows = conn().execute(
        """SELECT id, message, source, line, stack, build, screen,
                  platform, version, user_id, count, first_at, last_at
             FROM client_errors ORDER BY last_at DESC LIMIT ?""",
        (max(1, min(int(limit or 50), 200)),)).fetchall()
    return [{
        "id": r[0], "message": r[1], "source": r[2], "line": r[3],
        "stack": r[4], "build": r[5], "screen": r[6], "platform": r[7],
        "version": r[8], "user_id": r[9], "count": r[10],
        "first_at": r[11], "last_at": r[12],
    } for r in rows]


def totals() -> dict:
    row = conn().execute(
        """SELECT COUNT(*), COALESCE(SUM(count), 0),
                  COALESCE(SUM(CASE WHEN last_at >= datetime('now', '-1 day')
                                    THEN count ELSE 0 END), 0)
             FROM client_errors""").fetchone()
    return {"kinds": row[0], "total": row[1], "day": row[2]}


def forget(error_id: int = 0) -> int:
    """
    Убрать разобранное. Без номера — стереть всё.

    Нужно после выкладки починки: иначе старые записи висят вперемешку с
    новыми, и непонятно, помогло или нет.
    """
    c = conn()
    if error_id:
        cur = c.execute("DELETE FROM client_errors WHERE id=?", (int(error_id),))
    else:
        cur = c.execute("DELETE FROM client_errors")
    return cur.rowcount
