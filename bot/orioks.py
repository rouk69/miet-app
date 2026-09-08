# -*- coding: utf-8 -*-
"""
Клиент студенческого API ОРИОКС: что сдавать, когда и на сколько баллов.

Домашние задания в ОРИОКС живут не отдельной сущностью, а контрольными
мероприятиями дисциплины: у каждого есть название, тип («Домашнее
задание», «Контрольная работа», «Лабораторная»), учебная неделя сдачи и
баллы. Текста самого задания и вложенных файлов API не отдаёт — только
что сдавать и к какому сроку.

**Пароль здесь не хранится.** ОРИОКС выдаёт токен в обмен на логин и
пароль (Basic-авторизация), и дальше нужен только токен: он и лежит в
базе, привязанный к человеку. Пароль проходит через сервер один раз в
момент подключения и нигде не остаётся. Токен студент может отозвать
сам — и через приложение, и в любом другом клиенте ОРИОКС.

Документация API: https://orioks.gitlab.io/student-api/
"""
from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.request

from .db import conn

log = logging.getLogger("miet.orioks")

BASE = "https://orioks.miet.ru/api/v1"
TIMEOUT = 20

# Оба заголовка обязательны: без них ОРИОКС отвечает 400, не объясняя
# причины. User-Agent документация требует в виде «имя/версия ОС».
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "miet_mini_app/1.0 (Telegram Mini App)",
}

# Типы мероприятий, которые студент воспринимает как «задание, которое
# нужно сделать и сдать». Остальное (экзамен, зачёт) — это событие, а не
# работа, и в списке дел ему не место.
HOMEWORK_TYPES = ("домашн", "лаборатор", "реферат", "курсов", "расчёт",
                  "расчет", "практич", "контрольн", "коллоквиум", "тест",
                  "эссе", "доклад")


class OrioksError(Exception):
    """Ошибка, которую можно показать человеку."""


def _explain(e) -> str:
    """
    Переводит ответ ОРИОКС на человеческий.

    Разбирать тело важнее, чем код: у ОРИОКС они расходятся с его же
    документацией, и по одному коду сообщение получалось бы неверным —
    человек с опечаткой в пароле читал бы про лимит приложений.
    """
    text = ""
    try:
        body = json.loads(e.read().decode("utf-8", "replace"))
        err = body.get("error") if isinstance(body, dict) else None
        text = err if isinstance(err, str) else (err or {}).get("text", "")
    except Exception:                                   # noqa: BLE001
        pass

    low = (text or "").lower()
    if "логин" in low or "парол" in low:
        return "ОРИОКС не принял логин или пароль"
    if "токен" in low and ("восем" in low or "больше" in low):
        return ("В ОРИОКС уже восемь подключённых приложений — "
                "отзови лишние токены в самом ОРИОКС")
    if e.code == 401:
        return "ОРИОКС не принял логин или пароль"
    if e.code == 404:
        return "ОРИОКС не нашёл такой раздел"
    if text:
        return f"ОРИОКС: {text}"
    return f"ОРИОКС ответил {e.code}"


def _request(path: str, headers: dict, method: str = "GET") -> object:
    """
    Запрос к ОРИОКС. Прокси обходим явно: на машине автора системный
    прокси заворачивает такие адреса и отвечает 502.
    """
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(BASE + path, headers={**HEADERS, **headers},
                                 method=method)
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Код ответа у ОРИОКС не совпадает с документацией: на неверный
        # пароль приходит 403, хотя обещан 401, а 403 в документации
        # отведён под «больше восьми токенов». Поэтому решает текст в
        # теле ответа, а код — только запасной вариант.
        raise OrioksError(_explain(e))

    except urllib.error.URLError as e:
        # Отдельно от прочих ошибок: ОРИОКС рвёт TLS с внешних адресов,
        # и понять это по тексту исключения иначе невозможно.
        raise OrioksError(f"ОРИОКС недоступен ({type(e.reason).__name__})")
    except json.JSONDecodeError:
        raise OrioksError("ОРИОКС ответил не по-человечески")
    except Exception as e:                              # noqa: BLE001
        raise OrioksError(f"ОРИОКС недоступен ({type(e).__name__})")


def get_token(login: str, password: str) -> str:
    """Меняет логин и пароль на токен. Пароль после этого не нужен."""
    raw = f"{login}:{password}".encode("utf-8")
    auth = base64.b64encode(raw).decode("ascii")
    out = _request("/auth", {"Authorization": "Basic " + auth})
    token = out.get("token") if isinstance(out, dict) else None
    if not token:
        raise OrioksError("ОРИОКС не выдал токен")
    return str(token)


def _with_token(path: str, token: str, method: str = "GET") -> object:
    return _request(path, {"Authorization": "Bearer " + token}, method)


# Путь контрольных мероприятий в открытой документации не опубликован —
# описан только раздел. Вместо того чтобы гадать одним вариантом и
# получать пустой экран, перебираем известные формы и запоминаем ту, что
# ответила: следующий запрос идёт сразу по ней.
EVENT_PATHS = (
    "/student/disciplines/{id}/control_events",
    "/student/disciplines/{id}/control-events",
    "/student/disciplines/{id}/controlevents",
    "/student/disciplines/{id}/events",
    "/student/control_events/{id}",
)
_events_path = None


def student(token: str) -> dict:
    out = _with_token("/student", token)
    return out if isinstance(out, dict) else {}


def disciplines(token: str) -> list:
    out = _with_token("/student/disciplines", token)
    return out if isinstance(out, list) else []


def control_events(token: str, discipline_id: int) -> list:
    global _events_path
    tries = ([_events_path] if _events_path else []) + [
        p for p in EVENT_PATHS if p != _events_path]
    last = None
    for template in tries:
        try:
            out = _with_token(template.format(id=discipline_id), token)
        except OrioksError as e:
            last = e
            continue
        if _events_path != template:
            _events_path = template
            log.info("контрольные мероприятия отвечают по пути %s", template)
        return out if isinstance(out, list) else []
    if last:
        raise last
    return []


def revoke(token: str) -> bool:
    """
    Аннулирует токен на стороне ОРИОКС.

    Путь и метод — из документации: DELETE /student/tokens/<токен>.
    Сначала я предположил GET на выдуманный /revoke, и отзыв молча не
    работал бы: токен остался бы жить после «Отключить».
    """
    try:
        _with_token("/student/tokens/" + token, token, method="DELETE")
        return True
    except OrioksError as e:
        log.info("токен не аннулирован: %s", e)
        return False


# ─────────────────────────── хранение ───────────────────────────

def save_token(user_id: int, token: str) -> None:
    conn().execute(
        """INSERT INTO orioks_links (user_id, token, linked_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
             token=excluded.token, linked_at=CURRENT_TIMESTAMP""",
        (user_id, token))


def token_of(user_id: int) -> str:
    row = conn().execute("SELECT token FROM orioks_links WHERE user_id=?",
                         (user_id,)).fetchone()
    return row[0] if row else ""


def forget(user_id: int) -> None:
    conn().execute("DELETE FROM orioks_links WHERE user_id=?", (user_id,))


def linked_count() -> int:
    return conn().execute("SELECT COUNT(*) FROM orioks_links").fetchone()[0]


# ─────────────────────────── сборка ───────────────────────────

def is_homework(event_type: str) -> bool:
    low = (event_type or "").lower()
    return any(mark in low for mark in HOMEWORK_TYPES)


def tasks(token: str) -> dict:
    """
    Всё, что предстоит сдать: задания по всем дисциплинам семестра.

    Номер недели превращать в дату здесь не пытаемся: начало семестра
    знает клиент (оно считается из расписания), и дублировать этот
    расчёт значило бы получить два разных ответа на один вопрос.
    """
    subjects = disciplines(token)
    out, total, done = [], 0, 0
    for d in subjects:
        events = []
        for e in control_events(token, d.get("id")):
            grade = e.get("current_grade")
            got = grade is not None and grade >= 0
            events.append({
                "name": e.get("name") or e.get("type") or "Задание",
                "type": e.get("type") or "",
                "week": e.get("week"),
                "max_grade": e.get("max_grade"),
                "grade": grade if got else None,
                "done": got,
                "homework": is_homework(e.get("type")),
            })
            total += 1
            done += 1 if got else 0
        out.append({
            "id": d.get("id"),
            "name": d.get("name") or "Дисциплина",
            "teachers": d.get("teachers") or [],
            "control_form": d.get("control_form") or "",
            "current_grade": d.get("current_grade"),
            "max_grade": d.get("max_grade"),
            "exam_date": d.get("exam_date"),
            "events": events,
        })
    return {"disciplines": out, "total": total, "done": done}


def _raw_code(path: str, headers: dict, method: str = "GET"):
    """Код ответа как есть — для разведки, без перевода на человеческий."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(BASE + path, headers=headers, method=method)
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status, r.read()[:200].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200].decode("utf-8", "replace")
    except Exception as e:                              # noqa: BLE001
        return 0, type(e).__name__


def probe() -> dict:
    """
    Разведка: как именно ОРИОКС отвечает нашему серверу.

    Проверяем несколько форм одного запроса. Заведомо неверный пароль
    здесь безопасен и нужен по делу: если на него приходит 401, значит
    запрос разобран правильно и формат верен, а 400 означает, что
    ОРИОКС не понял сам запрос. Отличить одно от другого иначе нельзя —
    настоящего пароля у разработчика нет и быть не должно.
    """
    wrong = base64.b64encode(b"00000000:definitely-wrong").decode("ascii")
    checks = {
        "без заголовков вовсе": ("/auth", {}),
        "только Authorization": ("/auth", {"Authorization": "Basic " + wrong}),
        "полный набор": ("/auth", {**HEADERS, "Authorization": "Basic " + wrong}),
        "корень API": ("", HEADERS),
    }
    out = {}
    for name, (path, headers) in checks.items():
        code, body = _raw_code(path, headers)
        out[name] = {"code": code, "body": body[:120]}
    return {
        "reachable": any(v["code"] for v in out.values()),
        "checks": out,
        "events_path": _events_path or "ещё не выяснен",
    }
