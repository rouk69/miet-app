# -*- coding: utf-8 -*-
"""
Интеграционные проверки бота: настоящие обработчики прогоняются
синтетическими апдейтами, вместо Telegram — заглушка, которая запоминает
вызовы. Ни одного сетевого запроса: расписание подменено фикстурой.

    python -m bot.test_flows
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("BOT_TOKEN", "0:TEST")
os.environ.setdefault("WEBAPP_URL", "https://example.github.io/miet-app")

# Своя база на каждый прогон — чтобы тест не трогал живые настройки людей.
from . import storage                                              # noqa: E402
storage.DB_PATH = os.path.join(tempfile.mkdtemp(), "test-users.db")

from . import keyboards as kbs                                     # noqa: E402
from . import main as B                                            # noqa: E402
from . import rich as rich_mod                                     # noqa: E402
from . import schedule_api as api                                  # noqa: E402
from telebot import types                                          # noqa: E402
from telebot.apihelper import ApiTelegramException                 # noqa: E402

ok = fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name}  {detail}")


# ─────────────────────── фикстура расписания ───────────────────────

KIND_CLS = {"Лекция": "lek", "Практика": "pr", "Лабораторная": "lab"}


def _lesson(day, week, pair, frm, to, subj, kind, emoji, teacher, room):
    return {"day": day, "week": week, "pair": pair, "from": frm, "to": to,
            "subject": subj, "kind": kind, "kindCls": KIND_CLS.get(kind, "oth"),
            "emoji": emoji, "flags": [], "teacher": teacher, "room": room}


FIXTURE = {
    "semestr": "Осенний семестр 2026/2027",
    "times": [{"code": i, "label": f"{i} пара", "from": "09:00", "to": "10:20"}
              for i in range(1, 9)],
    "lessons": [
        _lesson(d, w, 1, "09:00", "10:20", "Базы данных", "Лекция", "📘",
                "Иванов И.И.", "1204 м")
        for d in range(1, 7) for w in range(4)
    ] + [
        _lesson(1, 0, 2, "10:30", "11:50", "Матанализ", "Практика", "✏️",
                "Петров П.П.", "3105 а"),
    ],
}

GROUPS = ["ПИН-31", "ПИН-32", "ПИН-33", "ЭН-24", "МП-11", "Аспирантура 11"]

api.fetch_schedule = lambda group, force=False: FIXTURE
api.cached_schedule = lambda group: FIXTURE
api.fetch_groups = lambda force=False: GROUPS


# ─────────────────────── заглушка Telegram ───────────────────────

class FakeTelegram:
    """Запоминает вызовы вместо обращения к api.telegram.org."""

    def __init__(self):
        self.sent, self.edited, self.answers, self.inline = [], [], [], []

    def send_message(self, chat_id, text, **kw):
        self.sent.append({"chat_id": chat_id, "text": text,
                          "markup": kw.get("reply_markup")})
        return types.Message(
            message_id=len(self.sent), from_user=None, date=0,
            chat=types.Chat(chat_id, "private"), content_type="text",
            options={}, json_string="")

    def edit_message_text(self, text, **kw):
        rm = kw.get("rich_message")
        self.edited.append({"text": text, "markup": kw.get("reply_markup"),
                            "chat_id": kw.get("chat_id"),
                            "message_id": kw.get("message_id"),
                            "inline_message_id": kw.get("inline_message_id"),
                            "rich": rm.html if rm else None})

    def send_rich_message(self, chat_id, rich_message, **kw):
        self.sent.append({"chat_id": chat_id, "text": rich_message.html,
                          "rich": rich_message.html, "markup": None})
        return types.Message(
            message_id=len(self.sent), from_user=None, date=0,
            chat=types.Chat(chat_id, "private"), content_type="text",
            options={}, json_string="")

    def answer_callback_query(self, call_id, text=None, **kw):
        self.answers.append({"id": call_id, "text": text})

    def answer_inline_query(self, query_id, results, **kw):
        self.inline.append({"id": query_id, "results": results, **kw})

    def reset(self):
        self.sent.clear(); self.edited.clear()
        self.answers.clear(); self.inline.clear()


tg = FakeTelegram()
B.bot.send_message = tg.send_message
B.bot.edit_message_text = tg.edit_message_text
B.bot.answer_callback_query = tg.answer_callback_query
B.bot.answer_inline_query = tg.answer_inline_query
B.bot.send_rich_message = tg.send_rich_message
B.bot.threaded = False           # обработчики выполняются сразу, а не в пуле
B.BOT_USERNAME = "mietapp_bot"

UID, CHAT = 777001, 777001


def msg(text: str, chat_type: str = "private", chat_id: int | None = None) -> None:
    upd = types.Update.de_json({
        "update_id": 1,
        "message": {
            "message_id": 10, "date": 0,
            "chat": {"id": chat_id or CHAT, "type": chat_type},
            "from": {"id": UID, "is_bot": False, "first_name": "Дима",
                     "username": "ddos"},
            "text": text,
            "entities": ([{"type": "bot_command", "offset": 0,
                           "length": len(text.split()[0])}]
                         if text.startswith("/") else []),
        },
    })
    B.bot.process_new_updates([upd])


def press(data: str, inline: bool = False) -> None:
    payload = {
        "id": "cb1", "from": {"id": UID, "is_bot": False, "first_name": "Дима"},
        "chat_instance": "1", "data": data,
    }
    if inline:
        payload["inline_message_id"] = "INLINE123"
    else:
        payload["message"] = {
            "message_id": 10, "date": 0,
            "chat": {"id": CHAT, "type": "private"},
            "from": {"id": 1, "is_bot": True, "first_name": "bot"},
            "text": "старое", "entities": [],
        }
    B.bot.process_new_updates([types.Update.de_json(
        {"update_id": 2, "callback_query": payload})])


def inline_query(q: str) -> None:
    B.bot.process_new_updates([types.Update.de_json({
        "update_id": 3,
        "inline_query": {
            "id": "iq1", "query": q, "offset": "",
            "from": {"id": UID, "is_bot": False, "first_name": "Дима"},
        },
    })])


def edited_body(i: int = 0) -> str:
    """Текст последней правки — из rich-разметки или обычного текста."""
    e = tg.edited[i]
    return e["rich"] or e["text"] or ""


def buttons(markup) -> list[str]:
    return [b.text for row in (markup.keyboard if markup else []) for b in row]


def callbacks(markup) -> list[str]:
    return [b.callback_data for row in (markup.keyboard if markup else [])
            for b in row if b.callback_data]


# ─────────────────────────── сценарии ───────────────────────────

print("\n1. /start без группы")
tg.reset(); msg("/start")
check("бот ответил дважды (приветствие + вопрос о группе)", len(tg.sent) == 2,
      f"сообщений: {len(tg.sent)}")
check("приветствие содержит название вуза", "МИЭТ" in tg.sent[0]["text"])
check("во втором сообщении спрашивают группу",
      "группа" in tg.sent[1]["text"].lower())
check("есть кнопка мини-приложения",
      any(b.web_app for row in tg.sent[0]["markup"].keyboard for b in row))

print("\n2. Пользователь отправляет название группы")
tg.reset(); msg("пин-31")
check("группа сохранена в базе", storage.get_user(UID)["group"] == "ПИН-31",
      str(storage.get_user(UID)))
check("подтверждение + карточка", len(tg.sent) == 2, f"сообщений: {len(tg.sent)}")
card = tg.sent[1]
check("в карточке есть предмет из фикстуры", "Базы данных" in card["text"])
check("в таблице есть выравнивание по центру", 'valign="middle"' in card["text"])
check("карточка ушла таблицей", "<table bordered" in card["text"])
check("6 кнопок дней в разметке",
      card["text"].count('type="callback_data" data="d|') >= 6)
check("есть «Сегодня»", ">Сегодня</tg-button>" in card["text"])
check("есть «Отправить в чат»", ">Отправить в чат</tg-button>" in card["text"])
check("кнопка недели неактивна", 'type="disabled"' in card["text"])
check("активный день выделен цветом", 'style="primary"' in card["text"])
check("в подтверждении есть ссылка для одногруппников",
      "t.me/mietapp_bot?start=" in tg.sent[0]["text"], tg.sent[0]["text"][:120])
check("ссылка в подтверждении раскодируется обратно в группу",
      kbs.decode_group(tg.sent[0]["text"].rsplit("start=", 1)[1].strip()) == "ПИН-31")

print("\n3. Неоднозначный и пустой ввод")
tg.reset(); msg("ПИН")
check("на «ПИН» предложен выбор", len(tg.sent) == 1 and tg.sent[0]["markup"] is not None)
check("в выборе три группы ПИН", len(buttons(tg.sent[0]["markup"])) == 3,
      str(buttons(tg.sent[0]["markup"])))
tg.reset(); msg("щщщ")
check("на мусор — «не нашёл»", "не нашёл" in tg.sent[0]["text"].lower())

print("\n4. Кнопки переключения дня")
tg.reset(); press("d|2|4|ПИН-31")
check("сообщение отредактировано", len(tg.edited) == 1)
check("правка ушла по message_id", tg.edited[0]["message_id"] == 10)
check("в тексте 3-я неделя", "3-я неделя" in edited_body(), edited_body()[:80])
check("на callback ответили", len(tg.answers) == 1)

print("\n5. Кнопки во вставленном сообщении (inline)")
tg.reset(); press("d|1|2|ПИН-31", inline=True)
check("правка ушла по inline_message_id",
      tg.edited[0]["inline_message_id"] == "INLINE123")
check("chat_id не использован", tg.edited[0]["chat_id"] is None)
check("правка ушла разметкой с кнопками",
      tg.edited[0]["rich"] and "<tg-button" in tg.edited[0]["rich"])

print("\n6. Неделя, сегодня, поправка")
tg.reset(); press("w|1|ПИН-31")
body = edited_body()
check("свод недели: все шесть дней",
      all(d in body for d in ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб")))
tg.reset(); press("today|ПИН-31")
check("«Сегодня» отредактировало сообщение", len(tg.edited) == 1)
tg.reset(); press("shift|2")
check("поправка недели сохранена", storage.get_user(UID)["shift"] == 2)
storage.set_shift(UID, 0)
tg.reset(); press("noop")
check("noop ничего не ломает", len(tg.edited) == 0 and len(tg.answers) == 1)

print("\n7. «Группа» пишет в личку, а не в общий чат")
tg.reset(); press("grp", inline=True)
check("вопрос ушёл пользователю в личку", tg.sent[0]["chat_id"] == UID,
      str(tg.sent[0]["chat_id"]))

print("\n8. Команды")
for cmd, expect in [("/today", "Базы данных"), ("/tomorrow", "Базы данных"),
                    ("/week", "неделя"), ("/help", "любом чате"),
                    ("/group", "группа")]:
    tg.reset(); msg(cmd)
    joined = " ".join(s["text"] for s in tg.sent).lower()
    check(f"{cmd} отвечает по делу", expect.lower() in joined,
          joined[:90])

print("\n9. Inline-режим")
tg.reset(); inline_query("ПИН-31")
res = tg.inline[0]["results"]
check("есть результат", len(res) >= 1)
content = res[0].input_message_content
rich_html = getattr(getattr(content, "rich_message", None), "html", None)
check("результат ушёл rich-разметкой", bool(rich_html))
check("в таблице есть расписание", "Базы данных" in rich_html)
check("кнопки внутри разметки несут группу", 'data="d|' in rich_html
      and "ПИН-31" in rich_html)
check("web_app в inline не пробрался — Telegram его там запрещает",
      'type="web_app"' not in rich_html, "web_app найден")
tg.reset(); inline_query("щщщ")
check("на мусор — пустой ответ", tg.inline[0]["results"] == [])

print("\n10. Диплинк на группу")
storage.set_group(UID, "ЭН-24")
link = kbs.share_link("mietapp_bot", "ПИН-31")
payload = link.split("start=")[1]
check(f"параметр из [A-Za-z0-9_-]: {payload}",
      all(c.isalnum() or c in "-_" for c in payload))
tg.reset(); msg(f"/start {payload}")
check("группа из ссылки применилась", storage.get_user(UID)["group"] == "ПИН-31",
      str(storage.get_user(UID)))
tg.reset(); msg("/start f0f0f0f0")
check("битый диплинк не роняет бота", len(tg.sent) >= 1)

print("\n11. Лимит длины сообщения")
from . import render                                              # noqa: E402
huge = {"semestr": "Осенний семестр 2026/2027", "times": [],
        "lessons": [_lesson(1, 0, i % 8 + 1, "09:00", "10:20",
                            "Очень длинное название предмета " * 6,
                            "Лекция", "📘", "Преподаватель И.И.", "1204 м")
                    for i in range(40)]}
big = render.schedule_card("ПИН-31", huge, 0, 1, 0)
check(f"карточка обрезана до лимита ({len(big)} символов)", len(big) <= 4096)
check("обрезано по границе блока, тег не разорван",
      big.count("<blockquote>") == big.count("</blockquote>"),
      f"{big.count('<blockquote>')} открытых, {big.count('</blockquote>')} закрытых")
check("сказано, что показано не всё", "не всё" in big)

print("\n12. Премиум-эмодзи и откат на обычные")
fancy = render.schedule_card("ПИН-31", FIXTURE, 0, 1, 0, custom=True)
plain = render.schedule_card("ПИН-31", FIXTURE, 0, 1, 0, custom=False)
check("с премиумом в разметке есть tg-emoji", "<tg-emoji emoji-id=" in fancy)
check("без премиума тега нет вовсе", "<tg-emoji" not in plain)
check("запасной эмодзи виден и без премиума", "📖" in plain and "👤" in plain)
check("каждый tg-emoji закрыт и несёт запасной внутри",
      fancy.count("<tg-emoji") == fancy.count("</tg-emoji>")
      and ">📖</tg-emoji>" in fancy)
check("структура карточки от премиума не зависит",
      plain.count("blockquote") == fancy.count("blockquote"))

B._custom_emoji["direct"] = True
calls = []


def refusing(custom):
    """Telegram отказывает в премиум-эмодзи, обычные принимает."""
    calls.append(custom)
    if custom:
        raise ApiTelegramException("sendMessage", None, {
            "error_code": 400,
            "description": "Bad Request: CUSTOM_EMOJI_INVALID"})
    return "отправлено"


res = B.with_emoji_fallback(refusing)
check("после отказа повторил обычными", calls == [True, False], str(calls))
check("результат вернулся вызывающему", res == "отправлено")
check("отказ запомнен", B._custom_emoji["direct"] is False)
calls.clear()
B.with_emoji_fallback(refusing)
check("второй раз премиум уже не пробует", calls == [False], str(calls))
B._custom_emoji["direct"] = True


def broken(custom):
    """Наша же ошибка в разметке — прятать её откатом нельзя."""
    raise ApiTelegramException("sendMessage", None, {
        "error_code": 400, "description": "Bad Request: can't parse entities"})


try:
    B.with_emoji_fallback(broken)
    check("ошибка разметки не маскируется откатом", False, "исключения не было")
except ApiTelegramException:
    check("ошибка разметки не маскируется откатом", True)
check("чужая ошибка флаг не сбрасывает", B._custom_emoji["direct"] is True)

print("\n13. Откат с rich-сообщений на обычные")
rich_html = rich_mod.day_html("ПИН-31", FIXTURE, 0, 1, 0,
                              webapp_url="https://example.org/app")
check("таблица с рамками", "<table bordered compact>" in rich_html)
check("ячейки выровнены по вертикали", 'valign="middle"' in rich_html)
check("кнопки лежат рядами", "<tg-button-row>" in rich_html)
check("у активного дня свой стиль", 'style="primary"' in rich_html)
check("номер недели некликабелен", 'type="disabled"' in rich_html)
check("кнопка приложения — web_app", 'type="web_app"' in rich_html)
check("без адреса приложения кнопки web_app нет",
      'type="web_app"' not in rich_mod.day_html("ПИН-31", FIXTURE, 0, 1, 0))
check("значения атрибутов экранированы",
      '"' not in rich_mod.esc('он сказал "да"').replace("&quot;", ""))

# сервер отказал в rich — бот обязан прислать обычную карточку
B._rich["direct"] = True


def rich_refused(chat_id, rich_message, **kw):
    raise ApiTelegramException("sendRichMessage", None, {
        "error_code": 400, "description": "Bad Request: method not found"})


B.bot.send_rich_message = rich_refused
tg.reset()
B.send_day(CHAT, "ПИН-31")
check("после отказа пришла обычная карточка", len(tg.sent) == 1,
      f"сообщений: {len(tg.sent)}")
check("это уже цитаты, а не таблица",
      "<blockquote>" in tg.sent[0]["text"] and "<table" not in tg.sent[0]["text"])
check("клавиатура вернулась под сообщение", tg.sent[0]["markup"] is not None)
check("rich больше не пробуется", B._rich["direct"] is False)
tg.reset()
B.send_day(CHAT, "ПИН-31")
check("второй раз сразу обычной", len(tg.sent) == 1
      and "<table" not in tg.sent[0]["text"])
B.bot.send_rich_message = tg.send_rich_message
B._rich["direct"] = True

print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
