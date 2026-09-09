# -*- coding: utf-8 -*-
"""
Сторож объявлений ОРИОКС: бот сам говорит, что задали.

Объявление преподавателя («Задание к семинару», «Подготовка к ЛР №1») —
единственное место, где в ОРИОКС лежит текст домашнего задания. Оно уже
собирается для экрана «Учёба», но экран открывают, когда задание и так
вспомнили. Смысл появляется от обратного хода: преподаватель написал —
человек узнал, не открывая ничего.

Три правила, из-за которых модуль устроен именно так:

**Первый заход молчит.** У студента к середине семестра два десятка
объявлений, и рассылка «нового» на пустой памяти означала бы двадцать
сообщений подряд. Поэтому первый обход только запоминает, что есть, а
говорить начинает со второго.

**Ночью не пишем.** Преподаватели выкладывают задания и в полночь, но
сообщение в это время — не забота, а побудка. Окно проверок дневное;
объявление, пришедшее ночью, найдётся утром и не пропадёт: память
хранится в базе, а не в счётчике «последних N».

**Молчание ОРИОКС — не повод стирать доступ.** Сессию убирает только
явный отказ (`SessionExpired`), любая другая ошибка означает «попробуем
через полтора часа». Иначе человек вводил бы пароль после каждой заминки
института — на эти грабли проект уже наступал.
"""
from __future__ import annotations

import datetime as dt
import logging
import threading
import time

from . import notify, orioks, orioks_web
from .db import conn
from .render import esc

log = logging.getLogger("miet.orioks.watch")

# Полтора часа. Объявление пишут к занятию, а не к минуте: приходить
# чаще значит дёргать сервер института ради того же самого ответа.
EVERY = 90 * 60

# Дневное окно по Москве. Начало — до первой пары, конец — раньше, чем
# человек ложится: сообщение о домашнем задании в час ночи ничего не
# меняет, кроме сна.
DAY_FROM, DAY_TO = 8, 22

# Сколько объявлений показываем в одном сообщении. Больше трёх — уже
# полотно, а остальное всё равно лежит в приложении.
IN_MESSAGE = 3

# Пауза между людьми. Telegram терпит около двадцати сообщений в секунду,
# но узкое место здесь не он, а ОРИОКС: обход одного студента — это по
# запросу на каждую его дисциплину.
BETWEEN = 2.0


def msk_now() -> dt.datetime:
    return dt.datetime.utcnow() + dt.timedelta(hours=3)


def daytime(now: dt.datetime | None = None) -> bool:
    return DAY_FROM <= (now or msk_now()).hour < DAY_TO


# ─────────────────────────── память ───────────────────────────

def seen_ids(user_id: int) -> set:
    return {row[0] for row in conn().execute(
        "SELECT news_id FROM orioks_seen WHERE user_id=?", (user_id,))}


def remember(user_id: int, ids) -> None:
    rows = [(user_id, str(i)) for i in ids if i]
    if not rows:
        return
    with conn().transaction() as c:
        c.executemany(
            "INSERT OR IGNORE INTO orioks_seen (user_id, news_id) VALUES (?, ?)",
            rows)


def forget(user_id: int) -> None:
    """Отключил ОРИОКС — память об объявлениях уходит вместе с доступом."""
    conn().execute("DELETE FROM orioks_seen WHERE user_id=?", (user_id,))


def watchers() -> list:
    """Кому есть что сторожить: подключённые, с сессией и без отказа."""
    return [row[0] for row in conn().execute(
        "SELECT user_id FROM orioks_links "
        "WHERE web_cookie IS NOT NULL AND web_cookie<>'' "
        "AND COALESCE(notify, 1)=1")]


def notify_on(user_id: int) -> bool:
    row = conn().execute("SELECT COALESCE(notify, 1) FROM orioks_links "
                         "WHERE user_id=?", (user_id,)).fetchone()
    return bool(row[0]) if row else False


def set_notify(user_id: int, on: bool) -> None:
    conn().execute("UPDATE orioks_links SET notify=? WHERE user_id=?",
                   (1 if on else 0, user_id))


# ─────────────────────────── сообщение ───────────────────────────

SITE = "https://orioks.miet.ru"


def _link(href: str) -> str:
    href = str(href or "")
    if href.startswith("http"):
        return href
    return SITE + (href if href.startswith("/") else "/" + href)


def message(items: list) -> str:
    """
    Одно сообщение обо всём новом.

    Заголовок объявления бывает бессодержательным («Новость», «Внимание»),
    поэтому выжимка идёт следом и своей строкой: по ней и понятно, что
    именно задали.
    """
    head = ("📌 <b>Новое задание в ОРИОКС</b>" if len(items) == 1
            else f"📌 <b>Новых объявлений: {len(items)}</b>")
    parts = [head, ""]
    for it in items[:IN_MESSAGE]:
        subject = esc(it.get("discipline") or "ОРИОКС")
        title = esc(it.get("title") or "Объявление")
        parts.append(f"<b>{subject}</b>")
        parts.append(f'<a href="{esc(_link(it.get("href")))}">{title}</a>')
        preview = (it.get("preview") or "").strip()
        if preview:
            short = preview if len(preview) <= 220 else preview[:217] + "…"
            parts.append(f"<blockquote>{esc(short)}</blockquote>")
        author = (it.get("author") or "").strip()
        when = (it.get("date") or "").strip()
        sign = " · ".join(x for x in (author, when) if x)
        if sign:
            parts.append(f"<i>{esc(sign)}</i>")
        parts.append("")
    if len(items) > IN_MESSAGE:
        parts.append(f"<i>И ещё {len(items) - IN_MESSAGE} — "
                     f"в приложении, раздел «Учёба».</i>")
    return "\n".join(parts).strip()


# ─────────────────────────── обход ───────────────────────────

def check_user(user_id: int, send: bool = True) -> list:
    """
    Один студент: что у него появилось нового.

    Возвращает новые объявления. Первый заход возвращает пустой список и
    только запоминает — иначе подключение ОРИОКС оборачивалось бы
    рассылкой всего семестра разом.
    """
    cookie = orioks.cookie_of(user_id)
    if not cookie:
        return []

    try:
        items = orioks_web.course_news(cookie)
    except orioks_web.SessionExpired:
        # Явный отказ: сессия кончилась. Стираем её и говорим об этом
        # один раз — без cookie следующий обход этого человека пропустит.
        orioks.drop_cookie(user_id)
        orioks.forget_materials(user_id)
        if send:
            notify.to_user(user_id, (
                "🔑 <b>ОРИОКС попросил войти заново</b>\n\n"
                "Сессия кончилась — это обычное дело. Открой раздел "
                "«Учёба» в приложении и подключись ещё раз, тогда я снова "
                "буду говорить о новых заданиях."))
        return []
    except orioks_web.WebError as e:
        # Институт молчит или сменил вёрстку. Доступ не трогаем: он
        # рабочий, а вот попытка — нет.
        log.info("объявления %s не забрались: %s", user_id, e)
        return []

    known = seen_ids(user_id)
    fresh = [it for it in items if it.get("id") and str(it["id"]) not in known]

    # Первый заход: помечаем всё известным и молчим.
    if not known:
        remember(user_id, [it.get("id") for it in items])
        log.info("сторож ОРИОКС начал следить за %s (%d объявлений)",
                 user_id, len(items))
        return []

    if not fresh:
        return []

    # Запоминаем ДО отправки: не ушло сообщение — беда невелика, а вот
    # повторять его каждые полтора часа человек не простит.
    remember(user_id, [it.get("id") for it in fresh])
    if send:
        notify.to_user(user_id, message(fresh))
    return fresh


def round_once(send: bool = True) -> int:
    """Обход всех, кто подписан. Возвращает, скольким ушло."""
    told = 0
    for uid in watchers():
        try:
            if check_user(uid, send=send):
                told += 1
        except Exception:                                  # noqa: BLE001
            log.exception("сторож ОРИОКС споткнулся на %s", uid)
        time.sleep(BETWEEN)
    return told


def run_in_background() -> threading.Thread:
    """Фоновый сторож. Наружу не падает — бот важнее объявлений."""
    def loop():
        # Ждём дольше остальных задач: при старте контейнера сначала
        # должен подняться опрос Telegram и справочник, а объявления
        # минутой раньше или позже никого не спасают.
        time.sleep(120)
        while True:
            try:
                if daytime():
                    round_once()
            except Exception:
                log.exception("обход ОРИОКС сорвался")
            time.sleep(EVERY)

    t = threading.Thread(target=loop, name="orioks-watch", daemon=True)
    t.start()
    return t
