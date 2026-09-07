# -*- coding: utf-8 -*-
"""
Доска взаимопомощи: «нужна помощь по матанализу» и «могу помочь со
схемотехникой».

Отдельно от ленты намеренно. У объявления другая жизнь: оно живёт, пока
вопрос не решён, и закрывается — а в хронологическом потоке рядом с
новостями его через неделю никто не найдёт.

Главное отличие от остального приложения: **ник автора виден всем**. Так
и задумано — объявление публикуют затем, чтобы с человеком связались, и
скрытый контакт делает раздел бессмысленным. Интерфейс обязан говорить
об этом прямо, до публикации, а не после.

Спам ограничен двумя рамками: сколько объявлений можно держать открытыми
и как часто их создавать. Модерация — правом `help_manage`.
"""
from __future__ import annotations

import re

from .db import conn
from .posts import Refused, _display_name

KINDS = ("need", "offer")
PRICES = ("free", "deal")

MAX_SUBJECT = 80
MAX_TEXT = 600

# Сколько объявлений один человек может держать открытыми. Больше пяти —
# это уже не «нужна помощь», а доска объявлений одного студента.
MAX_OPEN = 5

# Пауза между публикациями одного человека.
PAUSE = 60


def _clean(s: str, limit: int) -> str:
    return re.sub(r"[ \t]+", " ", str(s or "")).strip()[:limit]


FIELDS = ("h.id, h.user_id, h.kind, h.subject, h.text, h.price, h.status, "
          "h.created_at, u.first_name, u.username, u.group_name")


def _row(r) -> dict:
    return {
        "id": r[0], "author_id": r[1], "kind": r[2], "subject": r[3],
        "text": r[4], "price": r[5], "status": r[6], "created_at": r[7],
        "author_name": _display_name(r[8], r[9]),
        # Контакт — суть раздела, поэтому он в ответе для всех. Человек
        # соглашается на это, нажимая «Разместить»: экран говорит об этом
        # до публикации.
        "username": r[9] or "",
        "group": r[10] or "",
    }


def create(user_id: int, kind: str, subject: str, text: str = "",
           price: str = "free") -> dict:
    kind = kind if kind in KINDS else "need"
    price = price if price in PRICES else "free"
    subject = _clean(subject, MAX_SUBJECT)
    text = _clean(text, MAX_TEXT)
    if not subject:
        raise Refused("Укажи предмет")

    c = conn()
    open_now = c.execute(
        "SELECT COUNT(*) FROM help_offers WHERE user_id=? AND status='open'",
        (user_id,)).fetchone()[0]
    if open_now >= MAX_OPEN:
        raise Refused(f"У тебя уже {open_now} открытых объявлений — "
                      "закрой ненужные")
    recent = c.execute(
        """SELECT 1 FROM help_offers WHERE user_id=?
           AND created_at >= datetime('now', ?) LIMIT 1""",
        (user_id, f"-{PAUSE} seconds")).fetchone()
    if recent:
        raise Refused("Подожди минуту перед следующим объявлением")

    cur = c.execute(
        """INSERT INTO help_offers (user_id, kind, subject, text, price)
           VALUES (?, ?, ?, ?, ?)""", (user_id, kind, subject, text, price))
    return one(cur.lastrowid)


def one(offer_id: int) -> dict | None:
    row = conn().execute(
        f"""SELECT {FIELDS} FROM help_offers h
            LEFT JOIN users u ON u.user_id = h.user_id WHERE h.id=?""",
        (offer_id,)).fetchone()
    return _row(row) if row else None


def board(kind: str = "", q: str = "", limit: int = 50) -> dict:
    """Открытые объявления. Свежие сверху — старые уже, скорее всего, решены."""
    where = ["h.status='open'"]
    args = []
    if kind in KINDS:
        where.append("h.kind=?")
        args.append(kind)
    if q:
        # lower_ru — своя функция из db.py: обычный LIKE не знает регистра
        # кириллицы, и «матан» не находил «Матанализ».
        where.append("(lower_ru(h.subject) LIKE ?1 OR lower_ru(h.text) LIKE ?1)")
        args.append(f"%{q.lower()}%")
    sql = " AND ".join(where)
    rows = conn().execute(
        f"""SELECT {FIELDS} FROM help_offers h
            LEFT JOIN users u ON u.user_id = h.user_id
            WHERE {sql} ORDER BY h.id DESC LIMIT ?""",
        args + [max(1, min(limit, 100))]).fetchall()
    counts = dict(conn().execute(
        "SELECT kind, COUNT(*) FROM help_offers WHERE status='open' GROUP BY kind"))
    return {"offers": [_row(r) for r in rows],
            "need": counts.get("need", 0), "offer": counts.get("offer", 0)}


def mine(user_id: int) -> list:
    rows = conn().execute(
        f"""SELECT {FIELDS} FROM help_offers h
            LEFT JOIN users u ON u.user_id = h.user_id
            WHERE h.user_id=? ORDER BY h.id DESC LIMIT 50""",
        (user_id,)).fetchall()
    return [_row(r) for r in rows]


def close(offer_id: int) -> None:
    c = conn()
    c.execute("""UPDATE help_offers SET status='closed',
                 closed_at=CURRENT_TIMESTAMP WHERE id=?""", (offer_id,))


def reopen(offer_id: int) -> None:
    c = conn()
    c.execute("""UPDATE help_offers SET status='open', closed_at=NULL
                 WHERE id=?""", (offer_id,))


def delete(offer_id: int) -> None:
    conn().execute("DELETE FROM help_offers WHERE id=?", (offer_id,))


def stats() -> dict:
    c = conn()
    one_ = lambda sql: c.execute(sql).fetchone()[0]
    return {
        "open": one_("SELECT COUNT(*) FROM help_offers WHERE status='open'"),
        "closed": one_("SELECT COUNT(*) FROM help_offers WHERE status='closed'"),
        "need": one_("SELECT COUNT(*) FROM help_offers "
                     "WHERE status='open' AND kind='need'"),
        "offer": one_("SELECT COUNT(*) FROM help_offers "
                      "WHERE status='open' AND kind='offer'"),
    }
