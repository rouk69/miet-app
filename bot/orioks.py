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
    # Первым — тот, что реально отвечает: проверено на живом аккаунте.
    # Остальные оставлены на случай, если ОРИОКС поменяет адрес: без них
    # переезд означал бы пустой экран без объяснения. Порядок важен —
    # каждый лишний кандидат это 404 на каждую дисциплину, а их восемь.
    "/student/disciplines/{id}/events",
    "/student/disciplines/{id}/control_events",
    "/student/disciplines/{id}/control-events",
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

# Не работа, а формальность: посещаемость, активность, «порядок НБС»,
# семестровый план. В ОРИОКС они лежат вперемешку с заданиями, но сдавать
# там нечего — в списке дел им не место, иначе он превращается в шум.
# У живого студента таких записей оказалось больше трети из семидесяти
# пяти, и именно они делали экран нечитаемым.
NOT_A_TASK = ("посещаем", "активность", "порядок", "семестровый план",
              "план работы", "рейтинг", "итог", "общие ресурсы", "лекция")

# Экзамен и зачёт — не работа, которую сдают в течение семестра, а то,
# чем он заканчивается. В списке дел рядом с лабораторной они сбивают:
# «сдать» экзамен нельзя заранее. Показываем их отдельно.
SESSION_TYPES = ("экзамен", "зачёт", "зачет")


def is_homework(event_type: str) -> bool:
    low = (event_type or "").lower()
    return any(mark in low for mark in HOMEWORK_TYPES)


def is_session(event: dict) -> bool:
    """Экзамен или зачёт — конец семестра, а не текущее дело."""
    return any(m in (event.get("type") or "").lower() for m in SESSION_TYPES)


def is_task(event: dict) -> bool:
    """
    Настоящее ли это задание.

    Два признака: за него дают баллы и это не отметка о посещении.
    Мероприятие на ноль баллов сдавать бессмысленно — это запись для
    порядка, а не работа.
    """
    if not (event.get("max_grade") or 0) > 0:
        return False
    if is_session(event):
        return False
    text = f"{event.get('type') or ''} {event.get('name') or ''}".lower()
    return not any(mark in text for mark in NOT_A_TASK)


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
            task = is_task(e)
            events.append({
                "name": e.get("name") or e.get("type") or "Задание",
                "type": e.get("type") or "",
                "week": e.get("week"),
                "max_grade": e.get("max_grade"),
                "grade": grade if got else None,
                "done": got,
                "homework": is_homework(e.get("type")),
                # Формальности приходят вместе с заданиями, но считать и
                # показывать их наравне нельзя.
                "task": task,
                "session": is_session(e),
            })
            if task:
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


def raw_dump(token: str) -> dict:
    """
    Сырой ответ ОРИОКС как есть — для разбора, когда экран показывает
    ерунду. Отдаётся только своему владельцу токена и только про него:
    это его же данные, но в том виде, в каком их прислал ОРИОКС.
    """
    out = {"paths_tried": [], "disciplines": None, "events": None}
    try:
        out["disciplines"] = _with_token("/student/disciplines", token)
    except OrioksError as e:
        out["disciplines_error"] = str(e)
        return out

    first = None
    if isinstance(out["disciplines"], list) and out["disciplines"]:
        first = out["disciplines"][0]
        if isinstance(first, dict):
            first = first.get("id")
    if first is None:
        return out

    # Показываем ответ КАЖДОГО кандидата пути: так видно, какой из них
    # отдаёт мероприятия, а какой — что-то постороннее, принятое за них.
    for template in EVENT_PATHS:
        path = template.format(id=first)
        try:
            got = _with_token(path, token)
            # Полный первый элемент, а не обрезок: обрезанный ответ уже
            # один раз скрыл от меня половину полей.
            first_item = got[0] if isinstance(got, list) and got else got
            out["paths_tried"].append({
                "path": path, "ok": True,
                "count": len(got) if isinstance(got, list) else None,
                "keys": sorted(first_item.keys())
                        if isinstance(first_item, dict) else None,
                "first": first_item,
            })
        except OrioksError as e:
            out["paths_tried"].append({"path": path, "ok": False,
                                       "error": str(e)})
    # Что ещё ОРИОКС знает о дисциплине: вдруг описание заданий лежит
    # в соседнем разделе, а не в самих мероприятиях.
    for extra in ("/student/disciplines/{id}",
                  "/student/disciplines/{id}/resources",
                  "/student/disciplines/{id}/materials",
                  "/student/disciplines/{id}/info",
                  "/student/disciplines/{id}/events/{ev}"):
        path = extra.format(id=first, ev=1)
        try:
            got = _with_token(path, token)
            out.setdefault("extras", []).append(
                {"path": path, "ok": True, "sample": str(got)[:500]})
        except OrioksError as e:
            out.setdefault("extras", []).append(
                {"path": path, "ok": False, "error": str(e)})
    return out


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
