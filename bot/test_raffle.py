# -*- coding: utf-8 -*-
"""
Проверки розыгрыша: закрепление по ссылке, зачёт, накрутка и видимость.

Главное здесь — две вещи, которые ломаются молча. Первая: раздел закрыт,
пока владелец не открыл его всем, и закрытый он обязан быть закрыт и в
API, а не только в интерфейсе — иначе спрятанная плитка ничего не
значит. Вторая: очко даётся один раз и тому, кто привёл первым; сбейся
это, и таблица победителей станет выдумкой, по которой раздают призы.

    python -m bot.test_raffle
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
from urllib.parse import urlencode

sys.stdout.reconfigure(encoding="utf-8")

TOKEN = "123456:TESTTOKEN"
os.environ["BOT_TOKEN"] = TOKEN
os.environ["ADMIN_IDS"] = "777"

from . import db                                                   # noqa: E402
_dir = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _dir
db.reset_for_tests(os.path.join(_dir, "test-raffle.db"))

from . import analytics, api, appconf, raffle, storage             # noqa: E402

ok = fail = 0


def check(name: str, cond, detail: object = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name}  {detail}")


def init_data(uid: int, name: str, username: str) -> str:
    user = {"id": uid, "first_name": name, "username": username}
    pairs = {"auth_date": str(int(time.time())), "query_id": "AAA",
             "user": json.dumps(user, ensure_ascii=False, separators=(",", ":"))}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)


def person(uid: int, username: str = "", photo: bool = True,
           premium: bool = False) -> dict:
    """Пришедший так, как его видит бот в /start."""
    return {"id": uid, "username": username, "photo": photo, "premium": premium}


raffle.set_bot_username("mietapp_bot")

ADMIN = init_data(777, "Владелец", "byrouk")
ALICE = init_data(10, "Алёна", "alena")
BOB = init_data(20, "Борис", "boris")

# Профили заводим так же, как это делает живой бот.
for uid, name, nick in ((777, "Владелец", "byrouk"), (10, "Алёна", "alena"),
                        (20, "Борис", "boris")):
    analytics.touch({"id": uid, "first_name": name, "username": nick}, source="bot")

print("1. Раздел закрыт, пока его не открыли")
check("по умолчанию выключен", appconf.get("raffle_on") is False)
s, _ = api.handle("GET", "/api/raffle", {}, {}, ALICE)
check("постороннему 404, а не 403", s == 404, s)
s, _ = api.handle("GET", "/api/raffle/board", {}, {}, ALICE)
check("таблица закрыта тоже", s == 404, s)
s, me = api.handle("GET", "/api/me", {}, {}, ALICE)
check("и в профиле раздела нет", me["raffle"] is False, me.get("raffle"))
s, r = api.handle("GET", "/api/raffle", {}, {}, ADMIN)
check("а админ видит закрытый раздел", s == 200, s)
s, me = api.handle("GET", "/api/me", {}, {}, ADMIN)
check("и знает, что людям он не показан",
      me["raffle"] and not me["raffle_open"], me)

print("\n2. Ссылка у каждого своя и не меняется")
code = raffle.code_of(10)
check("код выдан", bool(code) and code == raffle.code_of(10), code)
check("чужой код другой", raffle.code_of(20) != code)
check("по коду находится хозяин", raffle.owner_of(code) == 10)
link = raffle.link_for(10)
check("ссылка собрана", link == f"https://t.me/mietapp_bot?start=r_{code}", link)
check("код разбирается обратно", raffle.parse_code(f"r_{code}") == code)
check("чужой параметр не путается с кодом",
      raffle.parse_code("0J_QmNCdLTMx") == "", raffle.parse_code("0J_QmNCdLTMx"))

print("\n3. Переход считается только после выбора группы")
got = raffle.attach(person(101, "vasya"), code)
check("закрепили", got["ok"] and got["state"] == "waiting", got)
check("пока в ожидании", raffle.counts_of(10)["waiting"] == 1, raffle.counts_of(10))
check("очка ещё нет", raffle.counts_of(10)["counted"] == 0)
storage.set_group(101, "ПИН-31")
check("после группы засчитано", raffle.counts_of(10)["counted"] == 1,
      raffle.counts_of(10))
check("и из ожидания ушло", raffle.counts_of(10)["waiting"] == 0)
storage.set_group(101, "ЭН-24")
check("смена группы второго очка не даёт",
      raffle.counts_of(10)["counted"] == 1, raffle.counts_of(10))

print("\n4. Человек закрепляется за первым и навсегда")
again = raffle.attach(person(101, "vasya"), raffle.code_of(20))
check("вторая ссылка не перетягивает", not again["ok"], again)
check("очко осталось у первого", raffle.counts_of(20)["counted"] == 0,
      raffle.counts_of(20))
check("и у первого не пропало", raffle.counts_of(10)["counted"] == 1)

print("\n5. Себя пригласить нельзя")
mine = raffle.attach(person(10, "alena"), code)
check("своя же ссылка отклонена", not mine["ok"], mine)

print("\n6. Кто уже пользовался приложением, очка не приносит")
analytics.touch({"id": 102, "first_name": "Старожил", "username": "old"},
                source="app")
db.conn().execute(
    "UPDATE users SET first_seen = datetime('now', '-40 days') WHERE user_id=102")
old = raffle.attach(person(102, "old"), code)
check("старый пользователь не в зачёт", not old["ok"], old)
storage.set_group(102, "ПИН-31")
check("и группа его не оживляет", raffle.counts_of(10)["counted"] == 1,
      raffle.counts_of(10))

print("\n7. Пустой аккаунт не проходит, живой — проходит")
empty = raffle.attach(person(103, "", photo=False, premium=False), code)
check("без ника, фото и премиума — отказ", not empty["ok"], empty)
storage.set_group(103, "ПИН-31")
check("и выбор группы его не спасает", raffle.counts_of(10)["counted"] == 1)
only_photo = raffle.attach(person(104, "", photo=True), code)
check("одной аватарки достаточно", only_photo["ok"], only_photo)
only_prem = raffle.attach(person(105, "", photo=False, premium=True), code)
check("премиума тоже", only_prem["ok"], only_prem)
no_nick = [i for i in raffle.invites_of(10) if i["user_id"] == 105]
check("но без ника метка стоит",
      no_nick and "noname" in no_nick[0]["flags"], no_nick)

print("\n8. Подозрительное помечается, а не отменяется молча")
fresh = raffle.attach(person(raffle.FRESH_ID + 7, "novichok"), code)
check("свежий аккаунт в зачёт идёт", fresh["ok"], fresh)
marks = [i for i in raffle.invites_of(10) if "fresh" in i["flags"]]
check("но помечен", len(marks) == 1, marks)
sus = raffle.overview()["suspicious"]
check("и виден владельцу в спорных", any(
    i["user_id"] == raffle.FRESH_ID + 7 for i in sus), len(sus))

print("\n9. Спорное решает человек")
who = raffle.FRESH_ID + 7
storage.set_group(who, "ПИН-31")
before = raffle.counts_of(10)["counted"]
raffle.decide(who, "no")
check("снятое уходит из счёта", raffle.counts_of(10)["counted"] == before - 1,
      raffle.counts_of(10))
raffle.decide(who, "ok")
check("возвращённое считается снова", raffle.counts_of(10)["counted"] == before)
check("и метка перестаёт быть спорной", all(
    i["user_id"] != who for i in raffle.overview()["suspicious"]))

print("\n10. Таблица и места")
for i, uid in enumerate((201, 202, 203)):
    raffle.attach(person(uid, f"drug{i}"), raffle.code_of(20))
    storage.set_group(uid, "ЭН-24")
board = raffle.board(20)
check("впереди тот, у кого больше", board["top"][0]["user_id"] == 20, board["top"])
check("счёт верный", board["top"][0]["count"] == 3, board["top"][0])
check("своё место посчитано", board["me"]["place"] == 1, board["me"])
check("участников двое", board["players"] == 2, board["players"])
check("метки посторонним не видны", "marked" not in board["top"][0],
      board["top"][0])
check("а с правом — видны",
      "marked" in raffle.board(20, with_marks=True)["top"][0])

print("\n11. Равный счёт делит место")
# Двое приглашающих с одинаковым счётом обязаны получить одно место, а
# следующий за ними — пропустить его. Иначе порядок решала бы сортировка,
# то есть случай, и таблица переставлялась бы сама собой.
for host, guest in ((501, 601), (502, 602)):
    analytics.touch({"id": host, "first_name": f"Хост {host}",
                     "username": f"host{host}"}, source="bot")
    raffle.attach(person(guest, f"g{guest}"), raffle.code_of(host))
    storage.set_group(guest, "ПИН-31")
tie = raffle.board(0, limit=100)
places = {p["user_id"]: p["place"] for p in tie["top"]}
counts = {p["user_id"]: p["count"] for p in tie["top"]}
check("одинаковый счёт — одно место", places.get(501) == places.get(502), places)
check("счёт у них и правда равный", counts.get(501) == counts.get(502) == 1, counts)
below = [p["place"] for p in tie["top"] if p["count"] < counts.get(501, 0)]
check("следующий за ними место пропускает",
      not below or min(below) > places.get(501, 0) + 1, (places.get(501), below))

print("\n12. Условия розыгрыша")
conf = raffle.set_conf({"title": "Розыгрыш звёзд", "ends": "2026-10-01",
                        "prizes": [{"text": "200 Stars"}, {"text": "100 Stars"}]})
check("название сохранено", conf["title"] == "Розыгрыш звёзд", conf)
check("места расставлены по порядку",
      [p["place"] for p in conf["prizes"]] == [1, 2], conf["prizes"])
check("срок понят", raffle.days_left("2026-10-01") is not None)
check("без срока — ничего не выдумываем", raffle.days_left("") is None)
try:
    raffle.set_conf({"ends": "первое октября"})
    check("кривая дата отклонена", False)
except raffle.Refused:
    check("кривая дата отклонена", True)
check("победителей столько, сколько призов", len(raffle.winners()) == 2,
      raffle.winners())

print("\n13. Права на разбор спорного")
s, _ = api.handle("GET", "/api/admin/raffle", {}, {}, ALICE)
check("без права в админку розыгрыша нельзя", s == 403, s)
s, d = api.handle("GET", "/api/admin/raffle", {}, {}, ADMIN)
check("владельцу — вся сводка", s == 200 and "suspicious" in d, s)
s, _ = api.handle("POST", "/api/admin/raffle", {},
                  {"action": "decide", "user_id": 201, "verdict": "нет"}, ADMIN)
check("неизвестное решение отклоняется", s == 400, s)

print("\n14. Открытие раздела всем")
s, r = api.handle("POST", "/api/admin/raffle", {},
                  {"action": "open", "on": True}, ADMIN)
check("флаг поднялся", s == 200 and r["on"] is True, r)
s, state = api.handle("GET", "/api/raffle", {}, {}, ALICE)
check("теперь виден всем", s == 200, s)
check("своя ссылка на месте", state["link"].endswith(raffle.code_of(10)), state)
check("счёт на месте", state["counted"] == raffle.counts_of(10)["counted"], state)
check("неделя — семь дней", len(state["week"]) == 7, len(state["week"]))
check("чужие метки не отдаются", state["rejected"] == 0, state)
s, b = api.handle("GET", "/api/raffle/board", {}, {}, ALICE)
check("таблица открыта", s == 200 and b["top"], s)
check("и меток в ней нет", "marked" not in b["top"][0], b["top"][0])

print("\n15. Привязка из мини-приложения")
api.handle("POST", "/api/admin/raffle", {}, {"action": "open", "on": True}, ADMIN)
s, r = api.handle("POST", "/api/raffle/join", {},
                  {"code": raffle.code_of(20), "username": "izapp",
                   "photo": True}, BOB)
check("своя же ссылка не срабатывает", s == 200 and not r["attached"], r)
NEW = init_data(401, "Новичок", "new401")
s, r = api.handle("POST", "/api/raffle/join", {},
                  {"code": raffle.code_of(20), "username": "new401",
                   "photo": True}, NEW)
check("чужая — закрепляет", s == 200 and r["attached"], r)
from_app = [i for i in raffle.invites_of(20) if i["user_id"] == 401]
check("источник записан", from_app and from_app[0]["source"] == "app", from_app)
s, _ = api.handle("POST", "/api/raffle/join", {}, {"code": "ZZZZZZ"}, NEW)
check("несуществующий код не ломает ответ", s == 200, s)

print("\n16. Заблокированному розыгрыш закрыт")
analytics.set_blocked(10, True)
s, _ = api.handle("GET", "/api/raffle", {}, {}, ALICE)
check("заблокированный не участвует", s == 403, s)
analytics.set_blocked(10, False)

print("\n17. Пьедестал не теряет людей при равном счёте")
# Пятеро с одним очком получают одно место на всех. Если верх списка
# резать по месту, а не по порядку, четвёртый и пятый исчезнут с экрана
# вовсе: у них тот же номер, что у стоящих на пьедестале.
for host, guest in ((503, 603), (504, 604)):
    analytics.touch({"id": host, "first_name": f"Хост {host}",
                     "username": f"host{host}"}, source="bot")
    raffle.attach(person(guest, f"g{guest}"), raffle.code_of(host))
    storage.set_group(guest, "ПИН-31")
wide = raffle.board(0, limit=100)
same = [p for p in wide["top"] if p["place"] == wide["top"][-1]["place"]]
check("одинаковых мест бывает больше трёх", len(same) >= 3, len(same))
check("и в таблице они все", len(wide["top"]) >= len(same), len(wide["top"]))

print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
