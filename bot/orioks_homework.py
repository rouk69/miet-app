# -*- coding: utf-8 -*-
"""
Сдача работ в ОРИОКС из приложения. ФУНДАМЕНТ, открыт только владельцу.

«Домашние задания» в ОРИОКС — это не выдача условий, а обращения
студента к преподавателю: студент нажимает «Добавить», выбирает
дисциплину и контрольное мероприятие, пишет описание и прикладывает
файлы; дальше идёт переписка со статусами «Ожидает», «В работе»,
«Требуется уточнение», «Завершено». Значит сдача работы и переписка с
преподавателем — одно и то же, и строить надо одно.

Что известно по разведке живого кабинета (24.09.2026, только чтение):

- список — `/student/homework/list`, таблица «Статус, Название,
  Дисциплина, Контрольное мероприятие, Студент, Группа, Время создания,
  Новых»;
- форма — `/student/homework/create`, отправка POST на
  `/student/homework/create?id_type=2`, поля `HomeworkTreadForm[...]`:
  `title`, `variant` (до пяти символов), `dis_id`, `id_km`, `type`,
  `message` (обязательно), `attachments`;
- мероприятия по дисциплинам лежат в самой странице, JSON в атрибуте
  `data-kms` у списка `id_km` — отдельного запроса нет;
- файлы грузятся виджетом кусками по 16 МБ на `/storage/upload`, в
  форму уходит только то, что вернула загрузка. Протокол виджета живёт в
  его скрипте и ещё не разобран — поэтому отправка пока только текстом.

Чего ещё НЕ проверено вживую: сама отправка (она уходит преподавателю
по-настоящему, пробовать её ради разведки нельзя) и страница переписки
(у владельца пока нет ни одного обращения — смотреть не на что).
"""
from __future__ import annotations

import html as _html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from . import orioks_web
from .orioks_web import BASE, TIMEOUT, UA, SessionExpired, WebError

LIST_PATH = "/student/homework/list"
CREATE_PATH = "/student/homework/create"
SUBMIT_PATH = "/student/homework/create?id_type=2"
FORM = "HomeworkTreadForm"

# Типы работ — как в самом ОРИОКС (список `type` в форме).
TYPES = {1: "Домашняя работа", 2: "Отчёт по лабораторной работе",
         3: "Расчёт", 4: "Другое"}

# Пределы — наши, чтобы не отправить полотно по ошибке; у ОРИОКС вариант
# ограничен пятью символами прямо в подсказке поля.
TITLE_MAX, VARIANT_MAX, MESSAGE_MAX = 200, 5, 5000


def _expired(page: str) -> bool:
    return orioks_web.FIELD_PASSWORD in page


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", _html.unescape(text)).strip()


# ─────────────────────────── форма ───────────────────────────

def parse_form(page: str) -> dict:
    """
    Что можно выбрать в форме: дисциплины, их мероприятия, типы работ.

    Мероприятия приходят JSON-ом в `data-kms` — словарь «id дисциплины →
    id мероприятия → {name: "2 неделя: ЛР.1 ЛР.1"}».
    """
    names = {}
    sel = re.search(r'(?is)<select[^>]*name="' + re.escape(FORM)
                    + r'\[dis_id\]"[^>]*>(.*?)</select>', page)
    for value, text in re.findall(
            r'(?is)<option[^>]*value="(\d+)"[^>]*>(.*?)</option>',
            sel.group(1) if sel else ""):
        names[value] = _clean(text)

    kms = {}
    m = re.search(r"data-kms='([^']*)'", page) or \
        re.search(r'data-kms="([^"]*)"', page)
    if m:
        try:
            kms = json.loads(_html.unescape(m.group(1)))
        except ValueError:
            kms = {}

    disciplines = []
    for did, name in names.items():
        events = [{"id": int(k), "name": _clean((v or {}).get("name", ""))}
                  for k, v in (kms.get(did) or {}).items() if str(k).isdigit()]
        disciplines.append({"id": int(did), "name": name, "events": events})
    return {"disciplines": disciplines,
            "types": [{"id": k, "name": v} for k, v in TYPES.items()],
            "uploads": False}


def form(cookie: str) -> dict:
    page = orioks_web.get_page(cookie, CREATE_PATH)
    if _expired(page):
        raise SessionExpired("Сессия ОРИОКС кончилась")
    return parse_form(page)


# ─────────────────────────── список ───────────────────────────

def parse_list(page: str) -> list:
    """
    Обращения из таблицы списка. Столбцы по заголовку, а не по номеру:
    ОРИОКС уже показывал, что меняет вёрстку без предупреждения.
    """
    table = re.search(r"(?is)<table[^>]*>(.*?)</table>", page)
    if not table:
        return []
    body = table.group(1)
    heads = [_clean(h).lower() for h in re.findall(r"(?is)<th[^>]*>(.*?)</th>", body)]

    def col(row, *words):
        for i, h in enumerate(heads):
            if any(w in h for w in words) and i < len(row):
                return _clean(row[i])
        return ""

    out = []
    for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", body):
        cells = re.findall(r"(?is)<td[^>]*>(.*?)</td>", tr)
        if not cells:
            continue
        link = re.search(r'href="([^"]*homework/view[^"]*)"', tr)
        fresh = col(cells, "новых")
        out.append({
            "status": col(cells, "статус"),
            "title": col(cells, "название"),
            "discipline": col(cells, "дисциплин"),
            "event": col(cells, "мероприят"),
            "created": col(cells, "время", "создан"),
            "new": int(fresh) if fresh.isdigit() else 0,
            "href": _html.unescape(link.group(1)) if link else "",
        })
    return out


def threads(cookie: str) -> list:
    page = orioks_web.get_page(cookie, LIST_PATH)
    if _expired(page):
        raise SessionExpired("Сессия ОРИОКС кончилась")
    return parse_list(page)


# ─────────────────────────── отправка ───────────────────────────

def check(fields: dict, known: dict) -> dict:
    """
    Проверка до похода в ОРИОКС: пустое описание или мероприятие чужой
    дисциплины ОРИОКС отклонит молча — той же формой с ошибкой, которую
    ещё надо выковырять. Возвращает чистые поля или бросает ValueError.
    """
    try:
        dis_id = int(fields.get("dis_id") or 0)
        km_id = int(fields.get("km_id") or 0)
        kind = int(fields.get("type") or 0)
    except (TypeError, ValueError):
        raise ValueError("Кривые номера в форме")
    disc = next((d for d in known.get("disciplines", []) if d["id"] == dis_id), None)
    if not disc:
        raise ValueError("Нет такой дисциплины")
    if not any(e["id"] == km_id for e in disc["events"]):
        raise ValueError("Это мероприятие не из выбранной дисциплины")
    if kind not in TYPES:
        raise ValueError("Нет такого типа работы")
    message = str(fields.get("message") or "").strip()
    if not message:
        raise ValueError("Напиши описание — без него ОРИОКС не примет")
    title = str(fields.get("title") or "").strip()[:TITLE_MAX]
    variant = str(fields.get("variant") or "").strip()
    if len(variant) > VARIANT_MAX:
        raise ValueError("Вариант — не длиннее пяти символов")
    return {"title": title, "variant": variant, "dis_id": dis_id,
            "id_km": km_id, "type": kind, "message": message[:MESSAGE_MAX]}


def _csrf(page: str) -> str:
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', page) or \
        re.search(r'name="csrf-token"\s+content="([^"]+)"', page)
    return m.group(1) if m else ""


def _post(cookie: str, path: str, data: dict) -> tuple:
    """POST формы под сессией: (тело ответа, адрес после переадресаций).
    Отдельной функцией — проверки подменяют её и в ОРИОКС не ходят."""
    req = urllib.request.Request(
        BASE + path, data=urllib.parse.urlencode(data).encode("utf-8"),
        headers={"User-Agent": UA, "Cookie": cookie,
                 "Referer": BASE + CREATE_PATH,
                 "Content-Type": "application/x-www-form-urlencoded"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        raise WebError(f"ОРИОКС ответил {e.code} на отправку")
    except Exception as e:                              # noqa: BLE001
        raise WebError(f"ОРИОКС недоступен ({type(e).__name__})")


def submit(cookie: str, fields: dict) -> dict:
    """
    Отправляет работу преподавателю. НЕ ПРОВЕРЕНО ВЖИВУЮ — см. шапку.

    Сначала заново открываем форму: из неё берётся свежий CSRF и список,
    по которому `check` сверяет выбор. Успех у Yii2 — переадресация прочь
    с формы; та же форма в ответе значит «не принял», и тогда отдаём
    текст ошибки со страницы.
    """
    page = orioks_web.get_page(cookie, CREATE_PATH)
    if _expired(page):
        raise SessionExpired("Сессия ОРИОКС кончилась")
    clean = check(fields, parse_form(page))
    token = _csrf(page)
    if not token:
        raise WebError("Не нашёл форму отправки — ОРИОКС изменил страницу")

    data = {"_csrf": token, FORM + "[attachments]": ""}
    for k, v in clean.items():
        data[f"{FORM}[{k}]"] = str(v)
    body, final = _post(cookie, SUBMIT_PATH, data)
    if _expired(body):
        raise SessionExpired("Сессия ОРИОКС кончилась")
    if "/homework/create" in final and FORM + "[message]" in body:
        err = re.search(r'help-block-error">([^<]+)<', body)
        raise WebError(err.group(1).strip() if err else "ОРИОКС не принял работу")
    return {"ok": True, "href": final.replace(BASE, "")}
