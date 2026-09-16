# -*- coding: utf-8 -*-
"""
Розыгрыш: кто привёл больше людей, тот и выше в таблице.

Награды выдаёт владелец руками — призовых кошельков, выплат и Stars
внутри бота нет и не заводится. Отсюда и устройство: задача модуля не
«наградить», а честно посчитать и показать, кого награждать.

**Что считается приглашением.** Не переход по ссылке: открыть и уйти
может кто угодно, и такая цифра меряет рассылку спама, а не пользу.
Приглашение засчитывается, когда пришедший дошёл до ВЫБОРА ГРУППЫ —
то есть начал пользоваться расписанием. До этого он висит в «ждут
группу»: приглашающий видит, что человек пришёл, но очко ещё не дали.

**Человек закрепляется навсегда** за тем, по чьей ссылке пришёл первым.
Перетянуть его второй ссылкой нельзя, иначе двое приглашающих
перекидывали бы одного и того же друг у друга, а счёт зависел бы от
того, кто отправил последним.

**Накрутка.** Полностью её здесь не отловить: у входа стоит Telegram, и
всё, что мы знаем о пришедшем, — это его профиль. Поэтому два уровня.
Совсем пустой аккаунт (без ника, без фото, без премиума) в зачёт не
идёт вовсе — так выглядит свежесозданная кукла. Остальное подозрительное
(аккаунт заведён только что, пачка переходов за минуту) очко не отменяет,
а вешает на приглашение метку: владелец видит её в админке и снимает
приглашение сам. Автомат, отбирающий призы молча, ошибётся на живом
студенте без аватарки, и доказать он ничего не сможет.

Раздел не виден никому, пока владелец не откроет его флагом
`raffle_on`: счёт при этом идёт с самого начала, чтобы к открытию
таблица была не пустой, а сам розыгрыш можно было пройти целиком
самому.
"""
from __future__ import annotations

import json
import logging
import os
import random
import re

from .db import MSK, conn

log = logging.getLogger("miet.raffle")


class Refused(Exception):
    """Отказ, который можно показать человеку как есть."""


# ─────────────────────────── ссылка ───────────────────────────

# Шесть знаков из непутающегося алфавита: без «0» и «o», без «1» и «l» —
# код читают вслух и набирают руками, когда ссылка пришла картинкой.
ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
CODE_LEN = 6

# Префикс в start-параметре. Нужен потому, что там же ездит закодированное
# название группы (`t.me/бот?start=<base64>`), и разбирать их надо
# по-разному. Подчёркивание Telegram в этом параметре пропускает.
PREFIX = "r_"

CODE_RE = re.compile(r"^[a-z2-9]{4,12}$")


def parse_code(payload: str) -> str:
    """Код из start-параметра или пустая строка, если это не наш случай."""
    raw = str(payload or "").strip()
    if not raw.startswith(PREFIX):
        return ""
    code = raw[len(PREFIX):].lower()
    return code if CODE_RE.match(code) else ""


def _new_code() -> str:
    return "".join(random.choice(ALPHABET) for _ in range(CODE_LEN))


def code_of(user_id: int) -> str:
    """
    Код этого человека, заводя его при первом спросе.

    Уникальность стережёт индекс в базе, а не проверка перед вставкой:
    два одновременных открытия раздела разошлись бы ровно между ними.
    Поэтому на столкновение просто пробуем ещё раз.
    """
    uid = int(user_id or 0)
    if not uid:
        return ""
    c = conn()
    row = c.execute("SELECT ref_code FROM users WHERE user_id=?", (uid,)).fetchone()
    if row and row[0]:
        return row[0]
    for _ in range(8):
        code = _new_code()
        try:
            cur = c.execute(
                "UPDATE users SET ref_code=? WHERE user_id=? AND ref_code IS NULL",
                (code, uid))
            if cur.rowcount:
                return code
            # Строки нет вовсе — человек ещё не записан. Заводим вместе с кодом.
            c.execute(
                "INSERT OR IGNORE INTO users (user_id, ref_code) VALUES (?, ?)",
                (uid, code))
            row = c.execute("SELECT ref_code FROM users WHERE user_id=?",
                            (uid,)).fetchone()
            if row and row[0]:
                return row[0]
        except Exception:                                   # noqa: BLE001
            log.info("код %s занят, беру другой", code)
    log.error("не удалось выдать код приглашения для %s", uid)
    return ""


def owner_of(code: str) -> int:
    """Чей это код. Ноль — ничей."""
    code = str(code or "").strip().lower()
    if not CODE_RE.match(code):
        return 0
    row = conn().execute("SELECT user_id FROM users WHERE ref_code=?",
                         (code,)).fetchone()
    return int(row[0]) if row else 0


# Имя бота в ссылке. Сам модуль его не знает: узнаёт его только живой
# процесс у Telegram при старте, а HTTP-API импортировать main не может —
# замкнулся бы круг. Поэтому бот кладёт имя сюда, как складывает свою
# send_message в notify.
_bot = {"username": ""}


def set_bot_username(name: str) -> None:
    _bot["username"] = str(name or "").lstrip("@")


def bot_username() -> str:
    return _bot["username"] or os.environ.get("BOT_USERNAME", "").lstrip("@")


def link_for(user_id: int, bot_username_: str = "") -> str:
    code = code_of(user_id)
    name = str(bot_username_ or bot_username()).lstrip("@")
    if not code or not name:
        return ""
    return f"https://t.me/{name}?start={PREFIX}{code}"


# ─────────────────────────── проверка пришедшего ───────────────────────────

# Аккаунты Telegram нумеруются по возрастанию, поэтому по id видно, что он
# заведён недавно. Порог не отсекает, только помечает: первокурсник,
# заведший Telegram к сентябрю, выглядит точно так же, как кукла.
FRESH_ID = 8_000_000_000

# Сколько переходов за час у одного приглашающего считать пачкой. Живая
# рассылка в чат группы даёт заметный всплеск, поэтому граница высокая:
# метка должна означать «посмотри руками», а не «тут людно».
BURST_PER_HOUR = 12


def judge(profile: dict, inviter_id: int = 0) -> tuple:
    """
    Что мы думаем о пришедшем: (пускать ли в зачёт, причина, метки).

    Профиль — то, что о человеке известно Telegram: ник, фото, премиум.
    Ничего больше у нас и нет: ни почты, ни телефона, ни истории.
    """
    uid = int(profile.get("id") or 0)
    has_name = bool(str(profile.get("username") or "").strip())
    has_photo = bool(profile.get("photo"))
    premium = bool(profile.get("premium"))

    flags = []
    if not has_name:
        flags.append("noname")
    if uid and uid >= FRESH_ID:
        flags.append("fresh")
    if inviter_id:
        burst = conn().execute(
            """SELECT COUNT(*) FROM raffle_invites WHERE inviter_id=?
               AND created_at >= datetime('now', '-1 hour')""",
            (inviter_id,)).fetchone()[0]
        if burst >= BURST_PER_HOUR:
            flags.append("burst")

    # Ни ника, ни аватарки, ни премиума — так не выглядит ни один живой
    # студент, зато ровно так выглядит аккаунт, заведённый ради очка.
    if not has_name and not has_photo and not premium:
        return False, "Пустой аккаунт: ни ника, ни фото", flags
    return True, "", flags


# Сколько секунд после первого появления человек ещё считается новым.
# Ссылка должна приводить НОВЫХ: тот, кто уже месяц пользуется
# приложением, очка приглашающему не приносит, даже если перешёл по ней.
# Четверть часа, а не секунда: профиль заводится в самом начале /start,
# и к моменту разбора ссылки человек уже записан.
NEW_WINDOW = 15 * 60


def is_new(user_id: int) -> bool:
    row = conn().execute(
        """SELECT first_seen IS NULL OR first_seen >= datetime('now', ?)
             FROM users WHERE user_id=?""",
        (f"-{NEW_WINDOW} seconds", int(user_id))).fetchone()
    return True if not row else bool(row[0])


def attach(profile: dict, code: str, source: str = "bot") -> dict:
    """
    Закрепить пришедшего за владельцем кода.

    Возвращает {ok, state, reason} и ничего не поднимает наружу: зовётся
    это из обработчика /start, где сбой учёта не должен помешать человеку
    получить расписание.
    """
    uid = int(profile.get("id") or 0)
    inviter = owner_of(code)
    if not uid or not inviter:
        return {"ok": False, "reason": "Ссылка не распознана"}
    if inviter == uid:
        return {"ok": False, "reason": "Это твоя же ссылка"}

    have = conn().execute(
        "SELECT inviter_id, state FROM raffle_invites WHERE user_id=?",
        (uid,)).fetchone()
    if have:
        # Закрепление навсегда, и молча: человек не виноват, что ему
        # прислали вторую ссылку, и знать ему об этом незачем.
        return {"ok": False, "reason": "Уже закреплён", "state": have[1]}
    if not is_new(uid):
        _remember(uid, inviter, source, "rejected",
                  "Уже пользовался приложением", [])
        return {"ok": False, "reason": "Уже пользовался приложением"}

    good, why, flags = judge(profile, inviter)
    state = "waiting" if good else "rejected"
    _remember(uid, inviter, source, state, why, flags)
    return {"ok": good, "state": state, "reason": why, "inviter": inviter}


def _remember(uid: int, inviter: int, source: str, state: str,
              reason: str, flags: list) -> None:
    conn().execute(
        """INSERT OR IGNORE INTO raffle_invites
               (user_id, inviter_id, source, state, reason, flags)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (uid, inviter, str(source or "bot")[:16], state, reason or None,
         ",".join(flags)))


def settle(user_id: int) -> bool:
    """
    Человек выбрал группу — зачесть приглашение, если оно ждало.

    Зовётся из storage.set_group, то есть на каждый выбор группы. Смены
    группы потом ничего не меняют: переход засчитывается один раз, на
    первой.
    """
    uid = int(user_id or 0)
    if not uid:
        return False
    cur = conn().execute(
        """UPDATE raffle_invites
              SET state='counted', counted_at=CURRENT_TIMESTAMP
            WHERE user_id=? AND state='waiting'""", (uid,))
    return bool(cur.rowcount)


def decide(user_id: int, verdict: str) -> dict:
    """
    Ручное решение владельца по спорному приглашению.

    'no' снимает очко, 'ok' возвращает его и стирает причину: спорное
    приглашение разбирает человек, а не автомат.
    """
    uid = int(user_id or 0)
    if verdict not in ("ok", "no"):
        raise Refused("Неизвестное решение")
    row = conn().execute(
        "SELECT state FROM raffle_invites WHERE user_id=?", (uid,)).fetchone()
    if not row:
        raise Refused("Такого приглашения нет")
    if verdict == "no":
        conn().execute(
            """UPDATE raffle_invites SET state='rejected', manual='no',
                      reason='Снято вручную' WHERE user_id=?""", (uid,))
        return {"state": "rejected"}
    # Возвращённое приглашение встаёт в то состояние, в котором было бы
    # без вмешательства: очко даётся только тем, кто выбрал группу.
    has_group = conn().execute(
        """SELECT group_name IS NOT NULL AND group_name<>''
             FROM users WHERE user_id=?""", (uid,)).fetchone()
    state = "counted" if has_group and has_group[0] else "waiting"
    conn().execute(
        """UPDATE raffle_invites
              SET state=?, manual='ok', reason=NULL,
                  counted_at=CASE WHEN ?='counted'
                                  THEN COALESCE(counted_at, CURRENT_TIMESTAMP)
                                  ELSE counted_at END
            WHERE user_id=?""", (state, state, uid))
    return {"state": state}


# ─────────────────────────── условия розыгрыша ───────────────────────────

# Условия лежат в базе, а не в переменных окружения и не в коде: розыгрыш
# заводят и перезаводят по обстановке, а правка переменной в панели Amvera
# означает перезапуск контейнера и две минуты молчания бота.
CONF_KEY = "raffle:conf"

DEFAULT_CONF = {
    "title": "Розыгрыш",
    "note": "Приглашай друзей — кто привёл больше, тот и выше",
    "prizes": [],
    # Дата окончания в виде ГГГГ-ММ-ДД или пусто. Пусто — значит срока
    # нет: «осталось N дней» тогда не показывается вовсе, а не считается
    # от балды.
    "ends": "",
    "rules_note": ("Накрутка запрещена: подозрительные аккаунты помечаются "
                   "автоматически, спорные приглашения снимаются вручную"),
}


def conf() -> dict:
    """Условия розыгрыша. Неизвестные ключи из базы отбрасываются."""
    row = conn().execute("SELECT value FROM index_meta WHERE key=?",
                         (CONF_KEY,)).fetchone()
    out = dict(DEFAULT_CONF)
    if row and row[0]:
        try:
            saved = json.loads(row[0])
        except (TypeError, ValueError):
            log.warning("условия розыгрыша в базе не разобрались")
            saved = {}
        if isinstance(saved, dict):
            for key in DEFAULT_CONF:
                if key in saved:
                    out[key] = saved[key]
    out["prizes"] = _clean_prizes(out.get("prizes"))
    return out


MAX_PRIZES = 10
MAX_TEXT = 200


def _clean_prizes(raw) -> list:
    """Призы: место и что за него дают. Место считается по порядку."""
    out = []
    for i, item in enumerate(raw if isinstance(raw, list) else []):
        if len(out) >= MAX_PRIZES:
            break
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()[:MAX_TEXT]
            emoji = str(item.get("emoji") or "").strip()[:8]
        else:
            text, emoji = str(item or "").strip()[:MAX_TEXT], ""
        if text:
            out.append({"place": i + 1, "text": text, "emoji": emoji})
    return out


def set_conf(patch: dict) -> dict:
    """Правит условия по кускам: экран настроек шлёт только изменённое."""
    now = conf()
    for key in DEFAULT_CONF:
        if key not in (patch or {}):
            continue
        value = patch[key]
        if key == "prizes":
            now[key] = _clean_prizes(value)
        elif key == "ends":
            now[key] = _clean_date(value)
        else:
            now[key] = str(value or "").strip()[:MAX_TEXT]
    conn().execute(
        """INSERT INTO index_meta (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (CONF_KEY, json.dumps(now, ensure_ascii=False)))
    return now


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _clean_date(value) -> str:
    """Дата окончания. Кривую отбрасываем в пусто, а не подставляем свою."""
    raw = str(value or "").strip()[:10]
    if not raw:
        return ""
    if not DATE_RE.match(raw):
        raise Refused("Дата нужна в виде 2026-10-01")
    return raw


def days_left(ends: str = "") -> int | None:
    """
    Сколько дней осталось. None — срок не задан, и показывать нечего.

    Считает база, а не Python: время в базе UTC, а сутки в приложении
    московские, и «осталось 0 дней» не должно наступать в три часа ночи.
    """
    ends = ends if ends is not None else conf()["ends"]
    if not ends:
        return None
    row = conn().execute(
        "SELECT CAST(julianday(?) - julianday(date('now', ?)) AS INTEGER)",
        (ends, MSK)).fetchone()
    return max(0, int(row[0])) if row and row[0] is not None else None


# ─────────────────────────── счёт ───────────────────────────

def _display_name(first: str, username: str, uid: int = 0) -> str:
    """
    Как звать человека в таблице.

    Имя из Telegram бывает собрано из невидимых символов: у одного
    участника оно состояло из вариационных селекторов, и строка в таблице
    выходила пустой. Поэтому чистим и откатываемся на ник, а в совсем
    безнадёжном случае — на номер места в списке людей.
    """
    name = re.sub(r"[​-‏⁠-⁯︀-️­]", "",
                  str(first or "")).strip()
    if name:
        return name[:32]
    if username:
        return str(username)[:32]
    return f"Участник {uid}" if uid else "Участник"


def counts_of(user_id: int) -> dict:
    """Сколько этот человек привёл: зачтено, ждут группу, отклонено."""
    rows = conn().execute(
        "SELECT state, COUNT(*) FROM raffle_invites WHERE inviter_id=? "
        "GROUP BY state", (int(user_id or 0),)).fetchall()
    by = dict(rows)
    return {"counted": by.get("counted", 0), "waiting": by.get("waiting", 0),
            "rejected": by.get("rejected", 0)}


def place_of(user_id: int) -> int:
    """
    Место в таблице. Ноль — приглашений нет вовсе, места тоже.

    Равный счёт делит место: двое с пятью приглашёнными оба вторые, и
    следующий за ними четвёртый. Иначе порядок решала бы сортировка, то
    есть случай.
    """
    mine = counts_of(user_id)["counted"]
    if not mine:
        return 0
    row = conn().execute(
        """SELECT COUNT(*) FROM (
               SELECT inviter_id FROM raffle_invites WHERE state='counted'
               GROUP BY inviter_id HAVING COUNT(*) > ?)""", (mine,)).fetchone()
    return int(row[0]) + 1


# Сколько дней показывать в полоске «приходят по твоей ссылке». Неделя:
# столбик на день читается, а месяц превращается в частокол.
WEEK_DAYS = 7


def week_of(user_id: int) -> list:
    """Переходы по дням за неделю — для полоски на экране."""
    rows = dict(conn().execute(
        f"""SELECT date(created_at, '{MSK}') AS d, COUNT(*)
              FROM raffle_invites
             WHERE inviter_id=? AND created_at >= datetime('now', '-6 days')
             GROUP BY d""", (int(user_id or 0),)).fetchall())
    days = conn().execute(
        f"""WITH RECURSIVE d(n) AS (SELECT 0 UNION ALL
                                    SELECT n+1 FROM d WHERE n < {WEEK_DAYS - 1})
            SELECT date('now', '{MSK}', '-' || (6 - n) || ' days') FROM d""",
    ).fetchall()
    return [{"date": day[0], "count": rows.get(day[0], 0)} for day in days]


def _rows_for_board(limit: int) -> list:
    return conn().execute(
        """SELECT r.inviter_id, COUNT(*) AS n,
                  u.first_name, u.username, u.photo_url,
                  SUM(CASE WHEN r.flags <> '' AND r.manual IS NULL
                           THEN 1 ELSE 0 END) AS marked
             FROM raffle_invites r
             LEFT JOIN users u ON u.user_id = r.inviter_id
            WHERE r.state='counted'
            GROUP BY r.inviter_id
            ORDER BY n DESC, MIN(r.counted_at) ASC
            LIMIT ?""", (max(1, min(int(limit or 20), 100)),)).fetchall()


def board(viewer_id: int = 0, limit: int = 20, with_marks: bool = False) -> dict:
    """
    Таблица: кто сколько привёл.

    Ник участника показывается всем — таблица публичная, и попадают в неё
    по собственной воле. А вот метки подозрительности видит только тот,
    кто разбирает спорные приглашения: для остальных это обвинение без
    разбирательства, вывешенное рядом с именем.

    При равном счёте выше тот, кто набрал его раньше: иначе порядок
    менялся бы сам собой при каждом обновлении.
    """
    out = []
    for i, r in enumerate(_rows_for_board(limit)):
        item = {
            "place": i + 1,
            "user_id": int(r[0]),
            "count": int(r[1]),
            "name": _display_name(r[2], r[3], int(r[0])),
            "username": r[3] or "",
            "photo": r[4] or "",
            "me": int(r[0]) == int(viewer_id or 0),
        }
        if with_marks:
            item["marked"] = int(r[5] or 0)
        out.append(item)
    # Место по счёту, а не по позиции в срезе: у равных оно общее.
    for item in out:
        item["place"] = 1 + sum(1 for x in out if x["count"] > item["count"])
    mine = counts_of(viewer_id) if viewer_id else {}
    return {
        "top": out,
        "me": {
            "user_id": int(viewer_id or 0),
            "count": mine.get("counted", 0),
            "waiting": mine.get("waiting", 0),
            "place": place_of(viewer_id) if viewer_id else 0,
            # Есть ли я в показанном куске: если нет, экран дорисует
            # отдельную строку снизу, чтобы своё место было видно всегда.
            "in_top": any(x["me"] for x in out),
        } if viewer_id else {},
        "players": conn().execute(
            "SELECT COUNT(DISTINCT inviter_id) FROM raffle_invites "
            "WHERE state='counted'").fetchone()[0],
    }


def state_for(user_id: int, bot_username_: str = "",
              can_moderate: bool = False) -> dict:
    """Всё, что нужно экрану розыгрыша одному человеку, одним ответом."""
    c = conf()
    counts = counts_of(user_id)
    return {
        "title": c["title"],
        "note": c["note"],
        "prizes": c["prizes"],
        "ends": c["ends"],
        "days_left": days_left(c["ends"]),
        "code": code_of(user_id),
        "link": link_for(user_id, bot_username_),
        "counted": counts["counted"],
        "waiting": counts["waiting"],
        "rejected": counts["rejected"] if can_moderate else 0,
        "place": place_of(user_id),
        "week": week_of(user_id),
        "rules_note": c["rules_note"],
    }


# ─────────────────────────── для админки ───────────────────────────

def invites_of(inviter_id: int, limit: int = 100) -> list:
    """Кого привёл этот человек — с метками и причинами отказа."""
    rows = conn().execute(
        """SELECT r.user_id, r.state, r.reason, r.flags, r.manual,
                  r.created_at, r.counted_at, r.source,
                  u.first_name, u.username, u.group_name
             FROM raffle_invites r
             LEFT JOIN users u ON u.user_id = r.user_id
            WHERE r.inviter_id=?
            ORDER BY r.created_at DESC, r.user_id DESC LIMIT ?""",
        (int(inviter_id or 0), max(1, min(int(limit or 100), 500)))).fetchall()
    return [{
        "user_id": int(r[0]), "state": r[1], "reason": r[2] or "",
        "flags": [f for f in (r[3] or "").split(",") if f],
        "manual": r[4] or "", "created_at": r[5], "counted_at": r[6],
        "source": r[7], "name": _display_name(r[8], r[9], int(r[0])),
        "username": r[9] or "", "group": r[10] or "",
    } for r in rows]


def overview(limit: int = 50) -> dict:
    """
    Сводка для владельца: кого награждать и что стоит посмотреть руками.

    Метки здесь отдаются всегда — это и есть экран, ради которого они
    заводились.
    """
    c = conf()
    totals = dict(conn().execute(
        "SELECT state, COUNT(*) FROM raffle_invites GROUP BY state").fetchall())
    suspicious = [{
        "user_id": int(r[0]), "inviter_id": int(r[1]),
        "flags": [f for f in (r[2] or "").split(",") if f],
        "state": r[3], "created_at": r[4],
        "name": _display_name(r[5], r[6], int(r[0])),
        "username": r[6] or "",
        "inviter_name": _display_name(r[7], r[8], int(r[1])),
    } for r in conn().execute(
        """SELECT r.user_id, r.inviter_id, r.flags, r.state, r.created_at,
                  u.first_name, u.username, i.first_name, i.username
             FROM raffle_invites r
             LEFT JOIN users u ON u.user_id = r.user_id
             LEFT JOIN users i ON i.user_id = r.inviter_id
            WHERE r.flags <> '' AND r.manual IS NULL AND r.state <> 'rejected'
            ORDER BY r.created_at DESC, r.user_id DESC LIMIT 100""").fetchall()]
    return {
        "conf": c,
        "days_left": days_left(c["ends"]),
        "board": board(0, limit, with_marks=True)["top"],
        "totals": {
            "counted": totals.get("counted", 0),
            "waiting": totals.get("waiting", 0),
            "rejected": totals.get("rejected", 0),
            "players": conn().execute(
                "SELECT COUNT(DISTINCT inviter_id) FROM raffle_invites"
            ).fetchone()[0],
        },
        "suspicious": suspicious,
    }


def winners(places: int = 0) -> list:
    """
    Кого награждать: столько верхних строк, сколько призовых мест.

    Ноль призов означает «покажи весь верх» — розыгрыш могли ещё не
    описать, а посмотреть, кто ведёт, уже хочется.
    """
    if not places:
        places = len(conf()["prizes"]) or 3
    top = board(0, max(places * 2, 10), with_marks=True)["top"]
    return [x for x in top if x["place"] <= places]
