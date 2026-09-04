# -*- coding: utf-8 -*-
"""
Сборка сообщений бота. Telegram понимает ограниченный HTML: b, i, u, s,
a, code, pre, blockquote. Каждая пара — отдельный blockquote, клиент рисует
его скруглённым блоком, поэтому карточка выглядит как таблица.
"""
from __future__ import annotations

import datetime as dt
import html
import re

from . import schedule_api as api


def esc(t) -> str:
    return html.escape(str(t or ""), quote=False)


PAIR_BADGE = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
              5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣"}


def short_semestr(s: str) -> str:
    m = re.search(r"(\d{4})\s*/\s*(\d{4})", s or "")
    season = "осень" if re.search(r"осен", s or "", re.I) else \
             "весна" if re.search(r"весен", s or "", re.I) else ""
    return f"{season} {m.group(1)}/{m.group(2)[2:]}".strip() if m else (season or "")


def room_label(room: str) -> str:
    """
    «1204 м» → «ауд. 1204 м», но «Виртуальная аудитория 10» оставляем как есть:
    приписка «ауд.» к такому названию читается как масло масляное.
    """
    r = (room or "").strip()
    return f"ауд. {esc(r)}" if re.match(r"^\d", r) else esc(r)


def lesson_block(l: dict, live: bool = False) -> str:
    """Одна пара — blockquote с номером, временем, предметом и деталями."""
    badge = PAIR_BADGE.get(l.get("pair"), "•")
    head = f"{badge} <b>{esc(l['from'])}–{esc(l['to'])}</b>"
    if live:
        head += "  ← <i>идёт сейчас</i>"

    meta = []
    if l.get("kind"):
        meta.append(esc(l["kind"]))
    if l.get("teacher"):
        meta.append(esc(l["teacher"]))
    if l.get("room"):
        meta.append(room_label(l["room"]))
    tail = " · ".join(meta)

    flags = "".join(f" <code>{esc(f)}</code>" for f in l.get("flags", []))

    return (f"<blockquote>{head}\n"
            f"{l.get('emoji', '📗')} <b>{esc(l['subject'])}</b>{flags}\n"
            f"{tail}</blockquote>")


def _now_pair(lessons: list[dict], now: dt.datetime) -> dict | None:
    mins = now.hour * 60 + now.minute
    def m(t):
        h, x = (t or "0:0").split(":")
        return int(h) * 60 + int(x)
    for l in lessons:
        if m(l["from"]) <= mins < m(l["to"]):
            return l
    return None


def schedule_card(group: str, sched: dict, week: int, day: int,
                  cur_week: int, now: dt.datetime | None = None) -> str:
    """Основная карточка расписания на конкретный день."""
    now = now or dt.datetime.now()
    date = api.date_for(week, day, cur_week, now.date())
    is_today = date == now.date()

    lessons = api.lessons_of(sched, week, day)
    live = _now_pair(lessons, now) if is_today else None

    title = api.DAY_NAMES[day]
    head = f"🗓 <b>{title} · {api.human_date(date)}</b>"
    if is_today:
        head += "  <i>· сегодня</i>"

    sub_bits = [f"{week + 1}-я неделя", esc(group)]
    sem = short_semestr(sched.get("semestr", ""))
    if sem:
        sub_bits.append(sem)
    sub = " · ".join(sub_bits)

    if not lessons:
        body = "\n<blockquote>☕ <b>Пар нет</b>\nМожно выдохнуть</blockquote>"
    else:
        body = "\n" + "\n".join(
            lesson_block(l, live is not None and l is live) for l in lessons)

    footer = ""
    if lessons:
        n = len(lessons)
        footer = (f"\n\n<i>{n} {plural(n, 'пара', 'пары', 'пар')} · "
                  f"с {lessons[0]['from']} до {lessons[-1]['to']}</i>")

    return f"{head}\n{sub}\n{body}{footer}"


def plural(n: int, one: str, few: str, many: str) -> str:
    m10, m100 = n % 10, n % 100
    if m10 == 1 and m100 != 11:
        return one
    if 2 <= m10 <= 4 and not 12 <= m100 <= 14:
        return few
    return many


def week_card(group: str, sched: dict, week: int, cur_week: int) -> str:
    """Свод на всю неделю — компактно, по дням."""
    counts = api.day_counts(sched, week)
    lines = [f"🗓 <b>{week + 1}-я неделя</b> · {esc(group)}", ""]
    for d in range(1, 7):
        lessons = api.lessons_of(sched, week, d)
        date = api.date_for(week, d, cur_week)
        if not lessons:
            lines.append(f"<blockquote><b>{api.DAY_SHORT[d]} {date.strftime('%d.%m')}</b> — "
                         f"<i>пар нет</i></blockquote>")
            continue
        rows = "\n".join(
            f"{l['from']} · {esc(l['subject'])}"
            + (f" · {esc(l['room'])}" if l.get("room") else "")
            for l in lessons)
        lines.append(f"<blockquote expandable><b>{api.DAY_SHORT[d]} {date.strftime('%d.%m')}</b>"
                     f" — {counts[d]} {plural(counts[d], 'пара', 'пары', 'пар')}\n"
                     f"{rows}</blockquote>")
    return "\n".join(lines)


def no_group_text() -> str:
    return ("👋 <b>Расписание МИЭТ</b>\n\n"
            "Сначала выбери свою группу — дальше бот будет открываться сразу "
            "на сегодняшнем дне.\n\n"
            "Просто отправь название: <code>ПИН-31</code>, <code>ЭН-24</code> "
            "и так далее.")


def start_text(name: str | None = None) -> str:
    hi = f"Привет, {esc(name)}!" if name else "Привет!"
    return (f"👋 <b>{hi}</b>\n\n"
            "Я показываю расписание НИУ МИЭТ — прямо с miet.ru, всегда свежее.\n\n"
            "<blockquote>📅 Пары на любой день и неделю цикла\n"
            "🔍 Поиск по 346 группам\n"
            "📱 Мини-приложение: новости, кружки, кампус\n"
            "💬 Работает в любом чате через <code>@имя_бота</code></blockquote>\n"
            "Выбери группу — и поехали.")


def help_text(bot_username: str = "") -> str:
    mention = f"@{bot_username}" if bot_username else "@имя_бота"
    return ("<b>Как пользоваться</b>\n\n"
            "<blockquote><b>Команды</b>\n"
            "/start — начало и выбор группы\n"
            "/today — пары на сегодня\n"
            "/tomorrow — на завтра\n"
            "/week — вся неделя\n"
            "/group — сменить группу\n"
            "/shift — поправка недели цикла</blockquote>\n"
            "<blockquote><b>В любом чате</b>\n"
            f"Напиши <code>{mention}</code> и пробел — бот предложит вставить "
            "карточку расписания. Кнопки под ней работают у всех.\n\n"
            f"<code>{mention} ПИН-31</code> — расписание конкретной группы.</blockquote>\n"
            "<blockquote><b>Неделя цикла</b>\n"
            "В МИЭТе четырёхнедельный цикл. Бот считает неделю от начала "
            "семестра. Если счёт разошёлся с деканатом — поправь через "
            "/shift, бот запомнит.</blockquote>")
