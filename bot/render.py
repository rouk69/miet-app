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

from . import emoji as em
from . import schedule_api as api


TG_LIMIT = 4096


def esc(t) -> str:
    return html.escape(str(t or ""), quote=False)


def clamp(text: str, limit: int = TG_LIMIT) -> str:
    """
    Не даёт сообщению выйти за лимит Telegram.

    Резать вслепую нельзя: обрыв внутри тега («<blockquo») роняет разбор
    HTML, и Telegram отвечает 400 на всё сообщение целиком. Поэтому режем
    по границе блока — по последнему закрытому </blockquote>.
    """
    if len(text) <= limit:
        return text
    tail = "\n\n<i>…показано не всё, открой приложение</i>"
    cut = text[:limit - len(tail)]
    end = cut.rfind("</blockquote>")
    if end != -1:
        cut = cut[:end + len("</blockquote>")]
    else:
        nl = cut.rfind("\n")
        cut = cut[:nl] if nl > 0 else cut
    return cut + tail


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


def lesson_block(l: dict, live: bool = False, custom: bool = True) -> str:
    """
    Одна пара. Три строки, как в эталоне: номер с временем, предмет с типом,
    преподаватель с аудиторией. Тип занятия задаёт иконку — лекция, практика
    и лабораторная различаются с одного взгляда, не вчитываясь.
    """
    num = em.pair_num(l.get("pair"), custom)
    head = f"{num} <b>{esc(l['from'])}</b>–{esc(l['to'])}"
    if live:
        head += f"  {em.ico('bell', custom)} <i>идёт сейчас</i>"

    subject = f"{em.kind_ico(l.get('kindCls', 'oth'), custom)} <b>{esc(l['subject'])}</b>"
    if l.get("kind"):
        subject += f" · {esc(l['kind']).lower()}"
    for f in l.get("flags", []):
        subject += f" <code>{esc(f)}</code>"

    tail = []
    if l.get("teacher"):
        tail.append(f"{em.ico('teacher', custom)} <i>{esc(l['teacher'])}</i>")
    if l.get("room"):
        tail.append(f"{em.ico('room', custom)} <i>{room_label(l['room'])}</i>")

    lines = [head, subject] + ([" · ".join(tail)] if tail else [])
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def _now_pair(lessons: list[dict], now: dt.datetime) -> dict | None:
    mins = now.hour * 60 + now.minute
    def m(t):
        h, x = (t or "0:0").split(":")
        return int(h) * 60 + int(x)
    for l in lessons:
        if m(l["from"]) <= mins < m(l["to"]):
            return l
    return None


def schedule_card(group: str, sched: dict, week: int, day: int, cur_week: int,
                  now: dt.datetime | None = None, custom: bool = True) -> str:
    """Основная карточка расписания на конкретный день."""
    now = now or dt.datetime.now()
    date = api.date_for(week, day, cur_week, now.date())
    is_today = date == now.date()

    lessons = api.lessons_of(sched, week, day)
    live = _now_pair(lessons, now) if is_today else None

    head = f"{em.ico('calendar', custom)} <b>{api.DAY_NAMES[day]} · {api.human_date(date)}</b>"
    if is_today:
        head += " <i>· сегодня</i>"

    sub_bits = [f"{week + 1}-я неделя", esc(group)]
    sem = short_semestr(sched.get("semestr", ""))
    if sem:
        sub_bits.append(sem)
    sub = "<i>" + " · ".join(sub_bits) + "</i>"

    if not lessons:
        body = "\n<blockquote>☕ <b>Пар нет</b>\nМожно выдохнуть</blockquote>"
    else:
        body = "\n" + "\n".join(
            lesson_block(l, live is not None and l is live, custom)
            for l in lessons)

    footer = ""
    if lessons:
        n = len(lessons)
        footer = (f"\n\n{em.ico('time', custom)} <i>{n} "
                  f"{plural(n, 'пара', 'пары', 'пар')} · "
                  f"с {lessons[0]['from']} до {lessons[-1]['to']}</i>")

    return clamp(f"{head}\n{sub}\n{body}{footer}")


def plural(n: int, one: str, few: str, many: str) -> str:
    m10, m100 = n % 10, n % 100
    if m10 == 1 and m100 != 11:
        return one
    if 2 <= m10 <= 4 and not 12 <= m100 <= 14:
        return few
    return many


def week_card(group: str, sched: dict, week: int, cur_week: int,
              custom: bool = True) -> str:
    """Свод на всю неделю. Дни с парами разворачиваются по нажатию."""
    counts = api.day_counts(sched, week)
    lines = [f"{em.ico('calendar', custom)} <b>{week + 1}-я неделя</b> · "
             f"<i>{esc(group)}</i>", ""]
    for d in range(1, 7):
        lessons = api.lessons_of(sched, week, d)
        date = api.date_for(week, d, cur_week)
        head = f"<b>{api.DAY_NAMES[d]}</b>, {date.strftime('%d.%m')}"
        if not lessons:
            lines.append(f"<blockquote>{head} — <i>пар нет</i></blockquote>")
            continue
        rows = "\n".join(
            f"{em.pair_num(l.get('pair'), custom)} <b>{l['from']}</b> "
            f"{esc(l['subject'])}"
            + (f" · <i>{room_label(l['room'])}</i>" if l.get("room") else "")
            for l in lessons)
        lines.append(
            f"<blockquote expandable>{head} — {counts[d]} "
            f"{plural(counts[d], 'пара', 'пары', 'пар')}\n{rows}</blockquote>")
    return clamp("\n".join(lines))


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
