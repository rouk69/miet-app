# -*- coding: utf-8 -*-
"""
Справочник преподавателей и аудиторий.

miet.ru отдаёт расписание только по группе. Вопрос, с которого начинается
половина студенческих поисков — «где сейчас Иванов» или «свободна ли
3105» — таким API не отвечается вовсе: пришлось бы спросить сайт про все
346 групп и сложить ответы.

Поэтому раз в сутки бот делает это сам и складывает плоский слепок в
`lessons_index`. Дальше поиск — обычный запрос к своей базе, мгновенный.

Обход намеренно неспешный: между группами пауза, и запускается он не при
старте, а спустя несколько минут. Триста сорок шесть запросов подряд к
чужому сайту — это то, за что банят, и торопиться тут некуда: расписание
на семестр меняется редко.
"""
from __future__ import annotations

import logging
import re
import threading
import time

from . import schedule_api as api
from .db import conn

log = logging.getLogger("miet.directory")

# Раз в сутки. Расписание на семестр стабильно, а замены МИЭТ публикует
# в самом расписании — их подхватит следующий обход.
EVERY = 24 * 60 * 60

# Пауза между группами. При 346 группах это около трёх минут на полный
# проход — незаметно для чужого сервера и не мешает боту отвечать.
PAUSE = 0.4

# Ждём после старта: сначала должен подняться опрос Telegram и API.
DELAY = 5 * 60

# Через сколько повторить, если обход не удался. Сутки без справочника
# из-за одной неудачной попытки — слишком дорого.
RETRY = 60 * 60


# Что происходит прямо сейчас. Снаружи это единственный способ отличить
# «обход идёт» от «обход упал»: логи Amvera видны только владельцу, а
# пустой индекс выглядит одинаково в обоих случаях.
state = {"running": False, "done": 0, "total": 0, "failed": 0,
         "started_at": None, "error": ""}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def rebuild() -> int:
    """
    Пересобирает индекс. Возвращает число записей.

    Собираем всё в память и меняем таблицу одной транзакцией: если сайт
    отвалится на середине, лучше оставить вчерашний полный индекс, чем
    получить половину сегодняшнего.
    """
    state.update(running=True, done=0, total=0, failed=0, error="",
                 started_at=time.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        groups = api.fetch_groups()
    except Exception as e:
        log.warning("список групп недоступен: %s", e)
        state.update(running=False, error=f"список групп: {e}")
        return 0

    state["total"] = len(groups)
    rows, semestr, failed = [], "", 0
    for i, group in enumerate(groups):
        try:
            sched = api.fetch_schedule(group)
        except Exception:
            failed += 1
            continue
        semestr = semestr or sched.get("semestr") or ""
        for l in sched.get("lessons", []):
            teacher = _norm(l.get("teacher"))
            if not teacher:
                continue
            rows.append((teacher, _norm(l.get("room")), _norm(l.get("subject")),
                         l.get("kindCls") or "", group, l.get("day"),
                         l.get("week"), l.get("pair"), l.get("from"), l.get("to")))
        state["done"], state["failed"] = i + 1, failed
        if i % 50 == 0 and i:
            log.info("справочник: %d из %d групп", i, len(groups))
        time.sleep(PAUSE)

    if not rows:
        log.warning("справочник не собрался: ни одной записи (групп %d, "
                    "неудачных %d)", len(groups), failed)
        state.update(running=False,
                     error=f"пусто: групп {len(groups)}, недоступно {failed}")
        return 0

    with conn().transaction() as raw:
        raw.execute("DELETE FROM lessons_index")
        raw.executemany(
            """INSERT INTO lessons_index
                 (teacher, room, subject, kind, group_name, day, week, pair,
                  t_from, t_to)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", rows)
        raw.execute("""INSERT INTO index_meta (key, value) VALUES ('built_at',
                       datetime('now')) ON CONFLICT(key) DO UPDATE SET
                       value=excluded.value""")
        raw.execute("""INSERT INTO index_meta (key, value) VALUES ('semestr', ?)
                       ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                    (semestr,))
    log.info("справочник собран: %d записей, групп %d, недоступно %d",
             len(rows), len(groups), failed)
    state.update(running=False, error="")
    return len(rows)


def meta() -> dict:
    rows = dict(conn().execute("SELECT key, value FROM index_meta"))
    total = conn().execute("SELECT COUNT(*) FROM lessons_index").fetchone()[0]
    return {"built_at": rows.get("built_at"), "semestr": rows.get("semestr"),
            "lessons": total, "progress": dict(state)}


# ─────────────────────────── поиск ───────────────────────────

# У физкультуры, военной подготовки и практик МИЭТ ставит в расписание не
# фамилию, а заглушку «Преподаватель ФВ», «Преподаватель П.П.». Пар у них
# тысячи, поэтому в списке они забивают весь верх, а найти по ним никого
# нельзя. Из поиска убираем, из расписания аудиторий — нет: там эта пара
# занимает кабинет так же, как любая другая.
PLACEHOLDER = "Преподаватель%"


def teachers(q: str = "", limit: int = 40) -> list:
    """Преподаватели с числом пар. Пустой запрос — самые загруженные."""
    c = conn()
    if q:
        rows = c.execute(
            """SELECT teacher, COUNT(*) n, COUNT(DISTINCT group_name) g
               FROM lessons_index
               WHERE lower_ru(teacher) LIKE ? AND teacher NOT LIKE ?
               GROUP BY teacher ORDER BY teacher LIMIT ?""",
            (f"%{q.lower()}%", PLACEHOLDER, max(1, min(limit, 100)))).fetchall()
    else:
        rows = c.execute(
            """SELECT teacher, COUNT(*) n, COUNT(DISTINCT group_name) g
               FROM lessons_index WHERE teacher NOT LIKE ?
               GROUP BY teacher ORDER BY n DESC LIMIT ?""",
            (PLACEHOLDER, max(1, min(limit, 100)))).fetchall()
    return [{"name": t, "lessons": n, "groups": g} for t, n, g in rows]


def _slots(rows) -> list:
    """
    Схлопывает пары, которые идут у нескольких групп одновременно.

    У преподавателя лекция на потоке — это одна пара, а в расписании она
    записана отдельно для каждой группы. Без склейки его день выглядел бы
    вчетверо длиннее, чем он есть.
    """
    out = {}
    for teacher, room, subject, kind, group, day, week, pair, t_from, t_to in rows:
        key = (week, day, pair, subject, room)
        slot = out.setdefault(key, {
            "week": week, "day": day, "pair": pair, "subject": subject,
            "kind": kind, "room": room, "from": t_from, "to": t_to,
            "teacher": teacher, "groups": [],
        })
        if group not in slot["groups"]:
            slot["groups"].append(group)
    return sorted(out.values(),
                  key=lambda s: (s["week"], s["day"], s["pair"] or 0))


FIELDS = ("teacher, room, subject, kind, group_name, day, week, pair, "
          "t_from, t_to")


def teacher_schedule(name: str) -> dict:
    rows = conn().execute(
        f"SELECT {FIELDS} FROM lessons_index WHERE teacher = ?", (name,))
    slots = _slots(rows)
    rooms = sorted({s["room"] for s in slots if s["room"]})
    groups = sorted({g for s in slots for g in s["groups"]})
    subjects = sorted({s["subject"] for s in slots if s["subject"]})
    return {"name": name, "slots": slots, "rooms": rooms,
            "groups": groups, "subjects": subjects}


def rooms(q: str = "", limit: int = 60) -> list:
    c = conn()
    where = "WHERE room <> ''" + (" AND lower_ru(room) LIKE ?" if q else "")
    args = ([f"%{q.lower()}%"] if q else []) + [max(1, min(limit, 200))]
    rows = c.execute(
        f"""SELECT room, COUNT(*) n FROM lessons_index {where}
            GROUP BY room ORDER BY room LIMIT ?""", args).fetchall()
    return [{"name": r, "lessons": n} for r, n in rows]


def room_schedule(name: str) -> dict:
    rows = conn().execute(
        f"SELECT {FIELDS} FROM lessons_index WHERE room = ?", (name,))
    slots = _slots(rows)
    return {"name": name, "slots": slots,
            "teachers": sorted({s["teacher"] for s in slots if s["teacher"]})}


def now_teaching(week: int, day: int, pair: int) -> list:
    """Кто и где ведёт в этот слот. Для вопроса «где он сейчас»."""
    rows = conn().execute(
        f"""SELECT {FIELDS} FROM lessons_index
            WHERE week=? AND day=? AND pair=?""", (week, day, pair))
    return _slots(rows)


# ─────────────────────────── фон ───────────────────────────

def run_in_background() -> threading.Thread:
    def loop():
        time.sleep(DELAY)
        while True:
            wait = EVERY
            try:
                # Если индекс уже собран сегодня — не трогаем сайт лишний
                # раз: перезапуск контейнера не повод обходить 346 групп.
                built = meta()
                if built["lessons"] and not _stale(built["built_at"]):
                    log.info("справочник свежий (%d записей), обход не нужен",
                             built["lessons"])
                else:
                    log.info("справочник: начинаю обход групп")
                    if not rebuild():
                        # Сутки без справочника из-за одной неудачной
                        # попытки — слишком дорого. Пробуем снова через час.
                        wait = RETRY
            except Exception:
                log.exception("сбор справочника сорвался")
                state.update(running=False, error="сорвался, см. лог")
                wait = RETRY
            time.sleep(wait)

    t = threading.Thread(target=loop, name="directory", daemon=True)
    t.start()
    return t


def _stale(built_at: str | None) -> bool:
    if not built_at:
        return True
    row = conn().execute(
        "SELECT ? < datetime('now', '-20 hours')", (built_at,)).fetchone()
    return bool(row and row[0])
