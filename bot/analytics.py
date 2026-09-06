# -*- coding: utf-8 -*-
"""
Учёт происходящего: кто пользуется приложением и ботом, какие разделы
смотрит, у кого какая роль. Отсюда админка берёт все цифры.

Событие пишется одной строкой и никогда не редактируется — так статистику
можно пересчитать под любым углом задним числом, не заводя новых счётчиков.
Единственное исключение — users.opens: счётчик заходов нужен в списке
юзеров, а считать его там каждый раз по всей таблице событий дорого.

Чего в базе нет принципиально: текстов сообщений, поисковых запросов,
содержимого чужих чатов. Только идентификатор человека, открытая часть его
профиля из Telegram и названия открытых разделов.
"""
from __future__ import annotations

import json

from .db import MSK, conn

# ─────────────────────────── роли ───────────────────────────

# Права модератора. Порядок важен: в этом же виде они показываются
# тумблерами в админке. Часть относится к разделам, которых в приложении
# ещё нет, — они заведены заранее, чтобы выдача прав не требовала правки
# базы, когда разделы появятся.
PERMS = [
    ("stats", "Видеть статистику и юзеров"),
    ("posts_write", "Писать посты в ленту"),
    ("posts_anon", "Публиковать анонимно без одобрения"),
    ("posts_moderate", "Одобрять анонимные посты"),
    ("posts_delete", "Удалять посты"),
    ("comments_delete", "Удалять комментарии"),
    ("posts_pin", "Закреплять посты сверху ленты"),
    ("users_block", "Блокировать пользователей"),
    ("dates_add", "Добавлять ключевые даты"),
    ("clubs_manage", "Управлять составом и лентами кружков"),
    ("help_manage", "Управлять разделом «Помощь в заданиях»"),
    ("files_moderate", "Модерировать «Полезные файлы»"),
]
PERM_IDS = [p for p, _ in PERMS]

ROLES = ("admin", "moderator", "none")


def _json_list(raw: str) -> list:
    try:
        v = json.loads(raw or "[]")
        return v if isinstance(v, list) else []
    except (TypeError, ValueError):
        return []


def identity(user_id: int, root_admins=frozenset()) -> dict:
    """
    Кто этот человек с точки зрения прав.

    Владельцы из ADMIN_IDS — корневые: их роль не хранится в базе и её
    нельзя снять из интерфейса. Иначе одним неверным тапом можно было бы
    закрыть себе доступ в админку и остаться без единственного ключа.
    """
    row = conn().execute(
        "SELECT role, perms, sections, blocked FROM roles WHERE user_id=?",
        (user_id,)).fetchone()
    role, perms, sections, blocked = row or ("none", "[]", "[]", 0)
    root = user_id in root_admins
    if root:
        role = "admin"
    # Блокировка отбирает доступ, но не стирает роль: разблокировали —
    # права вернулись те же. Отдавать их заблокированному нельзя, иначе
    # разжалованный модератор продолжал бы открывать админку.
    shut = bool(blocked) and not root
    full = role == "admin" and not shut
    granted = PERM_IDS[:] if role == "admin" else [
        p for p in _json_list(perms) if p in PERM_IDS]
    saved_sections = _json_list(sections)
    return {
        "id": user_id,
        "role": role,
        "root": root,
        # perms — что человек может прямо сейчас; granted — что ему выдано.
        # Расходятся они только у заблокированного, и админка рисует
        # тумблеры по granted, иначе снятие блокировки стирало бы права.
        "perms": [] if shut else granted,
        "granted": granted,
        "sections": [] if shut else saved_sections,
        "granted_sections": saved_sections,
        "blocked": shut,
        "is_admin": full,
    }


def can(ident: dict, perm: str) -> bool:
    """Право есть у полного админа всегда, у модератора — если выдано."""
    return bool(ident.get("is_admin")) or perm in ident.get("perms", [])


def set_role(user_id: int, role: str, perms: list, sections: list) -> None:
    if role not in ROLES:
        raise ValueError("неизвестная роль: " + str(role))
    keep = [p for p in perms if p in PERM_IDS]
    c = conn()
    c.execute(
        """INSERT INTO roles (user_id, role, perms, sections, updated_at)
           VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
             role=excluded.role, perms=excluded.perms,
             sections=excluded.sections, updated_at=CURRENT_TIMESTAMP""",
        (user_id, role, json.dumps(keep, ensure_ascii=False),
         json.dumps([str(s) for s in sections], ensure_ascii=False)))
    c.commit()


def set_blocked(user_id: int, blocked: bool) -> None:
    c = conn()
    c.execute(
        """INSERT INTO roles (user_id, blocked, updated_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
             blocked=excluded.blocked, updated_at=CURRENT_TIMESTAMP""",
        (user_id, 1 if blocked else 0))
    c.commit()


def is_blocked(user_id: int) -> bool:
    row = conn().execute(
        "SELECT blocked FROM roles WHERE user_id=?", (user_id,)).fetchone()
    return bool(row and row[0])


# ─────────────────────────── запись ───────────────────────────

def touch(user: dict, source: str = "app") -> None:
    """
    Отмечает, что человек появился: заводит строку или обновляет профиль.

    Профиль перезаписывается каждый раз, а не только при создании: имя и
    аватар в Telegram меняются, и список юзеров с прошлогодними никами
    бесполезен. NULLIF нужен, чтобы бот, знающий про человека только id,
    не затирал имя, полученное из мини-приложения.
    """
    uid = int(user.get("id") or 0)
    if not uid:
        return
    c = conn()
    c.execute(
        """INSERT INTO users (user_id, username, first_name, last_name,
                              photo_url, language, is_premium,
                              first_seen, last_seen, seen_bot, seen_app)
           VALUES (?, ?, ?, ?, ?, ?, ?,
                   CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
             username   = COALESCE(NULLIF(excluded.username, ''), users.username),
             first_name = COALESCE(NULLIF(excluded.first_name, ''), users.first_name),
             last_name  = COALESCE(NULLIF(excluded.last_name, ''), users.last_name),
             photo_url  = COALESCE(NULLIF(excluded.photo_url, ''), users.photo_url),
             language   = COALESCE(NULLIF(excluded.language, ''), users.language),
             is_premium = MAX(users.is_premium, excluded.is_premium),
             first_seen = COALESCE(users.first_seen, CURRENT_TIMESTAMP),
             last_seen  = CURRENT_TIMESTAMP,
             seen_bot   = MAX(COALESCE(users.seen_bot, 0), excluded.seen_bot),
             seen_app   = MAX(COALESCE(users.seen_app, 0), excluded.seen_app)""",
        (uid, user.get("username") or "", user.get("first_name") or "",
         user.get("last_name") or "", user.get("photo_url") or "",
         user.get("language_code") or "", 1 if user.get("is_premium") else 0,
         1 if source == "bot" else 0, 1 if source == "app" else 0))
    c.commit()


def note(user_id: int, kind: str, name: str = "") -> None:
    """Одно событие. kind: open | tab | screen | bot."""
    note_many(user_id, [(kind, name)])


def note_many(user_id: int, events) -> None:
    """
    Пачка событий одной вставкой.

    Приложение присылает переключения вкладок пачками, и раньше каждое
    событие писалось отдельным запросом со своей фиксацией. На сетевом
    диске это десяток отдельных записей там, где хватает одной.
    """
    uid = int(user_id or 0)
    rows = [(uid, str(k)[:16], str(n or "")[:64]) for k, n in events if k]
    if not uid or not rows:
        return
    c = conn()
    c.executemany("INSERT INTO events (user_id, kind, name) VALUES (?, ?, ?)", rows)
    opens = sum(1 for _, k, _ in rows if k == "open")
    if opens:
        c.execute("UPDATE users SET opens = COALESCE(opens, 0) + ? WHERE user_id=?",
                  (opens, uid))


def note_bot(user: dict, command: str, throttle: int = 0) -> None:
    """
    Человек воспользовался ботом: профиль и событие одним движением.

    throttle — сколько секунд не записывать такое же событие повторно.
    Нужен inline-режиму: Telegram шлёт запрос на каждое нажатие клавиши, и
    без окна одна набранная группа давала бы шесть событий, а график
    обращений показывал бы скорость печати, а не пользу.
    """
    uid = int(user.get("id") or 0)
    touch(user, source="bot")
    if throttle and uid:
        recent = conn().execute(
            """SELECT 1 FROM events WHERE user_id=? AND kind='bot' AND name=?
               AND ts >= datetime('now', ?) LIMIT 1""",
            (uid, command, "-" + str(int(throttle)) + " seconds")).fetchone()
        if recent:
            return
    note(uid, "bot", command)


# ─────────────────────────── чтение ───────────────────────────

def _days_back(n: int) -> list:
    """Список дат по московскому времени: n-1 дней назад … сегодня."""
    c = conn()
    return [c.execute("SELECT date('now', ?, ?)",
                      (MSK, "-" + str(i) + " days")).fetchone()[0]
            for i in range(n - 1, -1, -1)]


def _series(rows, days: int) -> list:
    """
    Достраивает ряд по дням до нужной длины: в базе есть только дни, когда
    что-то происходило, а пропуск дня на графике читался бы как сдвиг.
    """
    have = {d: n for d, n in rows}
    return [{"date": d, "count": have.get(d, 0)} for d in _days_back(days)]


def overview(days: int = 14) -> dict:
    c = conn()

    def one(sql, args=()):
        return c.execute(sql, args).fetchone()[0]

    total = one("SELECT COUNT(*) FROM users")
    today = one("SELECT COUNT(*) FROM users WHERE date(last_seen, ?) = date('now', ?)",
                (MSK, MSK))
    week = one("SELECT COUNT(*) FROM users WHERE last_seen >= datetime('now', '-7 days')")
    subs = one("SELECT COUNT(*) FROM users WHERE group_name IS NOT NULL AND group_name <> ''")
    in_app = one("SELECT COUNT(*) FROM users WHERE seen_app = 1")
    in_bot = one("SELECT COUNT(*) FROM users WHERE seen_bot = 1")
    premium = one("SELECT COUNT(*) FROM users WHERE is_premium = 1")
    blocked = one("SELECT COUNT(*) FROM roles WHERE blocked = 1")

    span = "-" + str(days) + " days"
    opens = c.execute(
        """SELECT date(ts, ?) d, COUNT(*) FROM events
           WHERE kind='open' AND ts >= datetime('now', ?) GROUP BY d""",
        (MSK, span)).fetchall()
    newcomers = c.execute(
        """SELECT date(first_seen, ?) d, COUNT(*) FROM users
           WHERE first_seen >= datetime('now', ?) GROUP BY d""",
        (MSK, span)).fetchall()
    commands = c.execute(
        """SELECT date(ts, ?) d, COUNT(*) FROM events
           WHERE kind='bot' AND ts >= datetime('now', ?) GROUP BY d""",
        (MSK, span)).fetchall()

    tabs = c.execute(
        """SELECT name, COUNT(*) n FROM events WHERE kind='tab'
           GROUP BY name ORDER BY n DESC""").fetchall()
    screens = c.execute(
        """SELECT name, COUNT(*) n FROM events WHERE kind='screen'
           GROUP BY name ORDER BY n DESC LIMIT 12""").fetchall()
    groups = c.execute(
        """SELECT group_name, COUNT(*) n FROM users
           WHERE group_name IS NOT NULL AND group_name <> ''
           GROUP BY group_name ORDER BY n DESC, group_name LIMIT 10""").fetchall()
    cmds = c.execute(
        """SELECT name, COUNT(*) n FROM events WHERE kind='bot'
           GROUP BY name ORDER BY n DESC LIMIT 10""").fetchall()

    tabs_total = sum(n for _, n in tabs) or 1
    return {
        "totals": {
            "users": total, "today": today, "week": week, "subs": subs,
            "app": in_app, "bot": in_bot, "premium": premium, "blocked": blocked,
        },
        "opens": _series(opens, days),
        "newcomers": _series(newcomers, days),
        "commands": _series(commands, days),
        "tabs": [{"name": n, "count": k, "share": round(k * 100 / tabs_total)}
                 for n, k in tabs],
        "screens": [{"name": n, "count": k} for n, k in screens],
        "groups": [{"name": n, "count": k} for n, k in groups],
        "bot_commands": [{"name": n, "count": k} for n, k in cmds],
    }


USER_FIELDS = ("user_id, username, first_name, last_name, photo_url, "
               "group_name, is_premium, opens, seen_app, seen_bot, "
               "first_seen, last_seen")


def _user_row(r) -> dict:
    return {
        "id": r[0], "username": r[1], "first_name": r[2], "last_name": r[3],
        "photo_url": r[4], "group": r[5], "premium": bool(r[6]),
        "opens": r[7] or 0, "in_app": bool(r[8]), "in_bot": bool(r[9]),
        "first_seen": r[10], "last_seen": r[11],
    }


def users_page(q: str = "", limit: int = 50, offset: int = 0) -> dict:
    c = conn()
    where, args = "", []
    if q:
        # Ищем сразу по всему, чем человек может быть назван: ник, имя,
        # группа, числовой id. Гадать, что именно ввели, не нужно — список
        # маленький, и лишнее совпадение дешевле пустого ответа.
        where = ("WHERE username LIKE ?1 OR first_name LIKE ?1 OR "
                 "last_name LIKE ?1 OR group_name LIKE ?1 OR "
                 "CAST(user_id AS TEXT) LIKE ?1")
        args = ["%" + q + "%"]
    total = c.execute("SELECT COUNT(*) FROM users " + where, args).fetchone()[0]
    rows = c.execute(
        "SELECT " + USER_FIELDS + " FROM users " + where +
        " ORDER BY last_seen DESC, user_id DESC LIMIT ? OFFSET ?",
        args + [max(1, min(limit, 200)), max(0, offset)]).fetchall()
    people = [_user_row(r) for r in rows]

    # Роли подтягиваем одним запросом, а не по строке на человека.
    ids = [p["id"] for p in people]
    if ids:
        marks = ",".join("?" * len(ids))
        held = {r[0]: (r[1], bool(r[2])) for r in c.execute(
            "SELECT user_id, role, blocked FROM roles WHERE user_id IN (" + marks + ")",
            ids)}
        for p in people:
            role, blocked = held.get(p["id"], ("none", False))
            p["role"], p["blocked"] = role, blocked
    return {"total": total, "users": people}


def user_card(user_id: int, days: int = 30) -> dict | None:
    c = conn()
    row = c.execute("SELECT " + USER_FIELDS + " FROM users WHERE user_id=?",
                    (user_id,)).fetchone()
    if not row:
        return None
    card = _user_row(row)

    counts = dict(c.execute(
        "SELECT kind, COUNT(*) FROM events WHERE user_id=? GROUP BY kind",
        (user_id,)).fetchall())
    activity = c.execute(
        """SELECT date(ts, ?) d, COUNT(*) FROM events
           WHERE user_id=? AND ts >= datetime('now', ?) GROUP BY d""",
        (MSK, user_id, "-" + str(days) + " days")).fetchall()
    have = {d: n for d, n in activity}

    card["counts"] = {
        "opens": card["opens"],
        "tabs": counts.get("tab", 0),
        "screens": counts.get("screen", 0),
        "commands": counts.get("bot", 0),
    }
    card["activity"] = [{"date": d, "count": have.get(d, 0)}
                        for d in _days_back(days)]
    card["feed"] = [{"kind": k, "name": n, "ts": t} for k, n, t in c.execute(
        """SELECT kind, name, ts FROM events WHERE user_id=?
           ORDER BY id DESC LIMIT 40""", (user_id,)).fetchall()]
    card["tabs"] = [{"name": n, "count": k} for n, k in c.execute(
        """SELECT name, COUNT(*) n FROM events
           WHERE user_id=? AND kind='tab' GROUP BY name ORDER BY n DESC""",
        (user_id,)).fetchall()]
    return card
