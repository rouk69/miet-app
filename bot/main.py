# -*- coding: utf-8 -*-
"""
Бот расписания НИУ МИЭТ.

    pip install -r requirements.txt
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
import re
import sys

import telebot
from telebot import apihelper, types
from telebot.apihelper import ApiTelegramException

from . import keyboards as kbs
from . import render
from . import rich
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

    # Первая строка сообщения у telebot — служебное «Exception traceback:»,
    # а настоящая причина лежит в самом низу полотна. Её и достаём.
    CAUSE = re.compile(r"^\s*(?:\w+\.)*(\w*(?:Error|Exception))\b[:\s](.*)$")

    def _cause(self, text: str) -> str:
        for line in reversed(text.strip().splitlines()):
            m = self.CAUSE.match(line)
            if m:
                return f"{m.group(1)}: {m.group(2).strip()}"[:110]
        return text.strip().splitlines()[0][:110]

    def filter(self, record: logging.LogRecord) -> bool:
        text = str(record.getMessage())
        if any(n in text for n in self.NOISE):
            record.msg = ("связь с Telegram оборвалась, переподключаюсь — "
                          + self._cause(text))
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

# Через VPN связь с api.telegram.org рвётся раз в несколько минут. Опрос от
# этого восстанавливается сам, а вот ответ пользователю — нет: запрос падал
# с ConnectionError, обработчик умирал, и человек не получал ничего. Здесь
# повторы включены на все вызовы Bot API, включая отправку сообщений.
apihelper.RETRY_ON_ERROR = True
apihelper.MAX_RETRIES = 5        # цикл делает MAX_RETRIES-1 попыток
apihelper.RETRY_TIMEOUT = 1

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
BOT_USERNAME = ""

INLINE_LIMIT = 4     # сколько вариантов показать в inline-подсказке
INLINE_FETCH = 2     # из них — за сколькими можно сходить в сеть

# Премиум-эмодзи Telegram отдаёт не всем: в личку их можно слать, если
# владелец бота — Premium, а во вставленные через inline сообщения — только
# если у бота куплено имя на Fragment. Заранее это не проверить, поэтому
# пробуем и запоминаем отказ: один раз получили ошибку — дальше шлём
# обычными эмодзи, не дёргая Telegram впустую.
_custom_emoji = {"direct": True, "inline": True}

# Rich-сообщения (Bot API 10.1+) дают настоящие таблицы и кнопки в тексте.
# Если сервер или клиент их не примет — молча возвращаемся к обычным
# сообщениям с цитатами: они работают везде.
_rich = {"direct": True, "inline": True}


def _custom_emoji_rejected(e: Exception) -> bool:
    """
    Только про премиум-эмодзи. Ловить здесь «can't parse entities» нельзя:
    это была бы наша же ошибка в разметке, а откат на обычные эмодзи её
    молча спрятал бы — сообщение ушло бы, а баг остался.
    """
    text = str(e).upper()
    return "CUSTOM_EMOJI" in text or "CUSTOM EMOJI" in text


def with_emoji_fallback(send, scope: str = "direct"):
    """
    Вызывает send(custom=True); если Telegram отказал именно из-за
    премиум-эмодзи — повторяет с обычными и запоминает это для scope.
    """
    if _custom_emoji.get(scope):
        try:
            return send(True)
        except ApiTelegramException as e:
            if not _custom_emoji_rejected(e):
                raise
            _custom_emoji[scope] = False
            log.warning("Telegram не принял премиум-эмодзи (%s): %s — "
                        "перехожу на обычные", scope, e)
    return send(False)


# ─────────────────────────── помощники ───────────────────────────

def user_ctx(user_id: int) -> dict:
    return storage.get_user(user_id)


def today_day() -> int:
    """1..6 для Пн..Сб; воскресенье показываем как понедельник."""
    d = dt.date.today().isoweekday()
    return d if d <= 6 else 1


def build_rich_day(group: str, week: int | None = None, day: int | None = None,
                   shift: int = 0, webapp: bool = True, custom: bool = True,
                   uid: int | None = None) -> tuple[str, dict, int]:
    """Та же карточка дня, но разметкой Rich HTML — с таблицей и кнопками."""
    sched = api.fetch_schedule(group)
    if uid is not None:
        shift = storage.shift_for(uid, sched["semestr"])
    cur_week = api.week_of_cycle(dt.date.today(), sched["semestr"], shift)
    w = cur_week if week is None else week % 4
    d = today_day() if day is None else max(1, min(6, day))
    html = rich.day_html(group, sched, w, d, cur_week, custom=custom,
                         webapp_url=(WEBAPP_URL or None) if webapp else None)
    return html, sched, cur_week


def build_day(group: str, week: int | None = None, day: int | None = None,
              shift: int = 0, webapp: bool = True, custom: bool = True,
              uid: int | None = None
              ) -> tuple[str, types.InlineKeyboardMarkup, dict, int]:
    """
    Готовит текст и клавиатуру карточки дня.

    webapp=False обязателен для inline-результатов: Telegram запрещает
    кнопки web_app во вставляемых сообщениях и отклоняет весь
    answerInlineQuery целиком, а не просто игнорирует кнопку.
    """
    sched = api.fetch_schedule(group)
    if uid is not None:
        shift = storage.shift_for(uid, sched["semestr"])
    cur_week = api.week_of_cycle(dt.date.today(), sched["semestr"], shift)
    w = cur_week if week is None else week % 4
    d = today_day() if day is None else max(1, min(6, day))
    text = render.schedule_card(group, sched, w, d, cur_week, custom=custom)
    kb = kbs.day_keyboard(group, sched, w, d, cur_week,
                          (WEBAPP_URL or None) if webapp else None)
    return text, kb, sched, cur_week


def safe_edit(call: types.CallbackQuery, text: str | None,
              markup: types.InlineKeyboardMarkup | None,
              rich_html: str | None = None) -> None:
    """
    Правит сообщение и в личке, и во вставленном через inline.
    У inline-сообщения нет message_id — только inline_message_id.
    С rich_html уходит структурная разметка вместо обычного текста.
    """
    kw = {"reply_markup": markup}
    if rich_html is not None:
        kw["rich_message"] = types.InputRichMessage(html=rich_html)
    else:
        kw["disable_web_page_preview"] = True
    try:
        if call.inline_message_id:
            bot.edit_message_text(text, inline_message_id=call.inline_message_id, **kw)
        else:
            bot.edit_message_text(text, chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, **kw)
    except ApiTelegramException as e:
        # Нажали ту же кнопку ещё раз — Telegram ругается, но это не ошибка.
        if "message is not modified" not in str(e):
            raise


def group_saved_text(group: str) -> str:
    """Подтверждение выбора + ссылка, по которой настроятся одногруппники."""
    text = f"✅ Группа <b>{render.esc(group)}</b> сохранена"
    if BOT_USERNAME:
        link = kbs.share_link(BOT_USERNAME, group)
        text += ("\n\nКинь одногруппникам — у них выберется та же группа:\n"
                 f"{link}")
    return text


def edit_day(call: types.CallbackQuery, group: str, week: int | None,
             day: int | None, shift: int, scope: str,
             uid: int | None = None) -> None:
    """Перерисовывает карточку дня в уже отправленном сообщении."""
    webapp = not call.inline_message_id      # web_app в inline запрещён
    if _rich[scope]:
        try:
            return with_emoji_fallback(lambda c: safe_edit(
                call, None, None,
                rich_html=build_rich_day(group, week, day, shift,
                                         webapp=webapp, custom=c,
                                         uid=uid)[0]), scope)
        except ApiTelegramException as e:
            _rich[scope] = False
            log.warning("rich-правка недоступна (%s) — перехожу на обычные", e)
    with_emoji_fallback(
        lambda c: safe_edit(call, *build_day(group, week, day, shift,
                                             webapp=webapp, custom=c,
                                             uid=uid)[:2]),
        scope)


def show_prefixes(call: types.CallbackQuery, groups: list[str],
                  current: str | None, scope: str) -> None:
    """Перерисовывает сообщение в список направлений."""
    if _rich[scope]:
        try:
            return with_emoji_fallback(lambda c: safe_edit(
                call, None, None,
                rich_html=rich.prefixes_html(groups, current, custom=c)), scope)
        except ApiTelegramException as e:
            _rich[scope] = False
            log.warning("rich-выбор в правке недоступен (%s)", e)
    safe_edit(call, "🎓 <b>Выбор группы</b>\n\nСначала направление, потом номер.",
              kbs.prefixes_keyboard(groups, current))


def show_group_list(call: types.CallbackQuery, groups: list[str], prefix: str,
                    current: str | None, scope: str) -> None:
    """Перерисовывает сообщение в список групп выбранного направления."""
    if _rich[scope]:
        try:
            return with_emoji_fallback(lambda c: safe_edit(
                call, None, None,
                rich_html=rich.group_list_html(groups, prefix, current,
                                               custom=c)), scope)
        except ApiTelegramException as e:
            _rich[scope] = False
            log.warning("rich-список групп недоступен (%s)", e)
    safe_edit(call,
              f"🎓 <b>{render.esc(prefix)}</b>\n\nНажми свою группу — "
              f"расписание откроется сразу.",
              kbs.group_list_keyboard(groups, prefix, current))


def ask_group(chat_id: int, current: str | None = None) -> None:
    """
    Показывает выбор группы кнопками: сначала направление, потом номер.
    Ввод названием тоже работает — но искать в списке проще, чем помнить,
    как именно записана твоя группа.
    """
    try:
        groups = api.fetch_groups()
    except Exception:
        groups = []

    if groups and _rich["direct"]:
        try:
            return with_emoji_fallback(lambda c: bot.send_rich_message(
                chat_id, types.InputRichMessage(
                    html=rich.prefixes_html(groups, current, custom=c))))
        except ApiTelegramException as e:
            _rich["direct"] = False
            log.warning("rich-выбор группы недоступен (%s)", e)

    if groups:
        return bot.send_message(
            chat_id,
            "🎓 <b>Выбор группы</b>\n\nСначала направление, потом номер. "
            "Или просто пришли название — например <code>ПИН-31</code>.",
            reply_markup=kbs.prefixes_keyboard(groups, current))

    bot.send_message(
        chat_id,
        "👥 <b>Какая у тебя группа?</b>\n\n"
        "Отправь название — например <code>ПИН-31</code>.",
        disable_web_page_preview=True)


# ─────────────────────────── команды ───────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)

    # Диплинк t.me/бот?start=ПИН-31 — чтобы одногруппники настраивались
    # в одно нажатие по присланной ссылке.
    parts = (m.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    if payload:
        # Названия групп кириллические, а в start-параметр Telegram пускает
        # только [A-Za-z0-9_-] — поэтому там лежит base64url, а не сам текст.
        wanted = kbs.decode_group(payload)
        if wanted:
            try:
                matches = api.resolve_group(wanted, api.fetch_groups())
            except Exception:
                matches = []
            if len(matches) == 1:
                storage.set_group(m.from_user.id, matches[0], m.from_user.username)
                ctx = user_ctx(m.from_user.id)
                bot.send_message(
                    m.chat.id,
                    f"✅ Группа <b>{render.esc(matches[0])}</b> сохранена")

    try:
        groups = api.fetch_groups()
    except Exception:
        groups = []

    sent_rich = False
    if groups and _rich["direct"]:
        # Приветствие и выбор направления — одним сообщением: без группы
        # читать инструкцию и ждать второго сообщения незачем.
        try:
            with_emoji_fallback(lambda c: bot.send_rich_message(
                m.chat.id, types.InputRichMessage(
                    html=rich.start_html(m.from_user.first_name, groups,
                                         ctx["group"], BOT_USERNAME,
                                         WEBAPP_URL or None, custom=c))))
            sent_rich = True
        except ApiTelegramException as e:
            _rich["direct"] = False
            log.warning("rich-приветствие недоступно (%s)", e)
        except Exception as e:
            # Сеть отвалилась посреди отправки. Простое сообщение короче и
            # уходит вернее — лучше отдать его, чем оставить человека без
            # ответа на самую первую команду.
            log.warning("приветствие не отправилось (%s), пробую обычным", e)

    if not sent_rich:
        try:
            bot.send_message(
                m.chat.id,
                render.start_text(m.from_user.first_name),
                reply_markup=kbs.start_keyboard(WEBAPP_URL or None,
                                                BOT_USERNAME, ctx["group"]),
                disable_web_page_preview=True)
            if not ctx["group"]:
                ask_group(m.chat.id)
        except Exception as e:
            log.error("не удалось ответить на /start: %s", e)
            return

    if ctx["group"]:
        send_day(m.chat.id, ctx["group"], shift=ctx["shift"], uid=m.from_user.id)


@bot.message_handler(commands=["help"])
def cmd_help(m: types.Message) -> None:
    bot.send_message(m.chat.id, render.help_text(BOT_USERNAME),
                     disable_web_page_preview=True)


@bot.message_handler(commands=["today", "segodnya"])
def cmd_today(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)
    if not ctx["group"]:
        return ask_group(m.chat.id)
    send_day(m.chat.id, ctx["group"], shift=ctx["shift"], uid=m.from_user.id)


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
    send_day(m.chat.id, ctx["group"], week=week, day=day,
             shift=ctx["shift"], uid=m.from_user.id)


@bot.message_handler(commands=["week"])
def cmd_week(m: types.Message) -> None:
    ctx = user_ctx(m.from_user.id)
    if not ctx["group"]:
        return ask_group(m.chat.id)
    sched = api.fetch_schedule(ctx["group"])
    cur = api.week_of_cycle(dt.date.today(), sched["semestr"], ctx["shift"])
    if _rich["direct"]:
        try:
            return with_emoji_fallback(lambda c: bot.send_rich_message(
                m.chat.id, types.InputRichMessage(
                    html=rich.week_html(ctx["group"], sched, cur, cur, custom=c,
                                        webapp_url=WEBAPP_URL or None))))
        except ApiTelegramException as e:
            _rich["direct"] = False
            log.warning("rich-свод недоступен (%s)", e)
    with_emoji_fallback(lambda c: bot.send_message(
        m.chat.id, render.week_card(ctx["group"], sched, cur, cur, custom=c),
        reply_markup=kbs.week_keyboard(ctx["group"], cur, WEBAPP_URL or None),
        disable_web_page_preview=True))


@bot.message_handler(commands=["support", "about"])
def cmd_support(m: types.Message) -> None:
    if _rich["direct"]:
        try:
            return with_emoji_fallback(lambda c: bot.send_rich_message(
                m.chat.id, types.InputRichMessage(
                    html=rich.support_html(custom=c,
                                           webapp_url=WEBAPP_URL or None))))
        except ApiTelegramException as e:
            _rich["direct"] = False
            log.warning("rich-поддержка недоступна (%s)", e)
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton(
        "Написать автору", url=f"https://t.me/{render.OWNER}"))
    bot.send_message(m.chat.id, render.support_text(), reply_markup=kb,
                     disable_web_page_preview=True)


@bot.message_handler(commands=["group"])
def cmd_group(m: types.Message) -> None:
    ask_group(m.chat.id, user_ctx(m.from_user.id)["group"])


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
             day: int | None = None, shift: int = 0,
             uid: int | None = None) -> None:
    """Шлёт карточку дня: сначала таблицей, при отказе — цитатами."""
    if _rich["direct"]:
        try:
            return with_emoji_fallback(lambda c: bot.send_rich_message(
                chat_id,
                types.InputRichMessage(
                    html=build_rich_day(group, week, day, shift, custom=c,
                                       uid=uid)[0])))
        except ApiTelegramException as e:
            _rich["direct"] = False
            log.warning("rich-сообщения недоступны (%s) — перехожу на обычные", e)
        except Exception:
            log.exception("расписание не загрузилось")
            return bot.send_message(chat_id, "⚠️ Не получилось загрузить расписание")

    def attempt(custom: bool):
        text, kb, _, _ = build_day(group, week, day, shift, custom=custom,
                                   uid=uid)
        return bot.send_message(chat_id, text, reply_markup=kb,
                                disable_web_page_preview=True)
    try:
        with_emoji_fallback(attempt)
    except ApiTelegramException as e:
        log.warning("не отправилось: %s", e)
        bot.send_message(chat_id, f"⚠️ Telegram не принял сообщение: {e}")
    except Exception as e:
        log.exception("расписание не загрузилось")
        bot.send_message(chat_id, f"⚠️ Не получилось загрузить расписание: {e}")


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
        bot.send_message(m.chat.id, group_saved_text(g),
                         disable_web_page_preview=True)
        return send_day(m.chat.id, g, shift=user_ctx(m.from_user.id)["shift"],
                        uid=m.from_user.id)

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

        scope = "inline" if call.inline_message_id else "direct"

        if action == "d":                       # день конкретной недели
            week, day, group = int(parts[1]), int(parts[2]), parts[3]
            edit_day(call, group, week, day, shift, scope, uid)
            return bot.answer_callback_query(call.id)

        if action == "today":                   # вернуться на сегодня
            group = parts[1]
            edit_day(call, group, None, None, shift, scope, uid)
            return bot.answer_callback_query(call.id, "Сегодня")

        if action == "w":                       # свод на неделю
            week, group = int(parts[1]) % 4, parts[2]
            sched = api.fetch_schedule(group)
            cur = api.week_of_cycle(dt.date.today(), sched["semestr"], shift)
            webapp = None if call.inline_message_id else (WEBAPP_URL or None)
            if _rich[scope]:
                try:
                    with_emoji_fallback(lambda c: safe_edit(
                        call, None, None,
                        rich_html=rich.week_html(group, sched, week, cur,
                                                 custom=c, webapp_url=webapp)),
                        scope)
                    return bot.answer_callback_query(call.id)
                except ApiTelegramException as e:
                    _rich[scope] = False
                    log.warning("rich-свод в правке недоступен (%s)", e)
            with_emoji_fallback(lambda c: safe_edit(
                call, render.week_card(group, sched, week, cur, custom=c),
                kbs.week_keyboard(group, week, webapp)), scope)
            return bot.answer_callback_query(call.id)

        if action == "grp":                     # список направлений
            # Работает и во вставленной в общий чат карточке: она общая, и
            # переключить её на другую группу — обычное дело, ровно как
            # переключить день. Гонять человека в личку ради этого незачем.
            groups = api.fetch_groups()
            show_prefixes(call, groups, user_ctx(uid)["group"], scope)
            return bot.answer_callback_query(call.id)

        if action == "gp":                      # группы одного направления
            prefix = parts[1]
            groups = api.fetch_groups()
            cur = user_ctx(uid)["group"]
            show_group_list(call, groups, prefix, cur, scope)
            return bot.answer_callback_query(call.id)

        if action == "set":                     # выбор из найденных
            group = parts[1]
            storage.set_group(uid, group, call.from_user.username)
            edit_day(call, group, None, None, shift, scope, uid)
            return bot.answer_callback_query(call.id, f"Группа {group} сохранена")

        if action == "shift":                   # поправка недели
            semestr = ""
            g = user_ctx(uid)["group"]
            if g:
                try:
                    semestr = api.fetch_schedule(g)["semestr"]
                except Exception:
                    pass
            storage.set_shift(uid, int(parts[1]), semestr)
            bot.answer_callback_query(call.id, "Сохранено")
            ctx = user_ctx(uid)
            if ctx["group"] and call.message:
                return edit_day(call, ctx["group"], None, None, ctx["shift"], scope, uid)
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
            text, kb, sched, cur = build_day(group, None, None, ctx["shift"],
                                             webapp=False,
                                             custom=_custom_emoji["inline"])
        except Exception:
            log.warning("inline: расписание %s не загрузилось", group)
            continue
        lessons = api.lessons_of(sched, cur, today_day())
        desc = (f"{len(lessons)} {render.plural(len(lessons), 'пара', 'пары', 'пар')} · "
                f"{cur + 1}-я неделя") if lessons else "Сегодня пар нет"
        content, markup = None, kb
        if _rich["inline"]:
            try:
                html = build_rich_day(group, None, None, ctx["shift"],
                                      webapp=False,
                                      custom=_custom_emoji["inline"])[0]
                # Кнопки уже внутри разметки — отдельная клавиатура не нужна.
                content, markup = types.InputRichMessageContent(
                    rich_message=types.InputRichMessage(html=html)), None
            except Exception as e:
                log.warning("rich в inline не собрался (%s)", e)
        if content is None:
            content = types.InputTextMessageContent(
                text, parse_mode="HTML", disable_web_page_preview=True)
        results.append(types.InlineQueryResultArticle(
            id=f"day-{i}-{group}",
            title=f"📅 {group} — сегодня",
            description=desc,
            input_message_content=content,
            reply_markup=markup,
        ))
        if len(results) >= INLINE_LIMIT:
            break

    try:
        bot.answer_inline_query(q.id, results, cache_time=60, is_personal=True,
                                switch_pm_text="Настроить группу",
                                switch_pm_parameter="start")
    except ApiTelegramException as e:
        if not _custom_emoji_rejected(e) or not _custom_emoji["inline"]:
            raise
        # Во вставляемых сообщениях премиум-эмодзи разрешены только ботам
        # с именем, купленным на Fragment. Отказ — собираем заново простыми.
        _custom_emoji["inline"] = False
        log.warning("премиум-эмодзи в inline недоступны (нужно имя с Fragment)"
                    " — перехожу на обычные")
        return on_inline(q)


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
            types.BotCommand("support", "Связаться с автором"),
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
