# -*- coding: utf-8 -*-
"""
Проверки серверной части: подпись Telegram, учёт событий, статистика,
роли и блокировки.

Маршруты вызываются через api.handle() напрямую, без сокета: так проверка
не зависит ни от свободного порта, ни от системного прокси, который на
машине автора заворачивает localhost и отвечает 502.

    python -m bot.test_admin
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

# База своя на каждый прогон — тест не должен трогать живую статистику.
from . import db                                                   # noqa: E402
db.reset_for_tests(os.path.join(tempfile.mkdtemp(), "test-admin.db"))

from . import analytics, api, storage                              # noqa: E402

ok = fail = 0


def check(name: str, cond: bool, detail: object = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {name}")
    else:
        fail += 1
        print(f"  ✗ {name}  {detail}")


def init_data(uid: int, name: str, username: str, premium: bool = False,
              token: str = TOKEN, auth_date: int | None = None) -> str:
    """Собирает подписанную initData так же, как это делает Telegram."""
    user = {"id": uid, "first_name": name, "username": username}
    if premium:
        user["is_premium"] = True
    pairs = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAA",
        "user": json.dumps(user, ensure_ascii=False, separators=(",", ":")),
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)


ADMIN = init_data(777, "Админ", "byrouk")
USER = init_data(42, "Студент", "student")

print("1. Подпись Telegram — единственный пропуск")
s, _ = api.handle("GET", "/api/me", {}, {}, "user=%7B%22id%22%3A1%7D&hash=деадбиф")
check("подделанная initData отвергнута", s == 401, s)
s, _ = api.handle("GET", "/api/me", {}, {}, "")
check("пустая initData отвергнута", s == 401, s)
s, _ = api.handle("GET", "/api/me", {}, {}, init_data(1, "Чужой", "x", token="999:OTHER"))
check("подпись чужим токеном не проходит", s == 401, s)
s, _ = api.handle("GET", "/api/me", {}, {},
                  init_data(1, "Старый", "x", auth_date=int(time.time()) - 90000))
check("просроченная initData отвергнута", s == 401, s)
s, _ = api.handle("GET", "/api/health", {}, {}, "")
check("проверка живости не требует подписи", s == 200, s)

print("\n2. Кто админ, решает ADMIN_IDS, а не клиент")
s, me = api.handle("GET", "/api/me", {}, {}, ADMIN)
check("владелец узнан", s == 200 and me["is_admin"] and me["role"] == "admin", me)
check("владелец помечен корневым", analytics.identity(777, api.admin_ids())["root"])
s, me2 = api.handle("GET", "/api/me", {}, {}, USER)
check("посторонний не админ", not me2["is_admin"] and not me2["can_stats"], me2)
s, _ = api.handle("GET", "/api/admin/stats", {}, {}, USER)
check("постороннего в статистику не пускают", s == 403, s)
s, _ = api.handle("GET", "/api/admin/users", {}, {}, USER)
check("и в список людей тоже", s == 403, s)

print("\n3. Учёт событий")
api.handle("POST", "/api/track", {}, {"group": "ПИН-31", "events": [
    {"kind": "open"},
    {"kind": "tab", "name": "schedule"},
    {"kind": "tab", "name": "schedule"},
    {"kind": "tab", "name": "clubs"},
    {"kind": "screen", "name": "club"},
]}, USER)
api.handle("POST", "/api/track", {}, {"events": [{"kind": "open"}]}, ADMIN)
s, st = api.handle("GET", "/api/admin/stats", {}, {}, ADMIN)
check("статистика отдалась", s == 200, s)
check("людей двое", st["totals"]["users"] == 2, st["totals"])
check("активны сегодня оба", st["totals"]["today"] == 2, st["totals"])
check("подписка на расписание одна", st["totals"]["subs"] == 1, st["totals"])
check("оба пришли из приложения", st["totals"]["app"] == 2, st["totals"])
tabs = {t["name"]: t["count"] for t in st["tabs"]}
check("вкладки посчитаны", tabs == {"schedule": 2, "clubs": 1}, tabs)
check("доли посчитаны от всех открытий",
      {t["name"]: t["share"] for t in st["tabs"]}["schedule"] == 67, st["tabs"])
check("ряд заходов достроен до 14 дней", len(st["opens"]) == 14, len(st["opens"]))
check("сегодняшний день — последний в ряду", st["opens"][-1]["count"] == 2,
      st["opens"][-1])
check("пустые дни в ряду нулевые",
      all(p["count"] == 0 for p in st["opens"][:-1]), st["opens"][:3])
check("группа попала в популярные", st["groups"][0]["name"] == "ПИН-31", st["groups"])

print("\n4. В базу не попадает лишнее")
api.handle("POST", "/api/track", {}, {"events": [
    {"kind": "evil", "name": "чужое"},
    {"kind": "search", "name": "что человек искал"},
    "мусор",
]}, USER)
s, st = api.handle("GET", "/api/admin/stats", {}, {}, ADMIN)
check("неизвестный вид события отброшен",
      all(x["name"] not in ("чужое", "что человек искал")
          for x in st["screens"] + st["tabs"]), st["screens"])
s, _ = api.handle("POST", "/api/track", {}, {"events": "не список"}, USER)
check("кривое тело не роняет приём", s == 200, s)
api.handle("POST", "/api/track", {}, {"events": [
    {"kind": "screen", "name": "x"} for _ in range(80)]}, USER)
s, card = api.handle("GET", "/api/admin/users/42", {}, {}, ADMIN)
check("пачка событий ограничена сверху", card["counts"]["screens"] <= 51,
      card["counts"])

print("\n5. Группа общая у бота и приложения")
check("группа из приложения дошла до базы бота",
      storage.get_user(42)["group"] == "ПИН-31")
s, me3 = api.handle("GET", "/api/me", {}, {}, USER)
check("сервер отдаёт её обратно", me3["group"] == "ПИН-31", me3)

print("\n6. Список людей")
s, page = api.handle("GET", "/api/admin/users", {}, {}, ADMIN)
check("список отдался", s == 200 and page["total"] == 2, page)
# Оба появились в одну секунду, а CURRENT_TIMESTAMP секундой и меряет —
# разводим их явно, иначе проверялся бы не порядок, а случайность.
db.conn().execute("UPDATE users SET last_seen='2026-01-01 00:00:00' WHERE user_id=777")
db.conn().commit()
s, page = api.handle("GET", "/api/admin/users", {}, {}, ADMIN)
check("кто был недавно — сверху", [u["id"] for u in page["users"]] == [42, 777],
      [u["id"] for u in page["users"]])
s, page = api.handle("GET", "/api/admin/users", {"q": ["student"]}, {}, ADMIN)
check("поиск по нику", page["total"] == 1, page)
s, page = api.handle("GET", "/api/admin/users", {"q": ["ПИН"]}, {}, ADMIN)
check("поиск по группе", page["total"] == 1, page)
s, page = api.handle("GET", "/api/admin/users", {"q": ["777"]}, {}, ADMIN)
check("поиск по числовому id", page["total"] == 1, page)
s, page = api.handle("GET", "/api/admin/users", {"limit": ["1"]}, {}, ADMIN)
check("страница режется по limit", len(page["users"]) == 1 and page["total"] == 2, page)

print("\n7. Карточка человека")
s, card = api.handle("GET", "/api/admin/users/42", {}, {}, ADMIN)
check("карточка отдалась", s == 200 and card["id"] == 42, s)
check("имя и ник на месте",
      card["first_name"] == "Студент" and card["username"] == "student", card)
check("заходы посчитаны", card["counts"]["opens"] == 1, card["counts"])
check("вкладки посчитаны", card["counts"]["tabs"] == 3, card["counts"])
check("активность за 30 дней", len(card["activity"]) == 30, len(card["activity"]))
check("лента действий не пуста", card["feed"], card["feed"][:2])
check("в карточке есть права", card["access"]["role"] == "none", card["access"])
s, _ = api.handle("GET", "/api/admin/users/999999", {}, {}, ADMIN)
check("несуществующий — 404", s == 404, s)

print("\n8. Роли и права")
s, r = api.handle("POST", "/api/admin/users/42/role", {},
                  {"role": "moderator", "perms": ["stats", "право-из-воздуха"],
                   "sections": ["sc0"]}, ADMIN)
check("роль выдана", s == 200 and r["access"]["role"] == "moderator", r)
check("выдуманное право отброшено", r["access"]["perms"] == ["stats"],
      r["access"]["perms"])
check("доступ к разделу сохранён", r["access"]["sections"] == ["sc0"], r["access"])
s, mod = api.handle("GET", "/api/me", {}, {}, USER)
check("модератор видит статистику", mod["can_stats"] and not mod["is_admin"], mod)
s, _ = api.handle("GET", "/api/admin/stats", {}, {}, USER)
check("и его туда пускают", s == 200, s)
s, _ = api.handle("POST", "/api/admin/users/1/role", {}, {"role": "admin"}, USER)
check("роли раздаёт только полный админ", s == 403, s)
s, _ = api.handle("POST", "/api/admin/users/1/block", {}, {"blocked": True}, USER)
check("без права блокировать — нельзя", s == 403, s)
s, _ = api.handle("POST", "/api/admin/users/777/role", {}, {"role": "none"}, ADMIN)
check("владельца из ADMIN_IDS не разжаловать", s == 403, s)
s, _ = api.handle("POST", "/api/admin/users/777/block", {}, {"blocked": True}, ADMIN)
check("и не заблокировать", s == 403, s)
s, _ = api.handle("POST", "/api/admin/users/42/role", {}, {"role": "царь"}, ADMIN)
check("неизвестная роль отвергнута", s == 400, s)
api.handle("POST", "/api/admin/users/42/role", {},
           {"role": "moderator", "perms": ["stats", "users_block"],
            "sections": []}, ADMIN)
s, _ = api.handle("POST", "/api/admin/users/777/block", {}, {"blocked": True}, USER)
check("модератор с правом всё равно не тронет владельца", s == 403, s)

print("\n9. Блокировка")
api.handle("POST", "/api/admin/users/42/block", {}, {"blocked": True}, ADMIN)
check("флаг проставлен", analytics.is_blocked(42))
s, _ = api.handle("POST", "/api/track", {}, {"events": [{"kind": "open"}]}, USER)
check("заблокированному события не пишем", s == 403, s)
s, st = api.handle("GET", "/api/admin/stats", {}, {}, ADMIN)
check("заход и не записался", st["opens"][-1]["count"] == 2, st["opens"][-1])
check("заблокированные посчитаны", st["totals"]["blocked"] == 1, st["totals"])
s, me4 = api.handle("GET", "/api/me", {}, {}, USER)
check("сам человек об этом узнаёт", me4["blocked"] is True, me4)
check("блокировка отбирает права модератора", not me4["can_stats"], me4)
s, _ = api.handle("GET", "/api/admin/stats", {}, {}, USER)
check("и закрывает саму админку", s == 403, s)
api.handle("POST", "/api/admin/users/42/block", {}, {"blocked": False}, ADMIN)
check("разблокировка снимает запрет", not analytics.is_blocked(42))
s, me5 = api.handle("GET", "/api/me", {}, {}, USER)
check("права вернулись те же", me5["can_stats"] and me5["role"] == "moderator", me5)
s, card = api.handle("GET", "/api/admin/users/42", {}, {}, ADMIN)
check("выданное видно даже у заблокированного",
      "stats" in card["access"]["granted"], card["access"])

print("\n10. Учёт обращений к боту")
me_bot = {"id": 99, "first_name": "Ботовод", "username": "botuser"}
analytics.note_bot(me_bot, "/today")
analytics.note_bot(me_bot, "/today")
s, card = api.handle("GET", "/api/admin/users/99", {}, {}, ADMIN)
check("человек из бота попал в базу", card["in_bot"] and not card["in_app"], card)
check("оба обращения записаны", card["counts"]["commands"] == 2, card["counts"])
analytics.note_bot(me_bot, "inline", throttle=60)
analytics.note_bot(me_bot, "inline", throttle=60)
analytics.note_bot(me_bot, "inline", throttle=60)
s, card = api.handle("GET", "/api/admin/users/99", {}, {}, ADMIN)
check("частые inline-запросы схлопнуты в один",
      card["counts"]["commands"] == 3, card["counts"])

print("\n11. Профиль обновляется, а не затирается")
analytics.touch({"id": 99, "first_name": "Ботовод", "username": "новый_ник"},
                source="app")
s, card = api.handle("GET", "/api/admin/users/99", {}, {}, ADMIN)
check("ник обновился", card["username"] == "новый_ник", card)
check("оба источника отмечены", card["in_bot"] and card["in_app"], card)
analytics.touch({"id": 99, "first_name": "", "username": ""}, source="bot")
s, card = api.handle("GET", "/api/admin/users/99", {}, {}, ADMIN)
check("пустое имя не затёрло прежнее", card["first_name"] == "Ботовод", card)

print("\n12. Неизвестные маршруты")
for path in ("/api/нет-такого", "/api/admin/", "/api/admin/users/abc"):
    s, _ = api.handle("GET", path, {}, {}, ADMIN)
    check(f"«{path}» — 404", s == 404, s)
s, _ = api.handle("POST", "/api/admin/stats", {}, {}, ADMIN)
check("статистика не принимает POST", s == 404, s)

print("\n13. Параллельные запросы не встают в очередь")
import threading                                                   # noqa: E402

# Тот самый случай, из-за которого лента «иногда не грузилась»: сервер
# заводит поток на каждый запрос, и раньше каждый поток открывал своё
# соединение с прогоном всей схемы — DDL под эксклюзивной блокировкой.
# Соседние запросы упирались в busy_timeout и отваливались через десять
# секунд. Здесь чтение и запись идут вперемешку из восьми потоков.
results, errors = [], []


def hammer(n):
    try:
        for i in range(6):
            api.handle("POST", "/api/track", {},
                       {"events": [{"kind": "tab", "name": "schedule"}]}, USER)
            code, _ = api.handle("GET", "/api/admin/stats", {}, {}, ADMIN)
            results.append(code)
            code, _ = api.handle("GET", "/api/admin/users", {}, {}, ADMIN)
            results.append(code)
    except Exception as e:                       # noqa: BLE001
        errors.append(repr(e))


started = time.time()
threads = [threading.Thread(target=hammer, args=(i,)) for i in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join(timeout=60)
spent = time.time() - started

check("ни один поток не упал", not errors, errors[:2])
check("все потоки завершились", not any(t.is_alive() for t in threads))
check("все ответы успешны", results and set(results) == {200}, set(results))
check("96 запросов уложились в 15 секунд", spent < 15, round(spent, 1))
print(f"    96 запросов из 8 потоков за {spent:.1f} с")


print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
