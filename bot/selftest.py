# -*- coding: utf-8 -*-
"""
Проверка бота без обращения к Telegram: расписание, рендер карточки,
клавиатуры и лимиты callback_data.

    python -m bot.selftest
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("BOT_TOKEN", "0:TEST")   # main.py без токена не импортируется

from . import keyboards as kbs      # noqa: E402
from . import render                # noqa: E402
from . import rich                  # noqa: E402
from . import schedule_api as api   # noqa: E402

ok = fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name}  {detail}")


print("\n1. Разбор названий предметов")
cases = [
    ("Основы цифровой схемотехники [Лек]", "Основы цифровой схемотехники", "Лекция", []),
    ("[ФТД] [ДСТ] Быстрые алгоритмы [Лек]", "Быстрые алгоритмы", "Лекция", ["ФТД", "ДСТ"]),
    ("Базы данных [Лаб]", "Базы данных", "Лабораторная", []),
    ("Командная работа [Пр]", "Командная работа", "Практика", []),
    ("Военная подготовка", "Военная подготовка", "", []),
]
for raw, name, kind, flags in cases:
    r = api.parse_subject(raw)
    check(f"{raw[:38]:40} → {r['name'][:26]}",
          r["name"] == name and r["kind"] == kind and r["flags"] == flags,
          f"получили {r}")

print("\n2. Недели цикла")
check("понедельник недели", api.monday_of(dt.date(2026, 9, 4)) == dt.date(2026, 8, 31))
check("воскресенье → та же неделя", api.monday_of(dt.date(2026, 9, 6)) == dt.date(2026, 8, 31))
check("начало осеннего семестра",
      api.semester_start("Осенний семестр 2026/2027") == dt.date(2026, 9, 1))
check("начало весеннего семестра",
      api.semester_start("Весенний семестр 2026/2027") == dt.date(2027, 2, 9))
w = api.week_of_cycle(dt.date(2026, 9, 4), "Осенний семестр 2026/2027")
check(f"неделя цикла 4 сентября = {w + 1}-я", w == 0, f"получили {w}")
check("через 4 недели цикл повторяется",
      api.week_of_cycle(dt.date(2026, 10, 2), "Осенний семестр 2026/2027") == w)
check("сдвиг работает",
      api.week_of_cycle(dt.date(2026, 9, 4), "Осенний семестр 2026/2027", 2) == 2)

print("\n3. Живой API miet.ru")
# Сайт МИЭТ временами лежит. Раньше это роняло весь прогон, хотя проверять
# разбор, рендер и клавиатуры можно и без сети — берём последнее из кеша
# и идём дальше, честно отметив, что живого запроса не было.
offline = False
try:
    groups = api.fetch_groups()
    check(f"список групп получен ({len(groups)})", len(groups) > 300)
    check("ПИН-31 есть в списке", "ПИН-31" in groups)
    sched = api.fetch_schedule("ПИН-31")
    check(f"расписание ПИН-31 ({len(sched['lessons'])} занятий)",
          len(sched["lessons"]) > 0)
    check(f"семестр: {sched['semestr']}", bool(sched["semestr"]))
    check("8 пар в сетке времени", len(sched["times"]) == 8)
except Exception as e:
    offline = True
    print(f"  ⚠ miet.ru недоступен ({type(e).__name__}) — живые проверки пропущены")
    groups = api._cache_get("groups", 10 ** 9) or []
    sched = api._cache_get("sched_ПИН-31", 10 ** 9)
    if not groups or not sched:
        sys.exit("  и кеша нет — прогнать offline-часть не на чем")
    print(f"  … работаем на кеше: групп {len(groups)}, "
          f"занятий {len(sched['lessons'])}")

print("\n4. Поиск группы")
check("точное совпадение", api.resolve_group("ПИН-31", groups) == ["ПИН-31"])
check("регистр не важен", api.resolve_group("пин-31", groups) == ["ПИН-31"])
check("частичный поиск даёт несколько", len(api.resolve_group("ПИН-3", groups)) > 1)
check("мусор ничего не находит", api.resolve_group("щщщ", groups) == [])

print("\n5. Карточка расписания")
cur = api.week_of_cycle(dt.date.today(), sched["semestr"])
card = render.schedule_card("ПИН-31", sched, cur, 3, cur)
check("карточка не пустая", len(card) > 80)
check("есть blockquote", "<blockquote>" in card)
check("уложились в лимит Telegram (4096)", len(card) < 4096, f"длина {len(card)}")
tags = set(re.findall(r"</?([a-z-]+)", card))
allowed = {"b", "i", "u", "s", "a", "code", "pre", "blockquote",
           "tg-spoiler", "tg-emoji"}
check(f"только разрешённые теги: {sorted(tags)}", tags <= allowed,
      f"лишние: {tags - allowed}")

week_card = render.week_card("ПИН-31", sched, cur, cur)
check("свод на неделю уложился в лимит", len(week_card) < 4096, f"длина {len(week_card)}")

print("\n5a. Подгруппы в одном слоте")
# Язык и физкультура делятся на подгруппы: две записи с одним временем.
# Раньше они считались двумя парами и рисовались двумя строками подряд
# с одинаковым временем — этого быть не должно.
SPLIT = {
    "semestr": "Осенний семестр 2026/2027",
    "times": [{"code": i, "label": f"{i} пара", "from": "09:00", "to": "10:20"}
              for i in range(1, 9)],
    "lessons": [
        {"day": 1, "week": 0, "pair": 1, "from": "09:00", "to": "10:20",
         "subject": "Матанализ", "kind": "Лекция", "kindCls": "lek",
         "emoji": "📘", "flags": [], "teacher": "Иванов И.И.", "room": "1201"},
        {"day": 1, "week": 0, "pair": 2, "from": "10:30", "to": "11:50",
         "subject": "Иностранный язык", "kind": "Практика", "kindCls": "pr",
         "emoji": "✏️", "flags": [], "teacher": "Рачеева Е.В.", "room": "4305"},
        {"day": 1, "week": 0, "pair": 2, "from": "10:30", "to": "11:50",
         "subject": "Иностранный язык", "kind": "Практика", "kindCls": "pr",
         "emoji": "✏️", "flags": [], "teacher": "Раух О.Б.", "room": "4306"},
    ],
}
slots = api.slots_of(SPLIT, 0, 1)
check("три записи свелись в две пары", len(slots) == 2, f"слотов {len(slots)}")
check("подгруппы собраны в один слот", slots[1]["split"] is True)
check("у слота общее название", slots[1]["subject"] == "Иностранный язык")
check("день считается по слотам", api.day_counts(SPLIT, 0)[1] == 2,
      f"насчитали {api.day_counts(SPLIT, 0)[1]}")

split_card = render.schedule_card("П-13", SPLIT, 0, 1, 0, custom=False)
check("в подписи «2 пары», а не три", "2 пары" in split_card,
      re.search(r"\d+ пар\w*", split_card).group(0) if re.search(r"\d+ пар\w*", split_card) else "—")
check("обе аудитории подгрупп на месте",
      "4305" in split_card and "4306" in split_card)
check("название не задвоено", split_card.count("Иностранный язык") == 1,
      f"встретилось {split_card.count('Иностранный язык')} раз")

split_rich = rich.day_html("П-13", SPLIT, 0, 1, 0, custom=False, buttons=False)
check("в таблице две строки", split_rich.count("<tr>") == 2,
      f"строк {split_rich.count('<tr>')}")
check("в таблице есть время окончания", "11:50" in split_rich)

print("\n6. Клавиатуры и callback_data")
kb = kbs.day_keyboard("ПИН-31", sched, cur, 3, cur, "https://example.com")
rows = kb.keyboard
check(f"рядов кнопок: {len(rows)}", len(rows) >= 4)
check("6 кнопок дней", sum(1 for r in rows for b in r
                           if b.callback_data and b.callback_data.startswith("d|")) == 6 + 2)
buttons = [b for r in rows for b in r]
check("есть кнопка мини-приложения", any(b.web_app for b in buttons))

longest = max(groups, key=lambda g: len(g.encode()))
try:
    data = kbs.cb("d", 3, 6, longest)
    check(f"самая длинная группа влезает в callback_data "
          f"({len(data.encode())} б, «{longest}»)", True)
except ValueError as e:
    check("самая длинная группа влезает в callback_data", False, str(e))

bad = 0
for g in groups:
    try:
        kbs.cb("d", 3, 6, g)
    except ValueError:
        bad += 1
check(f"все {len(groups)} групп влезают в callback_data", bad == 0, f"не влезло: {bad}")

print("\n7. Тексты бота")
for name, text in [("start", render.start_text("Дима")),
                   ("help", render.help_text("miettimebot")),
                   ("no_group", render.no_group_text())]:
    t = set(re.findall(r"</?([a-z-]+)", text))
    check(f"{name}: теги {sorted(t)}", t <= allowed, f"лишние: {t - allowed}")
    check(f"{name}: длина {len(text)} < 4096", len(text) < 4096)

print("\n8. Импорт бота целиком")
try:
    from . import main as bot_main
    check("bot.main импортируется", True)
    check("зарегистрированы обработчики команд",
          len(bot_main.bot.message_handlers) >= 6)
    check("есть обработчик кнопок", len(bot_main.bot.callback_query_handlers) >= 1)
    check("есть inline-обработчик", len(bot_main.bot.inline_handlers) >= 1)
except Exception as e:
    check("bot.main импортируется", False, repr(e))

print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)

print("\nТак карточка выглядит в Telegram (теги убраны):\n")
plain = re.sub(r"<blockquote>", "┌ ", card)
plain = re.sub(r"</blockquote>", "\n└" + "─" * 40, plain)
plain = re.sub(r"<[^>]+>", "", plain)
print(plain)

sys.exit(1 if fail else 0)
