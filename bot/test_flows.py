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
from . import schedule_api as api                                  # noqa: E402
from telebot import types                                          # noqa: E402

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

def _lesson(day, week, pair, frm, to, subj, kind, emoji, teacher, room):
    return {"day": day, "week": week, "pair": pair, "from": frm, "to": to,
            "subject": subj, "kind": kind, "emoji": emoji, "flags": [],
            "teacher": teacher, "room": room}


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
        self.edited.append({"text": text, "markup": kw.get("reply_markup"),
                            "chat_id": kw.get("chat_id"),
                            "message_id": kw.get("message_id"),
                            "inline_message_id": kw.get("inline_message_id")})

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
check("карточка размечена blockquote", "<blockquote>" in card["text"])
check("6 кнопок дней", sum(1 for c in callbacks(card["markup"])
                           if c.startswith("d|")) >= 6)
check("есть «Сегодня»", any("Сегодня" in b for b in buttons(card["markup"])))
check("есть «Отправить в чат»",
      any("Отправить" in b for b in buttons(card["markup"])))
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
check("в тексте 3-я неделя", "3-я неделя" in tg.edited[0]["text"],
      tg.edited[0]["text"][:80])
check("на callback ответили", len(tg.answers) == 1)

print("\n5. Кнопки во вставленном сообщении (inline)")
tg.reset(); press("d|1|2|ПИН-31", inline=True)
check("правка ушла по inline_message_id",
      tg.edited[0]["inline_message_id"] == "INLINE123")
check("chat_id не использован", tg.edited[0]["chat_id"] is None)
check("клавиатура пересобрана", tg.edited[0]["markup"] is not None)

print("\n6. Неделя, сегодня, поправка")
tg.reset(); press("w|1|ПИН-31")
check("свод недели: все шесть дней",
      all(d in tg.edited[0]["text"] for d in ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб")))
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
check("у результата своя клавиатура", res[0].reply_markup is not None)
check("в тексте расписание", "Базы данных" in res[0].input_message_content.message_text)
check("кнопки несут группу",
      any("ПИН-31" in c for c in callbacks(res[0].reply_markup)))
check("web_app в inline не пробрался — Telegram его там запрещает",
      not any(b.web_app for row in res[0].reply_markup.keyboard for b in row),
      "web_app найден")
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

print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
