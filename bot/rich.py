# -*- coding: utf-8 -*-
"""
Карточки в формате Rich Message (Bot API 10.1+).

Обычные сообщения умеют лишь b/i/u/s/code/blockquote, поэтому расписание
раньше приходилось выкладывать столбиком из цитат. Rich-сообщения понимают
настоящую разметку: таблицы с рамками и вертикальным выравниванием,
заголовки, и — главное — кнопки прямо в теле сообщения, со своим цветом.

Отправляется методом sendRichMessage, правится через editMessageText с
полем rich_message. Разметка — «Rich HTML style», это отдельный набор
тегов, шире обычного.
"""
from __future__ import annotations

import datetime as dt
import html

from . import emoji as em
from . import keyboards as kbs
from . import render
from . import schedule_api as api

# Стили кнопок из Bot API: primary, success, danger, link — плюс обычная
# без стиля. Тип disabled рисует некликабельную подпись.
STYLE_ACTIVE = "primary"
STYLE_ACTION = "link"
STYLE_SHARE = "success"


def esc(t) -> str:
    """Экранирование для текста и для значений атрибутов."""
    return html.escape(str(t or ""), quote=True)


def button(label: str, *, type: str = "callback_data", data: str = "",
           url: str = "", query: str | None = None, style: str = "") -> str:
    attrs = [f'type="{type}"']
    if style:
        attrs.append(f'style="{style}"')
    if data:
        attrs.append(f'data="{esc(data)}"')
    if url:
        attrs.append(f'url="{esc(url)}"')
    if query is not None:
        attrs.append(f'query="{esc(query)}"')
    return f'<tg-button {" ".join(attrs)}>{esc(label)}</tg-button>'


def row(*buttons: str, align: str = "") -> str:
    a = f' align="{align}"' if align else ""
    return f"<tg-button-row{a}>{''.join(buttons)}</tg-button-row>"


# ─────────────────────────── таблица дня ───────────────────────────

def lesson_rows(lessons: list[dict], live: dict | None, custom: bool) -> str:
    out = []
    for l in lessons:
        num = em.pair_num(l.get("pair"), custom)
        left = f'{num} {esc(l["from"])}'

        subject = (f'{em.kind_ico(l.get("kindCls", "oth"), custom)} '
                   f'<b>{esc(l["subject"])}</b>')
        if l.get("kind"):
            subject += f' · {esc(l["kind"]).lower()}'
        for f in l.get("flags", []):
            subject += f" <code>{esc(f)}</code>"
        if l is live:
            subject += f" {em.ico('bell', custom)} <mark>идёт</mark>"

        meta = []
        if l.get("teacher"):
            meta.append(esc(l["teacher"]))
        if l.get("room"):
            meta.append(render.room_label(l["room"]))
        right = subject + (f'<br><i>{" · ".join(meta)}</i>' if meta else "")

        out.append(
            f'<tr><td align="center" valign="middle">{left}</td>'
            f'<td valign="middle">{right}</td></tr>')
    return "".join(out)


def day_buttons(group: str, sched: dict, week: int, day: int, cur_week: int,
                webapp_url: str | None) -> str:
    """Ряды кнопок под таблицей: дни, недели, действия."""
    counts = api.day_counts(sched, week)
    parts = []

    days = []
    for d in range(1, 7):
        date = api.date_for(week, d, cur_week)
        label = f"{api.DAY_SHORT[d]} {date.strftime('%d.%m')}"
        if not counts[d]:
            label = f"· {label}"
        days.append(button(label, data=kbs.cb("d", week, d, group),
                           style=STYLE_ACTIVE if d == day else ""))
    parts.append(row(*days[:3]))
    parts.append(row(*days[3:]))

    prev_w, next_w = (week - 1) % 4, (week + 1) % 4
    parts.append(row(
        button("◀️", data=kbs.cb("d", prev_w, day, group)),
        button(f"Неделя {week + 1}-я", type="disabled"),
        button("▶️", data=kbs.cb("d", next_w, day, group)),
    ))

    parts.append(row(
        button("Сегодня", data=kbs.cb("today", group), style=STYLE_ACTION),
        button("Неделя", data=kbs.cb("w", week, group), style=STYLE_ACTION),
        button("Группа", data=kbs.cb("grp"), style=STYLE_ACTION),
    ))

    share = button("Отправить в чат", type="switch_inline_query",
                   query=group, style=STYLE_SHARE)
    link = kbs.webapp_link(webapp_url, group)
    if link:
        # web_app-кнопки Telegram разрешает только в личных чатах.
        parts.append(row(share, button("Приложение", type="web_app",
                                       url=link, style=STYLE_ACTIVE)))
    else:
        parts.append(row(share))
    return "".join(parts)


def day_html(group: str, sched: dict, week: int, day: int, cur_week: int,
             now: dt.datetime | None = None, custom: bool = True,
             webapp_url: str | None = None, buttons: bool = True) -> str:
    now = now or dt.datetime.now()
    date = api.date_for(week, day, cur_week, now.date())
    is_today = date == now.date()
    lessons = api.lessons_of(sched, week, day)
    live = render._now_pair(lessons, now) if is_today else None

    head = (f'<h3>{em.ico("calendar", custom)} {api.DAY_NAMES[day]} · '
            f'{api.human_date(date)}{" · сегодня" if is_today else ""}</h3>')

    sub_bits = [f"{week + 1}-я неделя", esc(group)]
    sem = render.short_semestr(sched.get("semestr", ""))
    if sem:
        sub_bits.append(sem)
    sub = f'<p><i>{" · ".join(sub_bits)}</i></p>'

    if lessons:
        body = (f'<table bordered compact>'
                f'{lesson_rows(lessons, live, custom)}</table>')
        n = len(lessons)
        body += (f'<p><i>{em.ico("time", custom)} {n} '
                 f'{render.plural(n, "пара", "пары", "пар")} · '
                 f'с {lessons[0]["from"]} до {lessons[-1]["to"]}</i></p>')
    else:
        body = "<blockquote>☕ Пар нет — можно выдохнуть</blockquote>"

    tail = day_buttons(group, sched, week, day, cur_week, webapp_url) \
        if buttons else ""
    return head + sub + body + tail


# ─────────────────────────── свод недели ───────────────────────────

def week_html(group: str, sched: dict, week: int, cur_week: int,
              custom: bool = True, webapp_url: str | None = None,
              buttons: bool = True) -> str:
    head = (f'<h3>{em.ico("calendar", custom)} {week + 1}-я неделя</h3>'
            f'<p><i>{esc(group)}</i></p>')

    rows_html = []
    for d in range(1, 7):
        lessons = api.lessons_of(sched, week, d)
        date = api.date_for(week, d, cur_week)
        left = f'<b>{api.DAY_SHORT[d]}</b><br>{date.strftime("%d.%m")}'
        if not lessons:
            right = "<i>пар нет</i>"
        else:
            right = "<br>".join(
                f'{esc(l["from"])} · {esc(l["subject"])}'
                + (f' · <i>{render.room_label(l["room"])}</i>'
                   if l.get("room") else "")
                for l in lessons)
        rows_html.append(
            f'<tr><td align="center" valign="middle">{left}</td>'
            f'<td valign="middle">{right}</td></tr>')

    body = f'<table bordered compact>{"".join(rows_html)}</table>'

    tail = ""
    if buttons:
        prev_w, next_w = (week - 1) % 4, (week + 1) % 4
        tail = row(
            button("◀️", data=kbs.cb("w", prev_w, group)),
            button(f"Неделя {week + 1}-я", type="disabled"),
            button("▶️", data=kbs.cb("w", next_w, group)),
        ) + row(
            button("Сегодня", data=kbs.cb("today", group), style=STYLE_ACTION),
            button("Группа", data=kbs.cb("grp"), style=STYLE_ACTION),
        )
    return head + body + tail


# ─────────────────────── выбор группы кнопками ───────────────────────

def _grid(buttons: list[str], per_row: int) -> str:
    return "".join(row(*buttons[i:i + per_row])
                   for i in range(0, len(buttons), per_row))


def prefixes_html(groups: list[str], current: str | None = None,
                  custom: bool = True) -> str:
    """Первый шаг: направления. Тридцать с небольшим кнопок влезают разом,
    поэтому листать ничего не нужно."""
    prefixes = api.group_prefixes(groups)
    head = (f'<h3>{em.ico("graduate", custom)} Выбор группы</h3>'
            f'<p><i>Направление, потом номер. Или просто пришли название — '
            f'например <code>ПИН-31</code>.</i></p>')
    cur_pref = api.group_prefix(current) if current else None
    btns = [button(p, data=kbs.cb("gp", p),
                   style=STYLE_ACTIVE if p == cur_pref else "")
            for p in prefixes]
    return head + _grid(btns, 4)


def group_list_html(groups: list[str], prefix: str, current: str | None = None,
                    custom: bool = True) -> str:
    """Второй шаг: конкретные группы направления."""
    items = api.groups_with_prefix(groups, prefix)
    head = (f'<h3>{em.ico("graduate", custom)} {esc(prefix)}</h3>'
            f'<p><i>{len(items)} '
            f'{render.plural(len(items), "группа", "группы", "групп")} — '
            f'нажми свою, расписание откроется сразу</i></p>')
    btns = [button(g, data=kbs.cb("set", g),
                   style=STYLE_ACTIVE if g == current else "")
            for g in items]
    back = row(button("← Все направления", data=kbs.cb("grp"),
                      style=STYLE_ACTION))
    return head + _grid(btns, 3) + back


def support_html(custom: bool = True, webapp_url: str | None = None) -> str:
    """Раздел поддержки: кто сделал и куда писать."""
    head = f'<h3>{em.ico("info", custom)} Поддержка</h3>'
    body = ('<p>Приложение и бот сделаны студентом для студентов МИЭТ. '
            'Если что-то сломалось, показывает не то расписание или хочется '
            'новой функции — напиши, разберёмся.</p>'
            f'<p>Автор и поддержка: <b>@{render.OWNER}</b></p>'
            '<p><i>Бот неофициальный. Расписание и справочная информация '
            'берутся с miet.ru.</i></p>')
    btns = [button("Написать автору", type="url",
                   url=f"https://t.me/{render.OWNER}", style=STYLE_ACTIVE)]
    link = webapp_link(webapp_url)
    if link:
        btns.append(button("Приложение", type="web_app", url=link))
    return head + body + row(*btns)
