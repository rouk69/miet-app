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
from . import uptime                                              # noqa: E402

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
s, h = api.handle("GET", "/api/health", {}, {}, "")
check("проверка живости не требует подписи", s == 200, s)
# Здоровье процесса отдаётся без подписи, и это осознанно: по нему
# разбирают жалобу «не открылось приложение». Значит в ответе не должно
# оказаться ничего личного — только числа про сам процесс.
check("живость говорит, сколько бот живёт", "uptime" in h and "starts_24h" in h, h)
uptime.note_start()
s, h = api.handle("GET", "/api/health", {}, {}, "")
check("запуск попал в историю", h["starts_24h"] >= 1 and h["started_at"], h)
db.conn().execute("DELETE FROM starts")

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

# Номер аудитории отделяется от пометок кафедры и вида занятия. Найдено
# на живом расписании: «1202» и «1202 м» — это один кабинет, и без
# склейки он показывался свободным, будучи занятым под другим
# написанием. То есть раздел врал ровно в том, ради чего он сделан.
check("пометка после номера отбрасывается",
      directory.room_key("1202 м") == "1202", directory.room_key("1202 м"))
check("буква в самом номере остаётся",
      directory.room_key("3102а л ПМТ") == "3102а", directory.room_key("3102а л ПМТ"))
check("кафедра в хвосте не мешает",
      directory.room_key("3125 ВП СГН") == "3125", directory.room_key("3125 ВП СГН"))
check("нечисловое имя остаётся собой",
      directory.room_key("Спорткомплекс") == "спорткомплекс",
      directory.room_key("Спорткомплекс"))

# Свободные аудитории. Фонд считается по самому расписанию: списка
# кабинетов МИЭТ нигде нет, и всё, что известно, — где хоть раз стоит
# пара. В фикстуре это 3105 и 3118.
free = directory.free_rooms(0, 1, 1)
check("занятая аудитория из свободных убрана",
      all(r["name"] != "3105" for r in free["free"]), free)
check("свободная — на месте",
      any(r["name"] == "3118" for r in free["free"]), free)
check("фонд считается по расписанию", free["total"] == 2, free)
check("занятых в слоте одна", free["busy"] == 1, free)
check("время слота взято из расписания",
      free["from"] == "09:00" and free["to"] == "10:20", free)

# «Свободна до» — главный вопрос: успеем ли доделать. В фикстуре 3105
# занята первой парой и второй, дальше в этот день — нет.
free2 = directory.free_rooms(0, 1, 3)
room = next(r for r in free2["free"] if r["name"] == "3105")
check("после последней пары — до конца дня", room["until_pair"] is None, room)
free0 = directory.free_rooms(0, 1, 1)
busy_later = next(r for r in free0["free"] if r["name"] == "3118")
check("в другой день занятость не считается",
      busy_later["until_pair"] is None, busy_later)

s, r = api.handle("GET", "/api/directory/free",
                  {"week": ["0"], "day": ["1"], "pair": ["1"]}, {}, USER)
check("маршрут свободных аудиторий отвечает",
      s == 200 and r["busy"] == 1, (s, r))
s, r = api.handle("GET", "/api/directory/free",
                  {"week": ["99"], "day": ["0"], "pair": ["77"]}, {}, USER)
check("кривой слот не роняет, а зажимается в границы",
      s == 200 and 0 <= r["week"] <= 3 and 1 <= r["day"] <= 6
      and 1 <= r["pair"] <= 8, (s, r))
s, _ = api.handle("GET", "/api/directory/free", {}, {}, "мусор")
check("и без подписи закрыт", s == 401, s)

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

# ─── доступ к «Учёбе»: закрыто всем, кроме владельца ───
from bot import orioks_access  # noqa: E402

s, r = api.handle("GET", "/api/orioks", {}, {}, USER)
check("студенту раздел закрыт", s == 403, (s, r))
s, r = api.handle("GET", "/api/me", {}, {}, USER)
check("и приложение об этом знает", r.get("orioks_access") is False, r)
s, r = api.handle("GET", "/api/me", {}, {}, ADMIN)
check("владельцу открыт", r.get("orioks_access") is True and r.get("root") is True, r)

# Полный админ, но не владелец: раздел ему сам собой не достаётся,
# выдать его другим и открыть всем он тоже не может.
SUB_ADMIN = init_data(555, "Второй", "second")
api.handle("GET", "/api/me", {}, {}, SUB_ADMIN)
api.handle("POST", "/api/admin/users/555/role", {},
           {"role": "admin", "perms": [], "sections": []}, ADMIN)
s, r = api.handle("GET", "/api/orioks", {}, {}, SUB_ADMIN)
check("полному админу не открыт сам собой", s == 403, (s, r))
s, r = api.handle("POST", "/api/admin/users/42/role", {},
                  {"role": "none", "perms": [], "sections": ["orioks"]}, SUB_ADMIN)
check("выдать доступ админ не может",
      not orioks_access.allowed_id(42), orioks_access.allowed_id(42))
s, r = api.handle("POST", "/api/admin/settings", {},
                  {"key": "orioks_open", "value": True}, SUB_ADMIN)
check("открыть всем админ не может", s == 403, (s, r))

# Владелец открывает всем — и закрывает обратно.
s, r = api.handle("POST", "/api/admin/settings", {},
                  {"key": "orioks_open", "value": True}, ADMIN)
check("владелец открывает всем", s == 200 and orioks_access.allowed_id(42), (s, r))
api.handle("POST", "/api/admin/settings", {},
           {"key": "orioks_open", "value": False}, ADMIN)
check("и закрывает", not orioks_access.allowed_id(42))

# Владелец выдаёт доступ одному человеку.
s, r = api.handle("POST", "/api/admin/users/42/role", {},
                  {"role": "none", "perms": [], "sections": ["orioks"]}, ADMIN)
check("владелец выдаёт доступ", s == 200 and orioks_access.allowed_id(42), (s, r))
# Сохранение роли другим админом не стирает выданное владельцем.
api.handle("POST", "/api/admin/users/42/role", {},
           {"role": "none", "perms": [], "sections": []}, SUB_ADMIN)
check("чужое сохранение роли доступ не стирает", orioks_access.allowed_id(42))
api.handle("POST", "/api/admin/users/555/role", {},
           {"role": "none", "perms": [], "sections": []}, ADMIN)

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


# Вторая половина источника — страница уведомлений. Она бонусная, и
# ходить в неё из проверок тоже нельзя.
NOTIFY_FAIL = {"how": None}


def fake_notify_page(cookie, limit=40):
    if NOTIFY_FAIL["how"] == "down":
        raise orioks_web.WebError("ОРИОКС недоступен (TimeoutError)")
    return []


orioks_web.announcements = fake_notify_page


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
check("но всё запомнил", orioks_watch.seen_ids(42) == {"-", "1", "2"},
      orioks_watch.seen_ids(42))

# Пустой ОРИОКС — тоже обойдённый. Иначе у студента, у которого
# объявлений ещё нет, первое молча ушло бы в память вместо лички.
FEED["items"] = []
orioks_watch.forget(43)
orioks.save_token(43, "T" * 32)
orioks.save_cookie(43, "PHPSESSID=web-session-abc")
orioks_watch.check_user(43)
check("пустой список тоже считается обходом",
      orioks_watch.seen_ids(43) == {"-"}, orioks_watch.seen_ids(43))
SENT.clear()
FEED["items"] = [news(99, "Первое объявление")]
check("и первое объявление уже доходит",
      len(orioks_watch.check_user(43)) == 1 and len(SENT) == 1, SENT)
orioks.forget(43)
orioks_watch.forget(43)
SENT.clear()
FEED["items"] = [news(1, "Подготовка к ЛР №1"), news(2, "Задание к семинару")]

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
# Без сессии сайта объявления не проверить, но баллы идут по токену —
# человек из обхода не выпадает, выпадают только объявления.
check("без сессии в обходе остаётся ради баллов",
      42 in orioks_watch.watchers(), orioks_watch.watchers())
SENT.clear()
check("а объявления без сессии не проверяются",
      not orioks_watch.check_user(42) and not SENT, SENT)
FEED["how"] = None

# ─── сторож баллов ───
# Мероприятия дисциплины 7 подменяем на изменяемый список: так видно,
# как сторож реагирует на новый, исправленный и снятый балл.
from bot import orioks_grades  # noqa: E402

EVENTS7 = [
    {"alias": "dz.1", "name": "Домашнее задание 1", "type": "Домашнее задание",
     "week": 4, "max_grade": 10.0, "current_grade": 8.0},
    {"alias": "dz.2", "name": "Домашнее задание 2", "type": "Домашнее задание",
     "week": 11, "max_grade": 10.0, "current_grade": -1.0},
    {"alias": "ex.1", "name": "Экзамен", "type": "Экзамен",
     "week": 17, "max_grade": 30.0, "current_grade": -1.0},
]
_plain_request = orioks._request


def graded_request(path, headers, method="GET"):
    if path == "/student/disciplines/7/events":
        _plain_request(path, headers, method)      # та же проверка токена
        return [dict(e) for e in EVENTS7]
    return _plain_request(path, headers, method)


orioks._request = graded_request

data = orioks.tasks("T" * 32)
mat = data["disciplines"][0]
# ОРИОКС отдаёт у дисциплины максимум только по оценённому (здесь 70 —
# из фикстуры); за семестр можно набрать сумму максимумов всех точек.
check("максимум за семестр — сумма точек", mat["semester_max"] == 50,
      mat["semester_max"])
check("у точки есть ключ", mat["events"][0]["key"] == "7:dz.1",
      mat["events"][0].get("key"))

orioks_grades.forget(42)
SENT.clear()
check("первый обход баллов молчит",
      not orioks_watch.check_grades(42) and not SENT, SENT)
check("но всё запомнил",
      len(orioks_grades._known(42)) == len(EVENTS7) + 1, orioks_grades._known(42))
check("и ничего не считает недавним", orioks_grades.recent(42) == {},
      orioks_grades.recent(42))
row = db.conn().execute("SELECT group_concat(sig) FROM orioks_grades "
                     "WHERE user_id=42").fetchone()[0]
check("самих баллов в базе нет — только отпечатки",
      "8.0" not in row and "|8" not in row, row)

SENT.clear()
check("повторный обход без перемен молчит",
      not orioks_watch.check_grades(42) and not SENT, SENT)

# Поставили за второе ДЗ.
EVENTS7[1]["current_grade"] = 9.0
SENT.clear()
got = orioks_watch.check_grades(42)
check("новый балл замечен",
      len(got) == 1 and got[0]["name"] == "Домашнее задание 2"
      and got[0]["fixed"] is False, got)
told = SENT[0][1] if SENT else ""
check("сообщение ушло человеку", len(SENT) == 1 and SENT[0][0] == 42, SENT)
check("в сообщении предмет, точка и балл",
      "Матанализ" in told and "Домашнее задание 2" in told
      and "<b>9</b> из 10" in told, told)
check("и итог по предмету за семестр", "из 50" in told, told)
check("недавнее видно приложению", "7:dz.2" in orioks_grades.recent(42),
      orioks_grades.recent(42))

# Исправили первое ДЗ: 8 → 10.
EVENTS7[0]["current_grade"] = 10.0
SENT.clear()
got = orioks_watch.check_grades(42)
check("исправленный балл помечен",
      len(got) == 1 and got[0]["fixed"] is True
      and "исправлен" in (SENT[0][1] if SENT else ""), (got, SENT))

# Балл сняли: запоминаем молча — «балл убрали» без причины только пугает.
EVENTS7[0]["current_grade"] = -1.0
SENT.clear()
check("снятый балл не объявляется",
      not orioks_watch.check_grades(42) and not SENT, SENT)
EVENTS7[0]["current_grade"] = 10.0
SENT.clear()
check("а вернувшийся — это новый балл",
      len(orioks_watch.check_grades(42)) == 1 and len(SENT) == 1, SENT)

# Сухой прогон ничего не записывает и не шлёт.
EVENTS7[2]["current_grade"] = 25.0
SENT.clear()
dry = orioks_watch.check_grades(42, send=False)
check("сухой прогон видит новое", len(dry) == 1, dry)
check("но не шлёт и не запоминает",
      not SENT and len(orioks_watch.check_grades(42)) == 1, SENT)

# Сломанный ОРИОКС — ничего не стираем и не шлём.
orioks._request = lambda *a, **k: (_ for _ in ()).throw(
    orioks.OrioksError("ОРИОКС недоступен"))
SENT.clear()
check("отказ ОРИОКС — тишина", not orioks_watch.check_grades(42) and not SENT)
check("и память цела", len(orioks_grades._known(42)) > 1)
orioks._request = graded_request

s_, r_ = api.handle("GET", "/api/orioks", {}, {}, USER)
check("приложение получает недавние баллы",
      s_ == 200 and "7:dz.2" in r_.get("recent", {}), r_.get("recent"))
check("сдача работ студенту не видна", r_.get("homework_beta") is False, r_)

# ─── баллы с сайта: API от него отстаёт ───
# Живой случай 24.09.2026: сайт показывал посещаемость и КР, API — нет.
# Структура — выжимка настоящего JSON веб-версии.
web_study = {"dises": [{"name": "Матанализ", "segments": [{"allKms": [
    {"sh": "dz.2", "name": "Домашнее задание 2", "week": 11, "max_ball": 10,
     "balls": [{"ball": 7}], "grade": {"b": 7, "p": "70.0", "o": 4}},
    {"sh": "dz.1", "name": "Домашнее задание 1", "week": 4, "max_ball": 10,
     "balls": [], "grade": {"b": "-", "p": "-", "o": "n"}},
    {"sh": "А/П", "name": " ", "week": 8, "max_ball": 24,
     "balls": [{"ball": 3}], "grade": {"b": "-", "p": "-", "o": "n"}},
]}]}]}
marks = orioks_web.grades(web_study)
check("с сайта взяты только выставленные",
      sorted(m["sh"] for m in marks) == ["dz.2", "А/П"], marks)
check("запасной путь — сумма balls",
      next(m for m in marks if m["sh"] == "А/П")["ball"] == 3, marks)

_saved7 = [e["current_grade"] for e in EVENTS7]
EVENTS7[0]["current_grade"] = 8.0
EVENTS7[1]["current_grade"] = -1.0
EVENTS7[2]["current_grade"] = -1.0
data = orioks.tasks("T" * 32)
data = orioks.with_web_grades(data, marks)
mat = data["disciplines"][0]
dz2 = next(e for e in mat["events"] if e["alias"] == "dz.2")
check("балл, которого нет в API, взят с сайта",
      dz2["grade"] == 7 and dz2["done"] and dz2.get("from_site"), dz2)
dz1 = next(e for e in mat["events"] if e["alias"] == "dz.1")
check("то, чего на сайте нет, из API не стирается",
      dz1["grade"] == 8 and dz1["done"], dz1)
check("сумма по предмету пересчитана", mat["current_grade"] == 15, mat["current_grade"])
check("и максимум по оценённому тоже", mat["max_grade"] == 20, mat["max_grade"])
check("счётчик сданного пересчитан", data["done"] == 2, data["done"])

# Одноимённые точки: у языка «КМ» на 6-й и 12-й неделе, балл есть только
# у первой. По одному названию он приклеивался ко второй (живой случай).
twins = {"disciplines": [{"id": 9, "name": "Язык", "events": [
    {"alias": "", "name": "КМ", "week": 6, "grade": None, "done": False, "max_grade": 10},
    {"alias": "", "name": "КМ", "week": 12, "grade": None, "done": False, "max_grade": 10},
]}]}
orioks.with_web_grades(twins, [{"discipline": "Язык", "sh": "", "name": "КМ",
                                "week": 6, "ball": 0.7, "max": 10}])
ev = twins["disciplines"][0]["events"]
check("балл одноимённой точки не уезжает на соседнюю",
      ev[0]["grade"] == 0.7 and ev[1]["grade"] is None, ev)
for e, g in zip(EVENTS7, _saved7):
    e["current_grade"] = g

# ─── сдача работ: фундамент только для владельца ───
from bot import orioks_homework  # noqa: E402

# Страница формы — выжимка настоящей: список дисциплин, мероприятия в
# data-kms, CSRF. Мероприятия у ОРИОКС — «N неделя: имя».
CREATE_HTML = (
    '<form id="w0" action="/student/homework/create?id_type=2" method="post">'
    '<input type="hidden" name="_csrf" value="CSRF-1">'
    '<select id="homework-discipline-field" name="HomeworkTreadForm[dis_id]">'
    '<option value=""></option><option value="300169">Информатика</option>'
    '<option value="300175">Математический анализ</option></select>'
    '<select id="homework-km-field" class="form-control" name="HomeworkTreadForm[id_km]" '
    "data-kms='{\"300169\":{\"2071580\":{\"name\":\"2 неделя: ЛР.1 ЛР.1\"}},"
    "\"300175\":{\"2080001\":{\"name\":\"3 неделя: ДЗ.1\"}}}'></select>"
    '<textarea name="HomeworkTreadForm[message]"></textarea></form>')
LIST_HTML = (
    '<table><tr><th>Статус</th><th>Название</th><th>Дисциплина</th>'
    '<th>Контрольное мероприятие</th><th>Студент</th><th>Группа</th>'
    '<th>Время создания</th><th>Новых</th></tr>'
    '<tr><td>В работе</td><td><a href="/student/homework/view?id=55">Отчёт ЛР1</a></td>'
    '<td>Информатика</td><td>ЛР.1</td><td>Иванов</td><td>ПИН-11</td>'
    '<td>20.09.2026 12:00</td><td>2</td></tr></table>')
POSTED = []
HW = {"reply": ("", "https://orioks.miet.ru/student/homework/view?id=56")}


def fake_page(cookie, path, ajax=False):
    if path.startswith("/student/homework/create"):
        return CREATE_HTML
    if path.startswith("/student/homework/list"):
        return LIST_HTML
    raise orioks_web.WebError("нет такой страницы в фикстуре")


def fake_post(cookie, path, data):
    POSTED.append((cookie, path, dict(data)))
    return HW["reply"]


orioks_web.get_page = fake_page
orioks_homework._post = fake_post

form = orioks_homework.parse_form(CREATE_HTML)
check("дисциплины разобраны",
      [d["name"] for d in form["disciplines"]] == ["Информатика", "Математический анализ"],
      form)
check("мероприятия пришли из data-kms",
      form["disciplines"][0]["events"] == [{"id": 2071580, "name": "2 неделя: ЛР.1 ЛР.1"}],
      form["disciplines"][0])
lst = orioks_homework.parse_list(LIST_HTML)
check("обращение разобрано по заголовкам",
      len(lst) == 1 and lst[0]["status"] == "В работе" and lst[0]["new"] == 2
      and lst[0]["href"] == "/student/homework/view?id=55", lst)

orioks.save_token(777, "T" * 32)
orioks.save_cookie(777, "PHPSESSID=owner")
s_, r_ = api.handle("GET", "/api/orioks/homework", {}, {}, USER)
check("студенту маршрута нет", s_ == 404, s_)
s_, r_ = api.handle("GET", "/api/orioks/homework", {}, {}, ADMIN)
check("владелец видит форму и обращения",
      s_ == 200 and r_["threads"] and r_["form"]["disciplines"], (s_, r_))

good = {"dis_id": 300169, "km_id": 2071580, "type": 2,
        "title": "Отчёт", "variant": "3", "message": "Готово, отчёт во вложении"}
s_, r_ = api.handle("POST", "/api/orioks/homework", {}, good, ADMIN)
check("без подтверждения не отправляет", s_ == 400 and not POSTED, (s_, POSTED))
s_, r_ = api.handle("POST", "/api/orioks/homework", {},
                    {**good, "km_id": 2080001, "confirm": True}, ADMIN)
check("мероприятие чужой дисциплины отклонено до ОРИОКС",
      s_ == 400 and not POSTED, (s_, r_))
s_, r_ = api.handle("POST", "/api/orioks/homework", {},
                    {**good, "message": "  ", "confirm": True}, ADMIN)
check("пустое описание отклонено", s_ == 400 and not POSTED, (s_, r_))
s_, r_ = api.handle("POST", "/api/orioks/homework", {},
                    {**good, "variant": "123456", "confirm": True}, ADMIN)
check("вариант длиннее пяти отклонён", s_ == 400 and not POSTED, (s_, r_))
s_, r_ = api.handle("POST", "/api/orioks/homework", {},
                    {**good, "confirm": True}, USER)
check("студент отправить не может", s_ == 404 and not POSTED, s_)

s_, r_ = api.handle("POST", "/api/orioks/homework", {},
                    {**good, "confirm": True}, ADMIN)
sent = POSTED[-1][2] if POSTED else {}
check("работа ушла", s_ == 200 and r_.get("ok") and len(POSTED) == 1, (s_, r_))
check("со свежим CSRF и под сессией владельца",
      sent.get("_csrf") == "CSRF-1" and POSTED[0][0] == "PHPSESSID=owner", POSTED)
check("поля формы названы как в ОРИОКС",
      sent.get("HomeworkTreadForm[id_km]") == "2071580"
      and sent.get("HomeworkTreadForm[message]") == "Готово, отчёт во вложении", sent)

# ОРИОКС вернул ту же форму с ошибкой — значит не принял.
HW["reply"] = ('<form><textarea name="HomeworkTreadForm[message]"></textarea>'
               '<p class="help-block help-block-error">Файл обязателен</p></form>',
               "https://orioks.miet.ru/student/homework/create?id_type=2")
s_, r_ = api.handle("POST", "/api/orioks/homework", {},
                    {**good, "confirm": True}, ADMIN)
check("отказ ОРИОКС показан его словами",
      s_ == 502 and r_["error"] == "Файл обязателен", (s_, r_))
orioks.forget(777)

# Подписка: по умолчанию включена, выключается своим маршрутом.
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
check("подписка включена по умолчанию", orioks_watch.notify_on(42))
check("подписчик виден обходу", 42 in orioks_watch.watchers(),
      orioks_watch.watchers())
api.handle("POST", "/api/admin/users/42/role", {},
           {"role": "none", "perms": [], "sections": []}, ADMIN)
check("закрыли раздел — сторож молчит", 42 not in orioks_watch.watchers(),
      orioks_watch.watchers())
check("а подключение осталось", orioks.token_of(42) != "")
s_, r_ = api.handle("POST", "/api/orioks/notify", {}, {"on": True}, USER)
check("закрытому раздел не отвечает", s_ == 403, s_)
api.handle("POST", "/api/admin/users/42/role", {},
           {"role": "none", "perms": [], "sections": ["orioks"]}, ADMIN)
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

# Заминка на странице уведомлений не должна уносить объявления
# дисциплин: они разные источники, и первый — главный.
NOTIFY_FAIL["how"] = "down"
orioks.forget_materials(42)
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
FEED["items"] = [news(41, "Задание к семинару")]
s_, r_ = api.handle("GET", "/api/orioks/news", {}, {}, USER)
check("объявления переживают отказ страницы уведомлений",
      s_ == 200 and len(r_.get("news") or []) == 1, (s_, r_))
NOTIFY_FAIL["how"] = None

# Показ «как это выглядит» отправляет сообщение, но память не трогает:
# иначе демонстрация обернулась бы пропущенной настоящей рассылкой.
orioks.save_token(777, "T" * 32)
orioks.save_cookie(777, "PHPSESSID=web-session-abc")
orioks.forget_materials(777)
FEED["items"] = [news(31, "Как это выглядит")]
orioks_watch.forget(777)
SENT.clear()
s_, r_ = api.handle("GET", "/api/admin/orioks-watch", {"demo": ["1"]}, {}, ADMIN)
check("показ отправляет сообщение",
      s_ == 200 and r_["sent"] and len(SENT) == 1, (s_, r_, SENT))
check("показ памяти не трогает", orioks_watch.seen_ids(777) == set(),
      orioks_watch.seen_ids(777))
orioks.forget(777)
SENT.clear()

# Сухой прогон ничего не помнит: иначе разведка «а что он сейчас видит»
# съедала бы настоящее уведомление — объявление помечено показанным, а
# показать его никто не показал.
api.handle("POST", "/api/orioks/link", {},
           {"login": "stud", "password": "secret"}, USER)
orioks_watch.forget(42)
FEED["items"] = [news(51, "Первое")]
orioks_watch.check_user(42)
FEED["items"] = [news(52, "Второе")] + FEED["items"]
SENT.clear()
dry = orioks_watch.check_user(42, send=False)
check("сухой прогон показывает новое", len(dry) == 1 and not SENT, (dry, SENT))
check("и ничего не запоминает",
      orioks_watch.seen_ids(42) == {"-", "51"}, orioks_watch.seen_ids(42))
check("после него уведомление доходит",
      len(orioks_watch.check_user(42)) == 1 and len(SENT) == 1, SENT)
SENT.clear()

# Утренняя карточка дня. Слать её можно только тому, кто попросил, —
# сообщение в половине восьмого утра вещь личная.
from . import morning, storage as _storage                        # noqa: E402
import datetime as _dt                                            # noqa: E402

check("по умолчанию карточка приходит", _storage.morning_on(42))
s_, r_ = api.handle("GET", "/api/me", {}, {}, USER)
check("признак виден приложению", r_.get("morning") is True, r_.get("morning"))

s_, r_ = api.handle("POST", "/api/morning", {}, {"on": False}, USER)
check("отказ принимается", s_ == 200 and r_["morning"] is False, (s_, r_))
check("и запомнился", not _storage.morning_on(42))
check("отказавшийся выпал из рассылки",
      all(row[0] != 42 for row in _storage.morning_list()),
      _storage.morning_list())
api.handle("POST", "/api/morning", {}, {"on": True}, USER)
check("и возвращается обратно", _storage.morning_on(42))

# Время: будим утром буднего дня и не будим ночью, поздно и в воскресенье.
check("в 7:30 понедельника пора",
      morning.time_to_send(_dt.datetime(2026, 9, 14, 7, 30)))
check("в 6 утра рано",
      not morning.time_to_send(_dt.datetime(2026, 9, 14, 6, 0)))
check("в 11 уже поздно",
      not morning.time_to_send(_dt.datetime(2026, 9, 14, 11, 0)))
check("в воскресенье молчим",
      not morning.time_to_send(_dt.datetime(2026, 9, 13, 8, 0)))

# Рассылка: кому ушло, кому нет и что именно.
SENT = []
_real_card = morning.card
morning.card = lambda group, uid, custom=True, webapp_url=None: (
    f"<h3>Доброе утро</h3><table><tr><td>{group}</td></tr></table>"
    f"<tg-button type=\"callback_data\" data=\"{morning.OFF_DATA}\">"
    f"Не присылать</tg-button>",
    f"Доброе утро, {group}")

storage.set_group(42, "ПИН-31")
day = _dt.datetime(2026, 9, 14, 7, 30)
sent = morning.send_all(lambda uid, html: SENT.append(("rich", uid, html)) or True,
                        lambda uid, text: SENT.append(("text", uid, text)) or True,
                        now=day)
check("карточка ушла, хотя никто не подписывался",
      sent >= 1 and any(row[1] == 42 for row in SENT), (sent, SENT))
check("ушла таблицей, а не текстом", SENT and SENT[0][0] == "rich", SENT)
check("в карточке есть кнопка отказа",
      SENT and morning.OFF_DATA in SENT[0][2], SENT[0][2][:80] if SENT else "")

SENT.clear()
check("второй раз за день не шлём",
      morning.send_all(lambda u, h: True, lambda u, t: True, now=day) == 0)

# Таблица не прошла — уходит обычным письмом.
_storage.morning_sent(42, "")
SENT.clear()
morning.send_all(lambda uid, html: False,
                 lambda uid, text: SENT.append(("text", uid, text)) or True,
                 now=day)
check("при отказе таблицы уходит письмо",
      SENT and SENT[0][0] == "text", SENT)

# Выходной или день без пар — молчим вовсе.
_storage.morning_sent(42, "")
morning.card = lambda group, uid, custom=True, webapp_url=None: None
SENT.clear()
check("в день без пар не пишем",
      morning.send_all(lambda u, h: True,
                       lambda u, t: SENT.append(t) or True, now=day) == 0
      and not SENT, SENT)
morning.card = _real_card

# Кнопка «Не присылать» отключает рассылку и больше её не шлёт.
_storage.set_morning(42, False)
check("после отказа список пуст для этого человека",
      all(row[0] != 42 for row in _storage.morning_list()))
_storage.morning_sent(42, "")
SENT.clear()
morning.send_all(lambda u, h: SENT.append(u) or True,
                 lambda u, t: SENT.append(u) or True, now=day)
check("отказавшемуся утром не пишут", 42 not in SENT, SENT)
_storage.set_morning(42, True)

# Раздача самого приложения: GitHub Pages у части операторов не
# открывается, и клиент уезжает с того же сервера, что и API.
got = api.static_file("/")
check("страница приложения отдаётся",
      bool(got) and got[0] == "index.html" and b"<!DOCTYPE html" in got[1],
      got[0] if got else None)
check("сборка отдаётся",
      (api.static_file("/js/bundle.js") or [None])[0] == "js/bundle.js")
check("шрифт отдаётся с нужным типом",
      (api.static_file("/fonts/manrope-700-cyrillic.woff2")
       or [None, None, None])[2] == "font/woff2")
for closed in ("/.env", "/bot/main.py", "/../.env", "/js/../../.env",
               "/tools/stamp.py", "/promo/post.md", "/bot/users.db"):
    check(f"наружу не уходит {closed}", api.static_file(closed) is None, closed)

# Предпросмотр утренней карточки: посмотреть на неё до 7:30.
storage.set_group(777, "ПИН-31")
morning.card = lambda group, uid, custom=True, webapp_url=None: (
    "<h3>Утро</h3>", "Утро, " + group)
s_, r_ = api.handle("GET", "/api/admin/day-preview",
                    {"group": ["ПИН-31"], "morning": ["1"]}, {}, ADMIN)
check("утренняя карточка показана",
      s_ == 200 and r_.get("morning") and "Утро" in r_["rich"], (s_, r_))
check("без просьбы не отправляется", r_.get("sent") is False, r_)
morning.card = lambda group, uid, custom=True, webapp_url=None: None
s_, r_ = api.handle("GET", "/api/admin/day-preview",
                    {"group": ["ПИН-31"], "morning": ["1"]}, {}, ADMIN)
check("в пустой день так и сказано", r_.get("empty") is True, r_)
morning.card = _real_card

# Разведка сторожа — только владельцу и только про него самого:
# чужие объявления не сторожит никто, и посмотреть на них тоже нельзя.
s_, r_ = api.handle("GET", "/api/admin/orioks-watch", {}, {}, USER)
check("разведка сторожа не для всех", s_ == 403, (s_, r_))
s_, r_ = api.handle("GET", "/api/admin/orioks-watch", {}, {}, ADMIN)
check("владельцу сторож отчитывается",
      s_ == 200 and "watchers" in r_ and r_["fresh"] == [], (s_, r_))

notify.bind(None)

print("\n15. Поломки на стороне клиента")
from . import oops                                                 # noqa: E402

# Одинаковые поломки складываются в одну строку со счётчиком: иначе
# первая же мелочь у двухсот человек вытеснит из таблицы всё остальное.
oops.forget()
oops.report(10, {"message": "Не удалось загрузить пост 412",
                 "source": "js/bundle.js", "line": 88, "screen": "news"})
r = oops.report(20, {"message": "Не удалось загрузить пост 987",
                     "source": "js/bundle.js", "line": 88, "screen": "news"})
check("номер в тексте не плодит записей", r["count"] == 2, r)
check("в списке одна строка", len(oops.recent()) == 1, oops.recent())
check("а случаев два", oops.totals()["total"] == 2, oops.totals())
oops.report(10, {"message": "Другая беда", "source": "js/bundle.js", "line": 5})
check("разные поломки — разные строки", oops.totals()["kinds"] == 2,
      oops.totals())
check("пустое сообщение не пишется",
      oops.report(10, {"message": "   "})["ok"] is False)
check("свежая сверху", oops.recent()[0]["message"] == "Другая беда",
      oops.recent()[0])

# Помним последнего, кто поймал, — чтобы было кого переспросить.
last = [e for e in oops.recent() if e["count"] == 2][0]
check("запомнен последний пойманный", last["user_id"] == 20, last)
check("экран записан", last["screen"] == "news", last)

s, r = api.handle("POST", "/api/oops", {},
                  {"message": "Экран tasks не открылся", "screen": "tasks",
                   "build": "abc123"}, USER)
check("клиент может сообщить о поломке", s == 200 and r["ok"], (s, r))
s, r = api.handle("GET", "/api/admin/oops", {}, {}, ADMIN)
check("владельцу список виден", s == 200 and r["totals"]["kinds"] == 3, r)
s, _ = api.handle("GET", "/api/admin/oops", {}, {}, USER)
check("постороннему — нет", s == 403, s)

gone = oops.recent()[0]["id"]
s, r = api.handle("POST", "/api/admin/oops", {}, {"id": gone}, ADMIN)
check("разобранное стирается", s == 200 and r["gone"] == 1, r)
s, r = api.handle("POST", "/api/admin/oops", {}, {}, ADMIN)
check("и всё разом тоже", s == 200 and oops.totals()["kinds"] == 0, r)

# Отчёт об ошибке не имеет права стать второй ошибкой.
check("кривые данные переживаются",
      oops.report(10, {"message": "Ок", "line": "не число"})["ok"] is True)
oops.forget()

print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
