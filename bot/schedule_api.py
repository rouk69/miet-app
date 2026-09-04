# -*- coding: utf-8 -*-
"""
Клиент расписания МИЭТ. Порт js/schedule.js — логика недель и разбора
предметов должна совпадать с мини-приложением, иначе бот и веб-версия
покажут разные пары.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import threading
import time
from typing import Any

import requests

API = "https://miet.ru/schedule/data"
GROUPS_API = "https://miet.ru/schedule/groups"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
TTL = 6 * 60 * 60          # расписание меняется редко, но не «никогда»
GROUPS_TTL = 24 * 60 * 60

# Версия формата разобранного расписания. Меняется, когда в записи пары
# появляются новые поля: старые файлы кеша тогда просто перестают находиться,
# а не отдают наружу записи без нужных ключей.
CACHE_VERSION = 2

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

DAY_NAMES = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
DAY_SHORT = ["", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]
MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]

_session = requests.Session()
_session.headers.update({"User-Agent": UA})
# Пул соединений под многопоточный опрос: иначе requests держит по 10 на хост
# и потоки начинают ждать друг друга на ровном месте.
_session.mount("https://", requests.adapters.HTTPAdapter(
    pool_connections=4, pool_maxsize=20, max_retries=2))

_mem: dict[str, tuple[float, Any]] = {}

# Замок на каждую группу отдельно, а не один общий: общий сериализовал бы
# все запросы и при десятке пользователей они вставали бы в очередь. Здесь
# же параллельные запросы разных групп идут одновременно, а одинаковые —
# ждут первого и берут готовый результат из кеша.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


# ─────────────────────────── кеш ───────────────────────────

def _cache_path(key: str) -> str:
    safe = re.sub(r"[^0-9A-Za-zА-Яа-яёЁ_-]", "_", key)
    return os.path.join(CACHE_DIR, f"v{CACHE_VERSION}_{safe}.json")


def _cache_get(key: str, ttl: int):
    hit = _mem.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    p = _cache_path(key)
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < ttl:
        try:
            data = json.load(open(p, encoding="utf-8"))
            _mem[key] = (os.path.getmtime(p), data)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _cache_put(key: str, data) -> None:
    _mem[key] = (time.time(), data)
    try:
        json.dump(data, open(_cache_path(key), "w", encoding="utf-8"),
                  ensure_ascii=False)
    except OSError:
        pass       # кеш не критичен, работаем и без него


# ─────────────────────── даты и недели ───────────────────────

def monday_of(d: dt.date) -> dt.date:
    """Понедельник недели, в которую попадает дата (воскресенье — к прошедшей)."""
    return d - dt.timedelta(days=d.weekday())


def semester_start(semestr: str) -> dt.date:
    """Осенний семестр считаем с 1 сентября, весенний — с 9 февраля."""
    m = re.search(r"(\d{4})\s*/\s*(\d{4})", semestr or "")
    autumn = bool(re.search(r"осен", semestr or "", re.I))
    today = dt.date.today()
    if not m:
        return (dt.date(today.year, 9, 1) if autumn or today.month >= 8
                else dt.date(today.year, 2, 9))
    return dt.date(int(m.group(1)), 9, 1) if autumn else dt.date(int(m.group(2)), 2, 9)


def week_of_cycle(d: dt.date, semestr: str, shift: int = 0) -> int:
    """Номер недели в четырёхнедельном цикле МИЭТ, 0..3."""
    start = monday_of(semester_start(semestr))
    weeks = (monday_of(d) - start).days // 7
    return (weeks + shift) % 4


def human_date(d: dt.date) -> str:
    return f"{d.day} {MONTHS_GEN[d.month - 1]}"


# ─────────────────────── разбор предмета ───────────────────────

KIND_MAP = {"лек": ("Лекция", "📘", "lek"),
            "пр": ("Практика", "✏️", "pr"),
            "лаб": ("Лабораторная", "🔬", "lab")}


def parse_subject(raw: str) -> dict:
    """«[ФТД] [ДСТ] Быстрые алгоритмы [Лек]» → части."""
    name = (raw or "").strip()
    flags: list[str] = []

    def grab(m):
        flags.append(m.group(1).upper())
        return ""

    name = re.sub(r"\[(ФТД|ДСТ|ФАК)\]", grab, name, flags=re.I)
    kind = ""
    m = re.search(r"\[([^\]]+)\]\s*$", name)
    if m:
        kind = m.group(1).strip()
        name = name[:m.start()]
    name = re.sub(r"\s{2,}", " ", name).strip()

    low = kind.lower()
    label, emoji, cls = kind, "📗", "oth"
    for pref, (lbl, emo, code) in KIND_MAP.items():
        if low.startswith(pref):
            label, emoji, cls = lbl, emo, code
            break
    # cls повторяет kindCls из js/schedule.js: по нему и веб, и бот выбирают
    # оформление типа занятия, и коды обязаны совпадать.
    return {"name": name, "kind": label, "emoji": emoji, "cls": cls,
            "flags": flags}


_hhmm = lambda s: (re.search(r"T(\d{2}:\d{2})", s or "") or [None, ""])[1] \
    if re.search(r"T(\d{2}:\d{2})", s or "") else ""


def _time_of(iso: str) -> str:
    m = re.search(r"T(\d{2}:\d{2})", iso or "")
    return m.group(1) if m else ""


# ─────────────────────── запросы к API ───────────────────────

def fetch_groups(force: bool = False) -> list[str]:
    if not force:
        hit = _cache_get("groups", GROUPS_TTL)
        if hit:
            return hit
    r = _session.get(GROUPS_API, timeout=25)
    r.encoding = "utf-8"
    groups = r.json()
    _cache_put("groups", groups)
    return groups


def _normalize(js: dict) -> dict:
    times = [{"code": t.get("Code"), "label": t.get("Time"),
              "from": _time_of(t.get("TimeFrom")), "to": _time_of(t.get("TimeTo"))}
             for t in js.get("Times", [])]
    lessons = []
    for d in js.get("Data", []):
        cls = d.get("Class") or {}
        s = parse_subject(cls.get("Name"))
        lessons.append({
            "day": d.get("Day"),                     # 1..6 — Пн..Сб
            "week": d.get("DayNumber"),              # 0..3 — неделя цикла
            "pair": (d.get("Time") or {}).get("Code"),
            "from": _time_of((d.get("Time") or {}).get("TimeFrom")),
            "to": _time_of((d.get("Time") or {}).get("TimeTo")),
            "subject": s["name"],
            "kind": s["kind"],
            "kindCls": s["cls"],
            "emoji": s["emoji"],
            "flags": s["flags"],
            "teacher": cls.get("Teacher") or cls.get("TeacherFull") or "",
            "room": (d.get("Room") or {}).get("Name") or "",
        })
    lessons.sort(key=lambda x: (x["day"] or 0, x["pair"] or 0))
    return {"semestr": js.get("Semestr", ""), "times": times, "lessons": lessons}


def fetch_schedule(group: str, force: bool = False) -> dict:
    key = f"sched_{group}"
    if not force:
        hit = _cache_get(key, TTL)
        if hit:
            return hit
    with _lock_for(key):
        # Пока ждали замок, соседний поток мог уже всё скачать.
        if not force:
            hit = _cache_get(key, TTL)
            if hit:
                return hit
        r = _session.get(API, params={"group": group}, timeout=20)
        r.encoding = "utf-8"
        if r.status_code != 200:
            raise RuntimeError(f"Расписание недоступно ({r.status_code})")
        data = _normalize(r.json())
        _cache_put(key, data)
    return data


def cached_schedule(group: str) -> dict | None:
    """Отдаёт расписание, только если оно уже в кеше. Нужно inline-режиму:
    там на ответ есть секунды, и лезть в сеть за каждым кандидатом нельзя."""
    return _cache_get(f"sched_{group}", TTL)


def lessons_of(sched: dict, week: int, day: int) -> list[dict]:
    return [l for l in sched.get("lessons", [])
            if l["week"] == week and l["day"] == day]


def day_counts(sched: dict, week: int) -> list[int]:
    c = [0] * 7
    for l in sched.get("lessons", []):
        if l["week"] == week and 1 <= (l["day"] or 0) <= 6:
            c[l["day"]] += 1
    return c


def resolve_group(query: str, groups: list[str]) -> list[str]:
    """Ищет группу по неточному вводу: регистр и пробелы не важны."""
    q = re.sub(r"\s+", "", (query or "").lower()).replace("ё", "е")
    if not q:
        return []
    exact = [g for g in groups
             if re.sub(r"\s+", "", g.lower()).replace("ё", "е") == q]
    if exact:
        return exact
    return [g for g in groups
            if q in re.sub(r"\s+", "", g.lower()).replace("ё", "е")]


def date_for(week: int, day: int, cur_week: int, today: dt.date | None = None) -> dt.date:
    """Календарная дата для дня выбранной недели цикла."""
    today = today or dt.date.today()
    mon = monday_of(today) + dt.timedelta(weeks=week - cur_week)
    return mon + dt.timedelta(days=day - 1)
