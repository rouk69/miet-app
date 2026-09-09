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
s, page = api.handle("GET", "/api/admin/users", {"q": ["студент"]}, {}, ADMIN)
# SQLite приводит к нижнему регистру только латиницу, поэтому у поиска
# своя функция lower_ru: без неё «студент» не находил «Студента».
check("поиск понимает регистр кириллицы", page["total"] == 1, page)
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


print("\n14. Справочник преподавателей и аудиторий")
from . import directory                                            # noqa: E402
from . import schedule_api as sched_api                            # noqa: E402

# Расписание подменяем фикстурой: обход настоящего miet.ru в проверках
# означал бы 346 запросов к чужому сайту на каждый прогон.
FIXTURE = {
    "semestr": "Осенний семестр 2026/2027",
    "lessons": [
        {"day": 1, "week": 0, "pair": 1, "from": "09:00", "to": "10:20",
         "subject": "Базы данных", "kindCls": "lek",
         "teacher": "Иванов И.И.", "room": "3105"},
        {"day": 1, "week": 0, "pair": 2, "from": "10:30", "to": "11:50",
         "subject": "Матанализ", "kindCls": "pr",
         "teacher": "Петров П.П.", "room": "3105"},
        {"day": 2, "week": 1, "pair": 1, "from": "09:00", "to": "10:20",
         "subject": "Базы данных", "kindCls": "lab",
         "teacher": "Иванов И.И.", "room": "3118"},
        # Пара без преподавателя — такие в расписании МИЭТ встречаются.
        {"day": 3, "week": 0, "pair": 1, "from": "09:00", "to": "10:20",
         "subject": "Физкультура", "kindCls": "oth", "teacher": "", "room": ""},
    ],
}
sched_api.fetch_groups = lambda force=False: ["ПИН-31", "ПИН-32"]
sched_api.fetch_schedule = lambda group, force=False: FIXTURE
directory.PAUSE = 0

rows = directory.rebuild()
check("индекс собран", rows == 6, rows)
check("пары без преподавателя не индексируются",
      all(t["name"] for t in directory.teachers()), directory.teachers())
meta = directory.meta()
check("в мете записан семестр", meta["semestr"] == FIXTURE["semestr"], meta)
check("и время сборки", bool(meta["built_at"]), meta)

people = {t["name"]: t for t in directory.teachers()}
check("преподаватели найдены", set(people) == {"Иванов И.И.", "Петров П.П."},
      set(people))
check("считаются группы", people["Иванов И.И."]["groups"] == 2, people)

found = directory.teachers("Иван")
check("поиск по части фамилии", [t["name"] for t in found] == ["Иванов И.И."], found)

# Физкультуре и военке МИЭТ вместо фамилии ставит заглушку, и пар у неё
# тысячи: в списке она забивает весь верх, а найти по ней некого.
FIXTURE["lessons"].append(
    {"day": 4, "week": 0, "pair": 1, "from": "09:00", "to": "10:20",
     "subject": "Физкультура", "kindCls": "oth",
     "teacher": "Преподаватель ФВ", "room": "Спорткомплекс"})
directory.rebuild()
check("заглушка не попадает в список",
      all(not t["name"].startswith("Преподаватель")
          for t in directory.teachers()), directory.teachers())
check("и в поиск тоже", directory.teachers("Преподаватель") == [],
      directory.teachers("Преподаватель"))
check("но аудиторию она занимает",
      len(directory.room_schedule("Спорткомплекс")["slots"]) == 1,
      directory.room_schedule("Спорткомплекс"))
FIXTURE["lessons"].pop()
directory.rebuild()

card = directory.teacher_schedule("Иванов И.И.")
check("лекция потока схлопнута в одну пару", len(card["slots"]) == 2, card["slots"])
check("но группы перечислены обе",
      card["slots"][0]["groups"] == ["ПИН-31", "ПИН-32"], card["slots"][0])
check("аудитории собраны", card["rooms"] == ["3105", "3118"], card["rooms"])
check("предметы собраны", card["subjects"] == ["Базы данных"], card["subjects"])

room = directory.room_schedule("3105")
check("в аудитории две пары", len(room["slots"]) == 2, room["slots"])
check("и два преподавателя", len(room["teachers"]) == 2, room["teachers"])

s, r = api.handle("GET", "/api/directory/teachers", {"q": ["Петров"]}, {}, USER)
check("справочник открыт обычному человеку", s == 200 and len(r["teachers"]) == 1,
      (s, r))
s, r = api.handle("GET", "/api/directory/teacher", {"name": ["Иванов И.И."]}, {}, USER)
check("карточка отдаётся", s == 200 and len(r["slots"]) == 2, s)
s, _ = api.handle("GET", "/api/directory/teacher", {"name": ["Сидоров"]}, {}, USER)
check("неизвестного нет", s == 404, s)
s, r = api.handle("GET", "/api/directory/rooms", {}, {}, USER)
check("аудитории отдаются", s == 200 and len(r["rooms"]) == 2, r)
s, _ = api.handle("GET", "/api/directory/room", {"name": ["9999"]}, {}, USER)
check("несуществующей аудитории нет", s == 404, s)
s, _ = api.handle("GET", "/api/directory/teachers", {}, {}, "мусор")
check("без подписи справочник закрыт", s == 401, s)

# Пересборка не должна оставлять половину данных, если сайт отвалился.
sched_api.fetch_schedule = lambda group, force=False: (_ for _ in ()).throw(
    RuntimeError("сайт недоступен"))
kept = directory.rebuild()
check("при недоступном сайте прежний индекс сохранён",
      kept == 0 and directory.meta()["lessons"] == 6, directory.meta())


print("\n15. Доска взаимопомощи")
from . import help_board                                           # noqa: E402

help_board.PAUSE = 0
s, r = api.handle("POST", "/api/help", {},
                  {"kind": "need", "subject": "Матанализ",
                   "text": "Не понимаю ряды, нужен разбор"}, USER)
check("объявление создано", s == 200 and r["offer"]["kind"] == "need", (s, r))
need_id = r["offer"]["id"]
check("контакт автора виден — в этом смысл доски",
      r["offer"]["username"] == "student", r["offer"])

s, r2 = api.handle("POST", "/api/help", {},
                   {"kind": "offer", "subject": "Схемотехника",
                    "price": "deal"}, ADMIN)
check("предложение помощи создано",
      r2["offer"]["kind"] == "offer" and r2["offer"]["price"] == "deal", r2)

s, board = api.handle("GET", "/api/help", {}, {}, USER)
check("оба объявления в выдаче", len(board["offers"]) == 2, board["offers"])
check("счётчики по видам", board["need"] == 1 and board["offer"] == 1, board)
check("свои объявления отдельно", len(board["mine"]) == 1, board["mine"])

s, only = api.handle("GET", "/api/help", {"kind": ["offer"]}, {}, USER)
check("фильтр по виду", len(only["offers"]) == 1
      and only["offers"][0]["kind"] == "offer", only["offers"])
s, found = api.handle("GET", "/api/help", {"q": ["матан"]}, {}, USER)
check("поиск по предмету", len(found["offers"]) == 1, found["offers"])

s, _ = api.handle("POST", "/api/help", {}, {"kind": "need", "subject": "  "}, USER)
check("без предмета не принимается", s == 400, s)

help_board.PAUSE = 60
s, _ = api.handle("POST", "/api/help", {}, {"subject": "Ещё одно"}, USER)
check("частые публикации придержаны", s == 400, s)
help_board.PAUSE = 0

# Больше пяти открытых — это уже не «нужна помощь», а личная доска.
for i in range(4):
    api.handle("POST", "/api/help", {}, {"subject": f"Предмет {i}"}, USER)
s, _ = api.handle("POST", "/api/help", {}, {"subject": "Шестое"}, USER)
check("больше пяти открытых нельзя", s == 400, s)

# Владелец правит что угодно, поэтому чужое пробует обычный человек.
s, _ = api.handle("POST", f"/api/help/{r2['offer']['id']}/close", {}, {}, USER)
check("чужое объявление не закрыть", s == 403, s)
s, _ = api.handle("POST", f"/api/help/{need_id}/close", {}, {}, USER)
check("своё закрывается", s == 200, s)
s, board = api.handle("GET", "/api/help", {}, {}, USER)
check("закрытого в выдаче нет",
      all(o["id"] != need_id for o in board["offers"]), board["offers"])
check("но у автора оно осталось",
      any(o["id"] == need_id and o["status"] == "closed" for o in board["mine"]),
      board["mine"])
s, _ = api.handle("POST", f"/api/help/{need_id}/reopen", {}, {}, USER)
s, board = api.handle("GET", "/api/help", {}, {}, USER)
check("и открывается заново",
      any(o["id"] == need_id for o in board["offers"]), board["offers"])

# Уборку раздела выдают правом help_manage.
api.handle("POST", "/api/admin/users/42/role", {},
           {"role": "moderator", "perms": ["help_manage"], "sections": []}, ADMIN)
s, me = api.handle("GET", "/api/me", {}, {}, USER)
s, _ = api.handle("POST", f"/api/help/{r2['offer']['id']}/delete", {}, {}, USER)
check("с правом убирают чужое", s == 200, s)
api.handle("POST", "/api/admin/users/42/role", {},
           {"role": "none", "perms": [], "sections": []}, ADMIN)
s, _ = api.handle("POST", "/api/help/999999/close", {}, {}, ADMIN)
check("несуществующее — 404", s == 404, s)

print("\n16. Подробная статистика")
s, st = api.handle("GET", "/api/admin/stats", {}, {}, ADMIN)
check("часы суток в сводке", len(st["hours"]) == 24, st.get("hours"))
check("дни недели в сводке", len(st["weekdays"]) == 7, st.get("weekdays"))
check("неделя начинается с понедельника",
      st["weekdays"][0]["day"] == "Пн" and st["weekdays"][-1]["day"] == "Вс",
      [d["day"] for d in st["weekdays"]])
check("доска помощи в сводке", "help" in st and st["help"]["open"] >= 1,
      st.get("help"))

s, days = api.handle("GET", "/api/admin/days", {}, {}, ADMIN)
check("список дней отдан", len(days["days"]) == 30, len(days["days"]))
today = days["days"][-1]
check("сегодня есть действия", today["actions"] > 0, today)
check("и люди посчитаны", today["people"] > 0, today)

s, day = api.handle("GET", "/api/admin/day", {"date": [today["date"]]}, {}, ADMIN)
check("разбор дня отдан", s == 200 and day["date"] == today["date"], s)
check("в нём видно, кто был", day["people"] and day["people"][0]["actions"] > 0,
      day["people"][:1])
check("у человека есть имя и время", day["people"][0]["name"]
      and day["people"][0]["first_at"], day["people"][0])
check("часы дня расписаны", len(day["hours"]) == 24, len(day["hours"]))
check("виды действий посчитаны", day["kinds"], day["kinds"])
s, _ = api.handle("GET", "/api/admin/day", {"date": ["вчера"]}, {}, ADMIN)
check("кривая дата отвергнута", s == 400, s)
s, _ = api.handle("GET", "/api/admin/days", {}, {}, USER)
check("постороннему разбор закрыт", s == 403, s)

s, card = api.handle("GET", "/api/admin/users/42", {}, {}, ADMIN)
check("в карточке видно, что нажимают в боте", isinstance(card["bot_actions"], list),
      card.get("bot_actions"))
check("часы человека расписаны", len(card["hours"]) == 24, len(card["hours"]))
check("дни человека собраны", card["days"] and card["active_days"] >= 1,
      card.get("days"))


print("\n17. ОРИОКС: задания и приватность")
from . import orioks, orioks_web                                  # noqa: E402

# Сеть подменяем: ходить в настоящий ОРИОКС из проверок нельзя — нужен
# чужой логин, а сервер вуза не должен получать запросы на каждый прогон.
CALLS = []


def fake_request(path, headers, method="GET"):
    CALLS.append((path, headers, method))
    if path == "/auth":
        if headers.get("Authorization") == "Basic c3R1ZDpzZWNyZXQ=":
            return {"token": "T" * 32}
        raise orioks.OrioksError("ОРИОКС не принял данные для входа")
    if headers.get("Authorization") != "Bearer " + "T" * 32:
        raise orioks.OrioksError("ОРИОКС не принял данные для входа")
    if path == "/student/disciplines":
        return [{"id": 7, "name": "Матанализ", "teachers": ["Иванов И.И."],
                 "control_form": "Экзамен", "current_grade": 20.0,
                 "max_grade": 70.0, "exam_date": "2027-01-15"}]
    if path == "/student/disciplines/7/events":
        return [
            {"alias": "dz.1", "name": "Домашнее задание 1", "type": "Домашнее задание",
             "week": 4, "max_grade": 10.0, "current_grade": 8.0},
            {"alias": "dz.2", "name": "Домашнее задание 2", "type": "Домашнее задание",
             "week": 11, "max_grade": 10.0, "current_grade": -1.0},
            {"alias": "ex.1", "name": "Экзамен", "type": "Экзамен",
             "week": 17, "max_grade": 30.0, "current_grade": -1.0},
            # Так выглядят формальности в живом ОРИОКС: сдавать нечего.
            {"alias": "А/П", "name": "А/П", "type": "Активность/Посещаемость",
             "week": 8, "max_grade": 24.0},
            {"alias": "Порядок НБС", "name": "Порядок НБС",
             "type": "Активность", "week": 1, "max_grade": 0},
        ]
    # Отзыв — DELETE /student/tokens/<токен>, как в документации.
    if path.startswith("/student/tokens/") and method == "DELETE":
        return {"ok": True}
    raise orioks.OrioksError("ОРИОКС ответил 404")


orioks._request = fake_request


# Веб-версия в проверках не должна ходить в живой ОРИОКС: подменяем вход
# так же, как API. Заодно видно, что пароль доходит только сюда.
WEB_SEEN = {}


def fake_sign_in(login, password):
    WEB_SEEN["login"] = login
    WEB_SEEN["password"] = password
    if password != "secret":
        raise orioks_web.WebError("ОРИОКС не принял логин или пароль")
    return "PHPSESSID=web-session-abc"


orioks_web.sign_in_cookie = fake_sign_in


# Материалы: подменяем разбор страницы, чтобы проверки не ходили в сеть.
WEB_FAIL = {"how": None}


def fake_study(cookie):
    if WEB_FAIL["how"] == "expired":
        raise orioks_web.SessionExpired("Сессия ОРИОКС кончилась")
    if WEB_FAIL["how"] == "down":
        raise orioks_web.WebError("ОРИОКС недоступен (TimeoutError)")
    return {"dises": [{"name": "Матанализ", "segments": [{"allKms": [
        {"name": "Домашнее задание 1", "week": 4, "irs": [
            {"name": "Условие ДЗ", "type": "Задание",
             "link": "https://orioks.miet.ru/storage/d/1/dz.pdf"}]},
    ]}]}]}


orioks_web.study_json = fake_study

s, r = api.handle("GET", "/api/orioks", {}, {}, USER)
check("без подключения так и сказано", s == 200 and r["linked"] is False, r)

s, r = api.handle("POST", "/api/orioks/link", {},
                  {"login": "stud", "password": "wrong"}, USER)
check("неверный пароль отвергнут", s == 400, (s, r))
s, _ = api.handle("POST", "/api/orioks/link", {}, {"login": "stud"}, USER)
check("без пароля не пускает", s == 400, s)

s, r = api.handle("POST", "/api/orioks/link", {},
                  {"login": "stud", "password": "secret"}, USER)
check("подключение прошло", s == 200 and r["linked"], (s, r))
check("токен сохранён", orioks.token_of(42) == "T" * 32, orioks.token_of(42))

# Главное: пароль не должен осесть нигде. Проверяем всю базу целиком.
found = []
for (table,) in db.conn().execute(
        "SELECT name FROM sqlite_master WHERE type='table'"):
    cols = [c[1] for c in db.conn().execute(f"PRAGMA table_info({table})")]
    for col in cols:
        hits = db.conn().execute(
            f"SELECT COUNT(*) FROM {table} WHERE CAST({col} AS TEXT) LIKE ?",
            ("%secret%",)).fetchone()[0]
        if hits:
            found.append(f"{table}.{col}")
check("пароля нет нигде в базе", not found, found)

tasks = r["tasks"]
check("дисциплина получена", len(tasks["disciplines"]) == 1, tasks)
events = tasks["disciplines"][0]["events"]
check("мероприятия получены", len(events) == 5, events)
check("сданное отмечено", events[0]["done"] and events[0]["grade"] == 8.0,
      events[0])
check("несданное без оценки",
      not events[1]["done"] and events[1]["grade"] is None, events[1])
check("домашка распознана как задание", events[1]["homework"], events[1])
check("экзамен заданием не считается", not events[2]["homework"], events[2])
check("неделя сдачи сохранена", events[1]["week"] == 11, events[1])
# Экзамен, посещаемость и «порядок» в счёт заданий не идут: в фикстуре
# остаются два домашних задания, одно из них сдано.
check("счётчики считают только задания",
      tasks["total"] == 2 and tasks["done"] == 1, tasks)
check("рабочий путь мероприятий найден и запомнен",
      orioks._events_path == "/student/disciplines/{id}/events",
      orioks._events_path)
# Живой ОРИОКС отдаёт вперемешку с заданиями посещаемость и записи «для
# порядка»: у одного студента их оказалось больше трети из семидесяти
# пяти, и именно они делали экран нечитаемым.
check("посещаемость не считается заданием",
      not orioks.is_task({"type": "Активность/Посещаемость", "name": "А/П",
                          "max_grade": 24.0}))
check("мероприятие на ноль баллов не задание",
      not orioks.is_task({"type": "Активность", "name": "Порядок НБС",
                          "max_grade": 0}))
check("лабораторная — задание",
      orioks.is_task({"type": "Лабораторная работа", "name": "ЛР.1",
                      "max_grade": 10.0}))
check("формальности не попали в счёт заданий",
      tasks["total"] == 2, tasks["total"])
check("экзамен помечен как сессия, а не задание",
      events[2]["session"] and not events[2]["task"], events[2])
check("зачёт тоже относится к сессии",
      orioks.is_session({"type": "Зачёт"})
      and not orioks.is_task({"type": "Зачёт", "max_grade": 20}))
check("но в списке мероприятий они есть",
      len(events) == 5 and not events[3]["task"], events[3])

s, r = api.handle("GET", "/api/orioks", {}, {}, USER)
check("после подключения задания отдаются", r["linked"] and r["tasks"], r)
s, me = api.handle("GET", "/api/me", {}, {}, USER)
check("признак подключения виден клиенту", me["orioks"] is True, me)

# Чужие задания недоступны никому, включая владельца: в ОРИОКС ходим
# под токеном того, кто спрашивает, и ничьим больше.
s, r = api.handle("GET", "/api/orioks", {}, {}, ADMIN)
check("владелец не видит чужой ОРИОКС", r["linked"] is False, r)

s, r = api.handle("POST", "/api/orioks/unlink", {}, {}, USER)
check("отключение сработало", s == 200 and not r["linked"], r)
check("токен убран", orioks.token_of(42) == "", orioks.token_of(42))
check("и аннулирован в ОРИОКС",
      any(c[0].startswith("/student/tokens/") and c[2] == "DELETE"
          for c in CALLS), CALLS[-3:])
s, r = api.handle("GET", "/api/orioks", {}, {}, USER)
check("после отключения снова не подключено", r["linked"] is False, r)

# Коды ответов ОРИОКС расходятся с его же документацией: на неверный
# пароль приходит 403, отведённый в документации под лимит токенов.
# Поймано разведкой на боевом сервере — сообщение решает текст, не код.


class FakeHTTPError(Exception):
    def __init__(self, code, body):
        self.code = code
        self._body = body.encode("utf-8")

    def read(self):
        return self._body


check("неверный пароль под кодом 403 назван правильно",
      orioks._explain(FakeHTTPError(403, '{"error":"Неверный логин или пароль"}'))
      == "ОРИОКС не принял логин или пароль",
      orioks._explain(FakeHTTPError(403, '{"error":"Неверный логин или пароль"}')))
check("лимит токенов отличается от неверного пароля",
      "восемь" in orioks._explain(FakeHTTPError(
          403, '{"error":"Нельзя получить больше восьми токенов"}')),
      orioks._explain(FakeHTTPError(403, '{"error":"Нельзя получить больше восьми токенов"}')))
check("вложенный текст ошибки тоже читается",
      "обработке" in orioks._explain(FakeHTTPError(
          400, '{"error":{"code":400,"text":"Произошла ошибка при обработке запроса"}}')),
      orioks._explain(FakeHTTPError(400, '{"error":{"code":400,"text":"Произошла ошибка при обработке запроса"}}')))
check("пустое тело не роняет разбор",
      orioks._explain(FakeHTTPError(500, "")) == "ОРИОКС ответил 500",
      orioks._explain(FakeHTTPError(500, "")))



# ── веб-версия ОРИОКС: сессия вместо пароля ──
# Выше связь уже разрывали, поэтому подключаемся заново: нас интересует
# именно то, что кладёт в базу успешный вход.
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
check("сессия сохранена при подключении",
      orioks.cookie_of(42) == "PHPSESSID=web-session-abc", orioks.cookie_of(42))
check("пароль дошёл только до входа", WEB_SEEN.get("password") == "secret")

# Та же проверка всей базы, но теперь после сохранения сессии: cookie
# лежит, пароль — нет.
found2 = []
for (table,) in db.conn().execute(
        "SELECT name FROM sqlite_master WHERE type='table'"):
    for col in [c[1] for c in db.conn().execute(f"PRAGMA table_info({table})")]:
        if db.conn().execute(
                f"SELECT COUNT(*) FROM {table} WHERE CAST({col} AS TEXT) LIKE ?",
                ("%secret%",)).fetchone()[0]:
            found2.append(f"{table}.{col}")
check("пароля нет в базе и после входа в веб-версию", not found2, found2)

orioks.drop_cookie(42)
check("отключение стирает сессию сразу", orioks.cookie_of(42) == "")
orioks.save_cookie(42, "PHPSESSID=web-session-abc")

# Разведка кабинета — только своя. Чужую сессию не берёт никто, включая
# владельца: смотрим по me["id"], а не по запрошенному пользователю.
s_, r_ = api.handle("GET", "/api/admin/orioks-web-dump", {}, {}, USER)
check("не админу разведка недоступна", s_ == 403, (s_, r_))

orioks.forget(42)
s_, r_ = api.handle("GET", "/api/admin/orioks-web-dump", {}, {}, ADMIN)
check("без сессии владельцу сказано переподключиться",
      s_ == 200 and "переподключи" in r_.get("error", ""), (s_, r_))

# Разбор страницы кабинета: заголовок, ссылки, текст без разметки.
page = ('<html><title> Журнал </title><body><script>x=1</script>'
        '<h1>Домашнее задание 1</h1><p>Решить задачи 1-5</p>'
        '<a href="/student/journal">Мой журнал</a>'
        '<a href="/site/logout">Выход</a></body></html>')
check("заголовок страницы читается", orioks_web._title(page) == "Журнал")
check("текст очищен от разметки и скриптов",
      "Решить задачи 1-5" in orioks_web.text_of(page)
      and "x=1" not in orioks_web.text_of(page), orioks_web.text_of(page))
check("ссылки кабинета собраны",
      ("/student/journal", "Мой журнал") in orioks_web._links(page),
      orioks_web._links(page))
check("csrf вынимается из скрытого поля",
      orioks_web._csrf_of('<input type="hidden" name="_csrf" value="Ab-9_z">')
      == "Ab-9_z")
check("без формы csrf пустой", orioks_web._csrf_of("<p>нет</p>") == "")



# ── материалы, выложенные преподавателем ──
# Текста задания в ОРИОКС нет нигде; есть вложение, которое его несёт.
# Связь выше разрывали — подключаемся заново.
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
orioks.forget_materials(42)
s_, r_ = api.handle("GET", "/api/orioks", {}, {}, USER)
ev = r_["tasks"]["disciplines"][0]["events"]
dz = [e for e in ev if e["name"] == "Домашнее задание 1"]
check("вложение приклеилось к своему мероприятию",
      dz and dz[0].get("materials"), ev)
check("у вложения есть название и ссылка",
      dz[0]["materials"][0]["name"] == "Условие ДЗ"
      and dz[0]["materials"][0]["link"].endswith("dz.pdf"), dz[0]["materials"])
check("у мероприятия без вложений список пуст",
      not [e for e in ev if e["name"] == "Экзамен"][0].get("materials"), ev)
check("счётчик вложений отдан", r_["tasks"]["materials_count"] == 1,
      r_["tasks"].get("materials_count"))

# Заминка у института не должна стоить человеку пароля.
orioks.forget_materials(42)
WEB_FAIL["how"] = "down"
s_, r_ = api.handle("GET", "/api/orioks", {}, {}, USER)
check("при недоступности ОРИОКС задания остаются", s_ == 200 and r_["linked"])
check("и доступ не стирается", orioks.cookie_of(42) != "", orioks.cookie_of(42))

# А кончившаяся сессия — стирается: держать мёртвую незачем.
orioks.forget_materials(42)
WEB_FAIL["how"] = "expired"
api.handle("GET", "/api/orioks", {}, {}, USER)
check("кончившаяся сессия убрана", orioks.cookie_of(42) == "")
WEB_FAIL["how"] = None

check("вложения без ссылки не берём",
      orioks_web.materials({"dises": [{"name": "Д", "segments": [
          {"allKms": [{"name": "К", "irs": [{"name": "без ссылки"}]}]}]}]}) == [])


# ── объявления преподавателей ──
# Здесь и живёт «задание к следующему занятию»: преподаватель пишет
# его объявлением к дисциплине, а не мероприятием.
PAGE_NEWS = (
    '<a href="/student/news/view?id=45462">Инструкция к ЛР №1</a>'
    '<div>Дата публикации: 04.09.2026 17:16</div>'
    '<p>Ищем модуль Лабораторный практикум.</p>'
    '<div>Автор: Королева Е.Н.</div><div>Комментариев: 0</div>'
    '<a href="/student/news/view?id=45415">Подготовка к ЛР №1</a>'
    '<div>Дата публикации: 03.09.2026 15:05</div>'
    '<p>На первом занятии студенты приступают к работе.</p>'
    '<div>Автор: Трифонов А.Ю.</div><div>Комментариев: 0</div>')


def fake_page(cookie, path, ajax=False):
    if "discipline_id=1" in path:
        return PAGE_NEWS
    if "discipline_id=2" in path:
        raise orioks_web.WebError("ОРИОКС ответил 403 на " + path)
    return "<html></html>"


_real_page = orioks_web.get_page
orioks_web.get_page = fake_page

got = orioks_web.course_news("c", {"dises": [
    {"id": 1, "name": "Физика"}, {"id": 2, "name": "Матанализ"}]})
check("объявления дисциплины разобраны", len(got) == 2, got)
check("заголовок взят из ссылки", got[0]["title"] == "Инструкция к ЛР №1", got[0])
check("новое объявление первое", got[0]["date"].startswith("04.09"), got)
check("автор распознан", got[1]["author"] == "Трифонов А.Ю.", got[1])
check("выжимка без подписи автора",
      "Комментариев" not in got[0]["preview"]
      and "Лабораторный практикум" in got[0]["preview"], got[0]["preview"])
check("закрытая дисциплина не роняет список",
      all(n["discipline"] == "Физика" for n in got), got)

# Сортировка по дате, а не по строке: «09.09» не должно оказаться
# старше «10.08» только потому, что девятка больше единицы.
check("даты сравниваются по-человечески",
      orioks_web._when({"date": "10.08.2026 09:00"})
      < orioks_web._when({"date": "09.09.2026 09:00"}))
check("объявление без даты не ломает сортировку",
      orioks_web._when({"date": ""}) == "")

# Текст объявления — без хвоста разметки: он начинался с «/div>».
orioks_web.get_page = lambda c, p, ajax=False: (
    '<h2><a href="/student/news/view?id=1">Задание к семинару</a></h2>'
    '<div>Дата публикации: 08.09.2026 22:53</div>'
    '<p>Подготовить доклады по теме.</p>'
    '<div>Дисциплина: История России</div>')
one = orioks_web.news_item("c", "/student/news/view?id=1")
check("заголовок объявления взят из самой новости",
      one["title"] == "Задание к семинару", one)
check("текст без хвоста тега",
      one["text"].startswith("Подготовить"), one["text"][:40])
check("дата объявления разобрана", one["date"] == "08.09.2026 22:53", one)
# Адрес объявления приходит от клиента, поэтому наружу он вести не
# должен: иначе через нашу сессию можно было бы дёрнуть чужой сайт.
try:
    orioks_web.news_item("c", "http://evil/x")
    outside = False
except orioks_web.WebError:
    outside = True
check("чужой адрес не открыть", outside)

orioks_web.get_page = _real_page


print("\n18. Сторож объявлений: бот сам говорит, что задали")
import datetime as dt                                             # noqa: E402
from . import notify, orioks_watch                                # noqa: E402

# Обход не должен ждать по две секунды на человека: пауза нужна живому
# ОРИОКС, а не проверке.
orioks_watch.BETWEEN = 0

SENT = []
notify.bind(lambda uid, text: SENT.append((uid, text)))

FEED = {"items": [], "how": None}


def fake_news(cookie, data=None):
    if FEED["how"] == "expired":
        raise orioks_web.SessionExpired("Сессия ОРИОКС кончилась")
    if FEED["how"] == "down":
        raise orioks_web.WebError("ОРИОКС недоступен (TimeoutError)")
    return FEED["items"]


orioks_web.course_news = fake_news


def news(num, title, discipline="Физика", preview="", author=""):
    return {"id": str(num), "href": f"/student/news/view?id={num}",
            "title": title, "discipline": discipline, "preview": preview,
            "author": author, "date": "08.09.2026 22:53", "course": True}


# Подключаемся заново: выше сессию намеренно роняли.
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
orioks_watch.forget(42)

# Первый заход молчит. Иначе подключение ОРИОКС в середине семестра
# оборачивалось бы десятком сообщений подряд ни о чём.
FEED["items"] = [news(1, "Подготовка к ЛР №1"), news(2, "Задание к семинару")]
first = orioks_watch.check_user(42)
check("первый заход молчит", not first and not SENT, (first, SENT))
check("но всё запомнил", orioks_watch.seen_ids(42) == {"1", "2"},
      orioks_watch.seen_ids(42))

# Появилось новое — вот теперь сообщение.
FEED["items"] = [news(3, "Лабораторная №2", "Физика",
                      "Оформить отчёт к среде", "Королева Е.Н.")] + FEED["items"]
fresh = orioks_watch.check_user(42)
check("новое объявление замечено", len(fresh) == 1 and fresh[0]["id"] == "3",
      fresh)
check("сообщение ушло человеку", len(SENT) == 1 and SENT[0][0] == 42, SENT)
told = SENT[0][1] if SENT else ""
check("в сообщении предмет и заголовок",
      "Физика" in told and "Лабораторная №2" in told, told)
check("выжимка приложена", "Оформить отчёт к среде" in told, told)
# Ссылка должна вести на сайт целиком: относительный адрес в Telegram
# не откроется никак.
check("ссылка абсолютная",
      'href="https://orioks.miet.ru/student/news/view?id=3"' in told, told)

# Второй обход по тому же списку обязан молчать: повтор каждые полтора
# часа — самая быстрая причина выключить уведомления навсегда.
SENT.clear()
again = orioks_watch.check_user(42)
check("прочитанное не повторяется", not again and not SENT, (again, SENT))

# Пять новых разом: показываем часть, про остальное говорим числом.
FEED["items"] = [news(i, f"Объявление {i}") for i in range(10, 15)] + FEED["items"]
many = orioks_watch.check_user(42)
check("все новые сосчитаны", len(many) == 5, len(many))
check("в сообщении показаны не все", "И ещё 2" in SENT[-1][1], SENT[-1][1])

# Молчание института не стоит человеку пароля — это уже ломалось раз.
SENT.clear()
FEED["how"] = "down"
check("при недоступности ОРИОКС ничего не шлём",
      not orioks_watch.check_user(42) and not SENT, SENT)
check("и доступ остаётся", orioks.cookie_of(42) != "", orioks.cookie_of(42))

# А прямой отказ — стирает сессию и объясняет это один раз.
FEED["how"] = "expired"
orioks_watch.check_user(42)
check("кончившаяся сессия убрана сторожем", orioks.cookie_of(42) == "")
check("человеку сказано, что надо войти заново",
      len(SENT) == 1 and "войти заново" in SENT[0][1], SENT)
check("без сессии обход этого человека пропускает",
      42 not in orioks_watch.watchers(), orioks_watch.watchers())
FEED["how"] = None

# Подписка: по умолчанию включена, выключается своим маршрутом.
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
check("подписка включена по умолчанию", orioks_watch.notify_on(42))
check("подписчик виден обходу", 42 in orioks_watch.watchers(),
      orioks_watch.watchers())
s_, r_ = api.handle("POST", "/api/orioks/notify", {}, {"on": False}, USER)
check("подписка выключается", s_ == 200 and r_["notify"] is False, (s_, r_))
check("выключивший выпал из обхода", 42 not in orioks_watch.watchers(),
      orioks_watch.watchers())
s_, r_ = api.handle("GET", "/api/orioks", {}, {}, USER)
check("состояние подписки видно клиенту", r_.get("notify") is False, r_)
api.handle("POST", "/api/orioks/notify", {}, {"on": True}, USER)
check("и включается обратно", orioks_watch.notify_on(42))

# Ночью не пишем: задание в час ночи ничего не меняет, кроме сна.
check("днём обход идёт",
      orioks_watch.daytime(dt.datetime(2026, 9, 9, 13, 0)))
check("ночью — нет",
      not orioks_watch.daytime(dt.datetime(2026, 9, 9, 3, 0))
      and not orioks_watch.daytime(dt.datetime(2026, 9, 9, 23, 30)))

# Обход целиком: он же проверяет, что подписанный получает сообщение
# не в одиночной проверке, а тем самым кругом, что крутится в боте.
SENT.clear()
FEED["items"] = [news(21, "Новая тема", "Физика", "Прочитать главу 3")]
orioks_watch.forget(42)
orioks_watch.round_once()
FEED["items"] = [news(22, "Ещё одно")] + FEED["items"]
check("круг обхода доносит новое", orioks_watch.round_once() == 1
      and len(SENT) == 1, SENT)

# Отключение ОРИОКС уносит память об объявлениях: иначе повторное
# подключение молча съело бы первую рассылку.
api.handle("POST", "/api/orioks/unlink", {}, {}, USER)
check("память об объявлениях ушла с доступом",
      orioks_watch.seen_ids(42) == set(), orioks_watch.seen_ids(42))
check("без подключения подписку не включить",
      api.handle("POST", "/api/orioks/notify", {}, {"on": True}, USER)[0] == 400)
check("отключившийся в обход не попадает", 42 not in orioks_watch.watchers(),
      orioks_watch.watchers())

# Разведка сторожа — только владельцу и только про него самого:
# чужие объявления не сторожит никто, и посмотреть на них тоже нельзя.
s_, r_ = api.handle("GET", "/api/admin/orioks-watch", {}, {}, USER)
check("разведка сторожа не для всех", s_ == 403, (s_, r_))
s_, r_ = api.handle("GET", "/api/admin/orioks-watch", {}, {}, ADMIN)
check("владельцу сторож отчитывается",
      s_ == 200 and "watchers" in r_ and r_["fresh"] == [], (s_, r_))

notify.bind(None)

print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
