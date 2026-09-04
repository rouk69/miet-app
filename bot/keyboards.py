# -*- coding: utf-8 -*-
"""
Инлайн-клавиатуры. Группа кодируется прямо в callback_data — тогда кнопки
под сообщением, вставленным в чужой чат, работают у любого, кто нажмёт,
без серверной сессии. Самое длинное название группы даёт 31 байт при
лимите Telegram в 64, так что запас есть.
"""
from __future__ import annotations

from urllib.parse import quote

from telebot import types

from . import schedule_api as api

SEP = "|"


def webapp_link(url: str | None, group: str | None = None) -> str | None:
    """Подставляет группу в адрес мини-приложения, чтобы оно открылось
    сразу на нужном расписании, а не просило выбрать группу заново."""
    if not url:
        return None
    return f"{url.rstrip('/')}/?group={quote(group)}" if group else url


def cb(*parts) -> str:
    """Собирает callback_data и следит за лимитом в 64 байта."""
    data = SEP.join(str(p) for p in parts)
    if len(data.encode()) > 64:
        raise ValueError(f"callback_data длиннее 64 байт: {data!r}")
    return data


def parse_cb(data: str) -> list[str]:
    return (data or "").split(SEP)


def day_keyboard(group: str, sched: dict, week: int, day: int, cur_week: int,
                 webapp_url: str | None = None) -> types.InlineKeyboardMarkup:
    """
    Дни недели с датами, переключение недель цикла и быстрые действия.
    webapp_url передаётся только в личке: в inline-сообщениях Telegram
    кнопки web_app запрещены, там останется обычная ссылка.
    """
    kb = types.InlineKeyboardMarkup(row_width=3)
    counts = api.day_counts(sched, week)

    row: list[types.InlineKeyboardButton] = []
    for d in range(1, 7):
        date = api.date_for(week, d, cur_week)
        mark = "•" if d == day else ("" if counts[d] else "·")
        label = f"{mark}{api.DAY_SHORT[d]} {date.strftime('%d.%m')}".strip()
        row.append(types.InlineKeyboardButton(
            label, callback_data=cb("d", week, d, group)))
        if len(row) == 3:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)

    prev_w, next_w = (week - 1) % 4, (week + 1) % 4
    kb.row(
        types.InlineKeyboardButton("◀️", callback_data=cb("d", prev_w, day, group)),
        types.InlineKeyboardButton(f"Неделя {week + 1}-я",
                                   callback_data=cb("noop")),
        types.InlineKeyboardButton("▶️", callback_data=cb("d", next_w, day, group)),
    )

    kb.row(
        types.InlineKeyboardButton("📍 Сегодня", callback_data=cb("today", group)),
        types.InlineKeyboardButton("🗓 Неделя", callback_data=cb("w", week, group)),
        types.InlineKeyboardButton("👥 Группа", callback_data=cb("grp")),
    )

    link = webapp_link(webapp_url, group)
    if link:
        kb.row(types.InlineKeyboardButton(
            "📱 Открыть приложение", web_app=types.WebAppInfo(url=link)))
    return kb


def week_keyboard(group: str, week: int,
                  webapp_url: str | None = None) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    prev_w, next_w = (week - 1) % 4, (week + 1) % 4
    kb.row(
        types.InlineKeyboardButton("◀️", callback_data=cb("w", prev_w, group)),
        types.InlineKeyboardButton(f"Неделя {week + 1}-я", callback_data=cb("noop")),
        types.InlineKeyboardButton("▶️", callback_data=cb("w", next_w, group)),
    )
    kb.row(
        types.InlineKeyboardButton("📍 Сегодня", callback_data=cb("today", group)),
        types.InlineKeyboardButton("👥 Группа", callback_data=cb("grp")),
    )
    link = webapp_link(webapp_url, group)
    if link:
        kb.row(types.InlineKeyboardButton(
            "📱 Открыть приложение", web_app=types.WebAppInfo(url=link)))
    return kb


def group_choice_keyboard(matches: list[str]) -> types.InlineKeyboardMarkup:
    """До 12 совпадений по введённому запросу, по две в ряд."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(g, callback_data=cb("set", g))
               for g in matches[:12]]
    for i in range(0, len(buttons), 2):
        kb.row(*buttons[i:i + 2])
    return kb


def start_keyboard(webapp_url: str | None, bot_username: str = "",
                   group: str | None = None) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    link = webapp_link(webapp_url, group)
    if link:
        kb.row(types.InlineKeyboardButton(
            "📱 Открыть приложение", web_app=types.WebAppInfo(url=link)))
    kb.row(types.InlineKeyboardButton(
        "📅 Расписание на сегодня" if group else "👥 Выбрать группу",
        callback_data=cb("today", group) if group else cb("grp")))
    if bot_username:
        kb.row(types.InlineKeyboardButton(
            "💬 Вставить в чат", switch_inline_query=group or ""))
    return kb


def link_keyboard(webapp_url: str | None) -> types.InlineKeyboardMarkup | None:
    """Для inline-сообщений: web_app там нельзя, поэтому обычная ссылка."""
    if not webapp_url:
        return None
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("📱 Приложение", url=webapp_url))
    return kb
