# -*- coding: utf-8 -*-
"""
Бот расписания НИУ МИЭТ.

    pip install -r bot/requirements.txt
    set BOT_TOKEN=123456:AA...
    set WEBAPP_URL=https://ваш-домен      (необязательно)
    python -m bot.main

Три режима работы:
  • личка — команды, выбор группы, кнопка мини-приложения;
  • inline — @бот в любом чате вставляет карточку с рабочими кнопками;
  • кнопки — переключают день и неделю прямо в сообщении.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import sys

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

from . import keyboards as kbs
from . import render
from . import schedule_api as api
from . import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("miet-bot")


class ShortNetworkErrors(logging.Filter):
    """
    Сворачивает простыни telebot про обрыв связи в одну строку.

    Через VPN или корпоративный прокси соединение с api.telegram.org рвётся
    раз в несколько минут — infinity_polling переподключается сам, но на
    каждый обрыв кладёт в лог полный трейсбек на сотню строк, и за час их
    набегает на треть мегабайта. Сообщение оставляем, полотно убираем.
    """

    NOISE = ("Connection aborted", "ConnectionResetError", "ConnectionError",
             "ReadTimeout", "Max retries exceeded", "Connection reset")

    def filter(self, record: logging.LogRecord) -> bool:
        text = str(record.getMessage())
        if any(n in text for n in self.NOISE):
            first = text.strip().splitlines()[0][:120]
            record.msg = f"связь с Telegram оборвалась, переподключаюсь ({first})"
            record.args = ()
            record.exc_info = None
            record.levelno, record.levelname = logging.WARNING, "WARNING"
        return True


telebot.logger.addFilter(ShortNetworkErrors())

def load_env(path: str = ".env") -> None:
    """
    Читает .env, если он есть. Файл лежит в .gitignore — токен не должен
    попадать в репозиторий. Уже заданные переменные окружения не трогаем:
    в проде настройки приходят оттуда, а не из файла.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, path)
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
WEBAPP_URL = os.environ.get("WEBAPP_URL", "").strip()

if not BOT_TOKEN:
    sys.exit("Не задан BOT_TOKEN. Получи токен у @BotFather и положи в переменную "
             "окружения:\n    set BOT_TOKEN=123456:AA...")

# Мини-приложение Telegram открывает только по https, локальный адрес
# он молча проигнорирует — лучше сразу не показывать кнопку.
if WEBAPP_URL and not WEBAPP_URL.startswith("https://"):
    log.warning("WEBAPP_URL не https — кнопка мини-приложения показана не будет")
    WEBAPP_URL = ""

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
BOT_USERNAME = ""

INLINE_LIMIT = 4     # сколько вариантов показать в inline-подсказке
INLINE_FETCH = 2     # из них — за сколькими можно сходить в сеть


# ─────────────────────────── помощники ───────────────────────────

def user_ctx(user_id: int) -> dict:
    return storage.get_user(user_id)


def today_day() -> int:
    """1..6 для Пн..Сб; воскресенье показываем как понедельник."""
    d = dt.date.today().isoweekday()
    return d if d <= 6 else 1


def build_day(group: str, week: int | None = None, day: int | None = None,
              shift: int = 0) -> tuple[str, types.InlineKeyboardMarkup, dict, int]:
    """Готовит текст и клавиатуру карточки дня."""
    sched = api.fetch_schedule(group)
    cur_week = api.week_of_cycle(dt.date.today(), sched["semestr"], shift)
    w = cur_week if week is None else week % 4
    d = today_day() if day is None else max(1, min(6, day))
    text = render.schedule_card(group, sched, w, d, cur_week)
    kb = kbs.day_keyboard(group, sched, w, d, cur_week, WEBAPP_URL or None)
    return text, kb, sched, cur_week


def safe_edit(call: types.CallbackQuery, text: str,
              markup: types.InlineKeyboardMarkup | None) -> None:
    """
    Правит сообщение и в личке, и во вставленном через inline.
    У inline-сообщения нет message_id — только inline_message_id.
    """
    try:
        if call.inline_message_id:
            bot.edit_message_text(text, inline_message_id=call.inline_message_id,
                                  reply_markup=markup, disable_web_page_preview=True)
        else:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=markup, disable_web_page_preview=True)
    except ApiTelegramException as e:
        # Нажали ту же кнопку ещё раз — Telegram ругается, но это не ошибка.
        if "message is not modified" not in str(e):
            raise


def ask_group(chat_id: int) -> None:
    bot.send_message(
        chat_id,
        "👥 <b>Какая у тебя группа?</b>\n\n"
        "Отправь название — например <code>ПИН-31</code>, <code>ЭН-24</code>, "
        "<code>МП-11</code>.\nРегистр и пробелы не важны.",
        disable_web_page_preview=True)


# ─────────────────────────── команды ───────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)

    # Диплинк t.me/бот?start=ПИН-31 — чтобы одногруппники настраивались
    # в одно нажатие по присланной ссылке.
    parts = (m.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    if payload and payload.lower() != "start":
        try:
            matches = api.resolve_group(payload.replace("_", " "), api.fetch_groups())
        except Exception:
            matches = []
        if len(matches) == 1:
            storage.set_group(m.from_user.id, matches[0], m.from_user.username)
            ctx = user_ctx(m.from_user.id)
            bot.send_message(m.chat.id, f"✅ Группа <b>{render.esc(matches[0])}</b> сохранена")

    bot.send_message(
        m.chat.id,
        render.start_text(m.from_user.first_name),
        reply_markup=kbs.start_keyboard(WEBAPP_URL or None, BOT_USERNAME,
                                        ctx["group"]),
        disable_web_page_preview=True)
    if ctx["group"]:
        send_day(m.chat.id, ctx["group"], shift=ctx["shift"])
    else:
        ask_group(m.chat.id)


@bot.message_handler(commands=["help"])
def cmd_help(m: types.Message) -> None:
    bot.send_message(m.chat.id, render.help_text(BOT_USERNAME),
                     disable_web_page_preview=True)


@bot.message_handler(commands=["today", "segodnya"])
def cmd_today(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)
    if not ctx["group"]:
        return ask_group(m.chat.id)
    send_day(m.chat.id, ctx["group"], shift=ctx["shift"])


@bot.message_handler(commands=["tomorrow"])
def cmd_tomorrow(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)
    if not ctx["group"]:
        return ask_group(m.chat.id)
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    sched = api.fetch_schedule(ctx["group"])
    week = api.week_of_cycle(tomorrow, sched["semestr"], ctx["shift"])
    day = tomorrow.isoweekday()
    if day > 6:                     # воскресенье — показываем понедельник
        day, week = 1, (week + 1) % 4
    send_day(m.chat.id, ctx["group"], week=week, day=day, shift=ctx["shift"])


@bot.message_handler(commands=["week"])
def cmd_week(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)
    if not ctx["group"]:
        return ask_group(m.chat.id)
    sched = api.fetch_schedule(ctx["group"])
    cur = api.week_of_cycle(dt.date.today(), sched["semestr"], ctx["shift"])
    bot.send_message(m.chat.id,
                     render.week_card(ctx["group"], sched, cur, cur),
                     reply_markup=kbs.week_keyboard(ctx["group"], cur, WEBAPP_URL or None),
                     disable_web_page_preview=True)


@bot.message_handler(commands=["group"])
def cmd_group(m: types.Message) -> None:
    ask_group(m.chat.id)


@bot.message_handler(commands=["shift"])
def cmd_shift(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.row(*[types.InlineKeyboardButton(
        ("• " if ctx["shift"] == s else "") + (f"+{s}" if s else "0"),
        callback_data=kbs.cb("shift", s)) for s in range(4)])
    bot.send_message(
        m.chat.id,
        "🔧 <b>Поправка недели</b>\n\n"
        "Цикл в МИЭТе четырёхнедельный. Бот считает неделю от начала семестра — "
        "если счёт разошёлся с деканатом, сдвинь на нужное число.\n\n"
        f"Сейчас: <b>{'без сдвига' if not ctx['shift'] else '+' + str(ctx['shift'])}</b>",
        reply_markup=kb)


def send_day(chat_id: int, group: str, week: int | None = None,
             day: int | None = None, shift: int = 0) -> None:
    try:
        text, kb, _, _ = build_day(group, week, day, shift)
    except Exception as e:
        log.exception("расписание не загрузилось")
        return bot.send_message(chat_id, f"⚠️ Не получилось загрузить расписание: {e}")
    bot.send_message(chat_id, text, reply_markup=kb, disable_web_page_preview=True)


# ─────────────────── свободный текст: поиск группы ───────────────────

@bot.message_handler(content_types=["text"], chat_types=["private"])
def on_text(m: types.Message) -> None:
    query = (m.text or "").strip()
    if query.startswith("/"):
        return
    try:
        groups = api.fetch_groups()
    except Exception as e:
        return bot.send_message(m.chat.id, f"⚠️ Список групп недоступен: {e}")

    matches = api.resolve_group(query, groups)
    if not matches:
        return bot.send_message(
            m.chat.id,
            f"🔍 Не нашёл группу «{render.esc(query)}».\n"
            "Проверь написание — например <code>ПИН-31</code>.")

    if len(matches) == 1:
        g = matches[0]
        storage.set_group(m.from_user.id, g, m.from_user.username)
        bot.send_message(m.chat.id, f"✅ Группа <b>{render.esc(g)}</b> сохранена")
        return send_day(m.chat.id, g, shift=user_ctx(m.from_user.id)["shift"])

    bot.send_message(
        m.chat.id,
        f"Нашлось {len(matches)} — выбери свою:",
        reply_markup=kbs.group_choice_keyboard(matches))


# ─────────────────────────── кнопки ───────────────────────────

@bot.callback_query_handler(func=lambda c: True)
def on_callback(call: types.CallbackQuery) -> None:
    parts = kbs.parse_cb(call.data)
    action = parts[0] if parts else ""
    uid = call.from_user.id
    shift = user_ctx(uid)["shift"]

    try:
        if action == "noop":
            return bot.answer_callback_query(call.id)

        if action == "d":                       # день конкретной недели
            week, day, group = int(parts[1]), int(parts[2]), parts[3]
            text, kb, _, _ = build_day(group, week, day, shift)
            safe_edit(call, text, kb)
            return bot.answer_callback_query(call.id)

        if action == "today":                   # вернуться на сегодня
            group = parts[1]
            text, kb, _, _ = build_day(group, None, None, shift)
            safe_edit(call, text, kb)
            return bot.answer_callback_query(call.id, "Сегодня")

        if action == "w":                       # свод на неделю
            week, group = int(parts[1]) % 4, parts[2]
            sched = api.fetch_schedule(group)
            cur = api.week_of_cycle(dt.date.today(), sched["semestr"], shift)
            safe_edit(call, render.week_card(group, sched, week, cur),
                      kbs.week_keyboard(group, week, WEBAPP_URL or None))
            return bot.answer_callback_query(call.id)

        if action == "grp":                     # сменить группу
            target = call.message.chat.id if call.message else uid
            try:
                ask_group(target)
            except ApiTelegramException:
                # Кнопку нажали во вставленном сообщении, а бота в личке не
                # запускали — писать туда нельзя, объясняем всплывающим окном.
                return bot.answer_callback_query(
                    call.id, "Открой бота в личке, чтобы выбрать группу",
                    show_alert=True)
            return bot.answer_callback_query(call.id)

        if action == "set":                     # выбор из найденных
            group = parts[1]
            storage.set_group(uid, group, call.from_user.username)
            text, kb, _, _ = build_day(group, None, None, shift)
            safe_edit(call, text, kb)
            return bot.answer_callback_query(call.id, f"Группа {group}")

        if action == "shift":                   # поправка недели
            storage.set_shift(uid, int(parts[1]))
            bot.answer_callback_query(call.id, "Сохранено")
            ctx = user_ctx(uid)
            if ctx["group"] and call.message:
                text, kb, _, _ = build_day(ctx["group"], None, None, ctx["shift"])
                return safe_edit(call, text, kb)
            return

        bot.answer_callback_query(call.id)

    except Exception as e:
        log.exception("ошибка в кнопке %s", call.data)
        try:
            bot.answer_callback_query(call.id, f"Ошибка: {e}", show_alert=True)
        except ApiTelegramException:
            pass


# ─────────────────────── inline: бот в любом чате ───────────────────────

@bot.inline_handler(func=lambda q: True)
def on_inline(q: types.InlineQuery) -> None:
    query = (q.query or "").strip()
    ctx = user_ctx(q.from_user.id)

    try:
        groups = api.fetch_groups()
    except Exception:
        groups = []

    if query:
        candidates = api.resolve_group(query, groups)
    elif ctx["group"]:
        candidates = [ctx["group"]]
    else:
        candidates = groups[:INLINE_LIMIT]

    if not candidates:
        return bot.answer_inline_query(
            q.id, [], cache_time=5, is_personal=True,
            switch_pm_text="Выбрать группу в боте", switch_pm_parameter="start")

    # Своя группа всегда первой — за ней приходят чаще всего.
    if ctx["group"] and ctx["group"] in candidates:
        candidates.remove(ctx["group"])
        candidates.insert(0, ctx["group"])

    # На inline-запрос у бота считанные секунды, а каждый несохранённый
    # ответ miet.ru — это ещё секунда-полторы. Поэтому в сеть ходим только
    # за первыми, остальных берём из кеша или пропускаем.
    results, fetched = [], 0
    for i, group in enumerate(candidates[:INLINE_LIMIT * 2]):
        sched = api.cached_schedule(group)
        if sched is None:
            if fetched >= INLINE_FETCH:
                continue
            fetched += 1
        try:
            text, kb, sched, cur = build_day(group, None, None, ctx["shift"])
        except Exception:
            log.warning("inline: расписание %s не загрузилось", group)
            continue
        lessons = api.lessons_of(sched, cur, today_day())
        desc = (f"{len(lessons)} {render.plural(len(lessons), 'пара', 'пары', 'пар')} · "
                f"{cur + 1}-я неделя") if lessons else "Сегодня пар нет"
        results.append(types.InlineQueryResultArticle(
            id=f"day-{i}-{group}",
            title=f"📅 {group} — сегодня",
            description=desc,
            input_message_content=types.InputTextMessageContent(
                text, parse_mode="HTML", disable_web_page_preview=True),
            reply_markup=kb,
        ))
        if len(results) >= INLINE_LIMIT:
            break

    bot.answer_inline_query(q.id, results, cache_time=60, is_personal=True,
                            switch_pm_text="Настроить группу",
                            switch_pm_parameter="start")


# ─────────────────────────── запуск ───────────────────────────

def main() -> None:
    global BOT_USERNAME
    me = bot.get_me()
    BOT_USERNAME = me.username or ""
    try:
        bot.set_my_commands([
            types.BotCommand("today", "Пары на сегодня"),
            types.BotCommand("tomorrow", "Пары на завтра"),
            types.BotCommand("week", "Вся неделя"),
            types.BotCommand("group", "Сменить группу"),
            types.BotCommand("shift", "Поправка недели цикла"),
            types.BotCommand("help", "Как пользоваться"),
        ])
    except ApiTelegramException as e:
        log.warning("не удалось задать команды: %s", e)

    log.info("Бот @%s запущен", BOT_USERNAME)
    if WEBAPP_URL:
        log.info("Мини-приложение: %s", WEBAPP_URL)
    else:
        log.info("WEBAPP_URL не задан — кнопки приложения не будет")
    if not me.supports_inline_queries:
        log.warning("Inline-режим выключен — включи у @BotFather: /setinline")
    if os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY"):
        log.info("Соединение идёт через прокси — окно опроса укорочено")

    # Длинный опрос держит соединение открытым, пока Telegram молчит. Прокси
    # такие «висящие» соединения обычно рвёт секунд через тридцать, и в лог
    # сыпется полотно трейсбеков на ровном месте. Окно в 20 секунд короче
    # этого порога, так что до обрыва дело не доходит.
    bot.infinity_polling(skip_pending=True, timeout=20,
                         long_polling_timeout=20,
                         logger_level=logging.WARNING)


if __name__ == "__main__":
    main()
