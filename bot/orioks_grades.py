# -*- coding: utf-8 -*-
"""
Сторож баллов ОРИОКС: бот сам говорит, что поставили.

Ради этого ОРИОКС и открывают чаще всего — «поставили ли за лабу». Баллы
уже приходят в приложение вместе с заданиями, но узнать о новом можно
было, только зайдя и сверив глазами. Здесь обратный ход: преподаватель
выставил — человек получил сообщение.

Как и у объявлений (`orioks_watch`), **первый обход молчит**: к середине
семестра у студента десятки оценок, и «новое» на пустой памяти означало
бы все разом. Первый заход только запоминает.

**Самих баллов в базе нет.** Для сравнения хватает отпечатка — хеша
балла вместе с id человека; число в сообщение берётся из свежего ответа
ОРИОКС. Оценки — личное, и хранить их копию, чтобы заметить перемену,
незачем.

Перемена — это и новый балл, и исправленный старый (пересдал, ошибка
преподавателя), и снятый. Снятый не объявляем: «балл убрали» без
причины только пугает, а причина в ОРИОКС не пишется.
"""
from __future__ import annotations

import hashlib

from .db import conn
from .render import esc

# Отметка «этого человека уже обходили»: как PRIMED у объявлений. Без
# неё студент без единой оценки каждый раз выглядел бы новичком, и его
# первый балл молча ушёл бы в память вместо лички.
PRIMED = "-"

# Сколько строк в одном сообщении. Сессия выставляется пачками, и
# двадцать строк подряд уже не читают.
IN_MESSAGE = 6

# Что считать «недавним» для блока «Новые баллы» в приложении.
RECENT_DAYS = 14


def event_key(discipline_id, event: dict) -> str:
    """
    Устойчивое имя контрольной точки.

    У мероприятия ОРИОКС нет своего id, зато есть `alias` («dz.1», «ЛР.1»),
    уникальный внутри дисциплины. Если его нет — склеиваем то, что есть:
    неделю, вид и название.
    """
    alias = event.get("alias") or ""
    tail = alias or f"{event.get('week')}|{event.get('type')}|{event.get('name')}"
    return f"{discipline_id}:{tail}"


def _sig(user_id: int, grade) -> str:
    # Соль — id человека: одинаковый балл у двух людей даёт разные
    # отпечатки, и по таблице нельзя сказать «у них одно и то же».
    raw = f"{user_id}|{'' if grade is None else float(grade)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def points(data: dict) -> list:
    """Все контрольные точки из `orioks.tasks()` плоским списком."""
    out = []
    for d in (data or {}).get("disciplines", []):
        for e in d.get("events", []):
            out.append({
                "key": e.get("key") or event_key(d.get("id"), e),
                "discipline": d.get("name") or "Дисциплина",
                "discipline_id": d.get("id"),
                "name": e.get("name") or "Мероприятие",
                "grade": e.get("grade"),
                "max_grade": e.get("max_grade"),
            })
    return out


# ─────────────────────────── память ───────────────────────────

def _known(user_id: int) -> dict:
    return {k: s for k, s in conn().execute(
        "SELECT key, sig FROM orioks_grades WHERE user_id=?", (user_id,))}


def forget(user_id: int) -> None:
    """Отключил ОРИОКС — память о баллах уходит вместе с доступом."""
    conn().execute("DELETE FROM orioks_grades WHERE user_id=?", (user_id,))


def recent(user_id: int, days: int = RECENT_DAYS) -> dict:
    """Когда менялся каждый балл за последние дни: ключ → время UTC."""
    return {k: at for k, at in conn().execute(
        "SELECT key, changed_at FROM orioks_grades WHERE user_id=? "
        "AND changed_at IS NOT NULL AND changed_at >= datetime('now', ?)",
        (user_id, f"-{int(days)} days"))}


# ─────────────────────────── сравнение ───────────────────────────

def diff(user_id: int, data: dict, save: bool = True) -> list:
    """
    Что поменялось с прошлого обхода. Возвращает новые и исправленные
    баллы (снятые молча запоминаются).

    Первый обход возвращает пустой список и только запоминает. `save=False`
    — сухой прогон: смотрим, ничего не записывая, иначе проверка «что он
    сейчас видит» съела бы настоящее уведомление.
    """
    known = _known(user_id)
    first = not known
    changed, rows = [], []
    for p in points(data):
        sig = _sig(user_id, p["grade"])
        old = known.get(p["key"])
        if old == sig:
            continue
        rows.append((user_id, p["key"], sig, None if first else "now"))
        # Новая контрольная точка без балла — не событие: преподаватель
        # просто завёл мероприятие.
        if not first and p["grade"] is not None:
            changed.append({**p, "fixed": old is not None
                            and old != _sig(user_id, None)})
    if first:
        rows.append((user_id, PRIMED, "", None))
    if save and rows:
        with conn().transaction() as c:
            c.executemany(
                "INSERT INTO orioks_grades (user_id, key, sig, changed_at) "
                "VALUES (?, ?, ?, CASE WHEN ? IS NULL THEN NULL "
                "ELSE CURRENT_TIMESTAMP END) "
                "ON CONFLICT(user_id, key) DO UPDATE SET sig=excluded.sig, "
                "changed_at=COALESCE(excluded.changed_at, changed_at)",
                [(u, k, s, at) for u, k, s, at in rows])
    return changed


# ─────────────────────────── сообщение ───────────────────────────

def _num(x) -> str:
    if x is None:
        return "—"
    x = float(x)
    return str(int(x)) if x.is_integer() else f"{x:g}".replace(".", ",")


def message(changed: list, data: dict) -> str:
    """
    Одно сообщение обо всех новых баллах.

    Под каждым предметом — итог за семестр: «поставили 8» без контекста
    не отвечает на настоящий вопрос «как у меня по матану».
    """
    totals = {d.get("id"): d for d in (data or {}).get("disciplines", [])}
    head = ("📊 <b>Новый балл в ОРИОКС</b>" if len(changed) == 1
            else f"📊 <b>Новых баллов: {len(changed)}</b>")
    parts = [head, ""]
    by_subject: dict = {}
    for c in changed[:IN_MESSAGE]:
        by_subject.setdefault(c["discipline_id"], []).append(c)
    for did, items in by_subject.items():
        d = totals.get(did) or {}
        parts.append(f"<b>{esc(items[0]['discipline'])}</b>")
        for c in items:
            mark = " <i>(исправлен)</i>" if c.get("fixed") else ""
            parts.append(f"• {esc(c['name'])}: <b>{_num(c['grade'])}</b> "
                         f"из {_num(c['max_grade'])}{mark}")
        if d:
            parts.append(f"<i>Всего по предмету: {_num(d.get('current_grade') or 0)} "
                         f"из {_num(d.get('semester_max') or d.get('max_grade'))}</i>")
        parts.append("")
    if len(changed) > IN_MESSAGE:
        parts.append(f"<i>И ещё {len(changed) - IN_MESSAGE} — в приложении, "
                     f"раздел «Задания» → «Успеваемость».</i>")
    return "\n".join(parts).strip()
