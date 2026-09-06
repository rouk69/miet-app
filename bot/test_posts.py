# -*- coding: utf-8 -*-
"""
Проверки ленты: кто что видит, опросы, реакции, прочтения, модерация
анонимных постов и новости с miet.ru.

Главное здесь — видимость. Пост «только для этих групп» не должен
доезжать до чужого клиента ни в ленте, ни по прямой ссылке: спрятать
его в интерфейсе мало, ответ API читается и руками.

    python -m bot.test_posts
"""
from __future__ import annotations

import base64
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
os.environ["DATA_DIR"] = _dir       # картинки лягут во временную папку
db.reset_for_tests(os.path.join(_dir, "test-posts.db"))

from . import analytics, api, media, posts, storage                 # noqa: E402

media.paths.DATA_DIR = _dir

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


ADMIN = init_data(777, "Владелец", "byrouk")      # корневой админ
WRITER = init_data(10, "Староста", "starosta")    # получит право писать
PIN = init_data(20, "Студент ПИН", "pin31")       # группа ПИН-31
EN = init_data(30, "Студент ЭН", "en24")          # группа ЭН-24

# Группы приезжают из приложения вместе с событиями.
api.handle("POST", "/api/track", {}, {"group": "ПИН-31"}, PIN)
api.handle("POST", "/api/track", {}, {"group": "ЭН-24"}, EN)
api.handle("POST", "/api/track", {}, {"group": "ПИН-31"}, WRITER)
api.handle("GET", "/api/me", {}, {}, ADMIN)

print("1. Право писать выдаётся, а не берётся")
s, _ = api.handle("POST", "/api/posts", {}, {"text": "Проба"}, WRITER)
check("без права писать нельзя", s == 403, s)
api.handle("POST", "/api/admin/users/10/role", {},
           {"role": "moderator", "perms": ["posts_write"], "sections": []}, ADMIN)
s, me = api.handle("GET", "/api/me", {}, {}, WRITER)
check("право появилось", me["can_write"] and not me["can_anon"], me)
check("подпись автора — должность", me["label"] == "Модератор", me["label"])

print("\n2. Обычный пост виден всем")
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Завтра сбор в 10 у главного"}, WRITER)
check("пост создан", s == 200 and r["post"]["status"] == "published", (s, r))
open_id = r["post"]["id"]
s, f = api.handle("GET", "/api/feed", {}, {}, EN)
check("виден постороннему", any(p["id"] == open_id for p in f["posts"]), f["total"])
check("подписан должностью автора",
      f["posts"][0]["author_label"] == "Модератор", f["posts"][0])

print("\n3. Пост для выбранных групп")
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "ПИН-31, зачёт переносится", "groups": ["ПИН-31"]},
                  WRITER)
closed_id = r["post"]["id"]
check("аудитория записана", r["post"]["audience"] == "groups"
      and r["post"]["groups"] == ["ПИН-31"], r["post"])
s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
check("своей группе виден", any(p["id"] == closed_id for p in f["posts"]), f)
s, f = api.handle("GET", "/api/feed", {}, {}, EN)
check("чужой группе не виден", all(p["id"] != closed_id for p in f["posts"]), f)
s, _ = api.handle("GET", f"/api/posts/{closed_id}", {}, {}, EN)
check("и по прямой ссылке тоже", s == 404, s)
s, _ = api.handle("POST", f"/api/posts/{closed_id}/react", {}, {"emoji": "🔥"}, EN)
check("и реакцию чужой не поставит", s == 404, s)

print("\n4. Опрос")
s, r = api.handle("POST", "/api/posts", {}, {
    "text": "Завтра идёшь в вуз?", "options": ["Да", "Нет"]}, WRITER)
poll_id = r["post"]["id"]
check("опрос создан с вариантами", len(r["post"]["poll"]["options"]) == 2, r["post"])
s, _ = api.handle("POST", "/api/posts", {},
                  {"text": "Кривой опрос", "options": ["Только один"]}, WRITER)
check("один вариант отвергнут", s == 400, s)
opts = r["post"]["poll"]["options"]
api.handle("POST", f"/api/posts/{poll_id}/vote", {}, {"option": opts[0]["id"]}, PIN)
s, v = api.handle("POST", f"/api/posts/{poll_id}/vote", {},
                  {"option": opts[1]["id"]}, EN)
poll = v["post"]["poll"]
check("голоса посчитаны", poll["total"] == 2, poll)
check("доли посчитаны", {o["share"] for o in poll["options"]} == {50}, poll)
api.handle("POST", f"/api/posts/{poll_id}/vote", {}, {"option": opts[1]["id"]}, PIN)
s, v = api.handle("GET", f"/api/posts/{poll_id}", {}, {}, PIN)
check("переголосование заменяет голос, а не добавляет",
      v["poll"]["total"] == 2 and v["poll"]["my_option"] == opts[1]["id"], v["poll"])
s, _ = api.handle("POST", f"/api/posts/{poll_id}/vote", {}, {"option": 99999}, PIN)
check("чужой вариант не принимается", s == 400, s)

print("\n5. Реакции")
api.handle("POST", f"/api/posts/{open_id}/react", {}, {"emoji": "❤️"}, PIN)
s, r = api.handle("POST", f"/api/posts/{open_id}/react", {}, {"emoji": "❤️"}, EN)
check("реакции сложились",
      {x["emoji"]: x["count"] for x in r["post"]["reactions"]} == {"❤️": 2},
      r["post"]["reactions"])
s, r = api.handle("POST", f"/api/posts/{open_id}/react", {}, {"emoji": "🔥"}, PIN)
counts = {x["emoji"]: x["count"] for x in r["post"]["reactions"]}
check("новая реакция заменяет прежнюю", counts == {"❤️": 1, "🔥": 1}, counts)
s, r = api.handle("POST", f"/api/posts/{open_id}/react", {}, {"emoji": "🔥"}, PIN)
check("повторный тап снимает реакцию", r["my_reaction"] == "", r)
s, _ = api.handle("POST", f"/api/posts/{open_id}/react", {}, {"emoji": "🤡"}, PIN)
check("реакция не из набора отвергнута", s == 400, s)

print("\n6. Прочтения")
api.handle("POST", f"/api/posts/{open_id}/read", {}, {}, PIN)
api.handle("POST", f"/api/posts/{open_id}/read", {}, {}, PIN)
api.handle("POST", f"/api/posts/{open_id}/read", {}, {}, EN)
s, p = api.handle("GET", f"/api/posts/{open_id}", {}, {}, PIN)
check("считаются люди, а не открытия", p["reads"] == 2, p["reads"])
check("своё прочтение отмечено", p["read"] is True, p)

print("\n7. Анонимный пост ждёт одобрения")
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Аноним: в 3 корпусе не работает лифт", "anon": True},
                  WRITER)
anon_id = r["post"]["id"]
check("ушёл в очередь", r["pending"] and r["post"]["status"] == "pending", r)
s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
check("в ленте его пока нет", all(p["id"] != anon_id for p in f["posts"]), f)
s, mine = api.handle("GET", f"/api/posts/{anon_id}", {}, {}, WRITER)
check("автор свой пост видит", s == 200 and mine["status"] == "pending", s)
s, _ = api.handle("GET", "/api/admin/moderation", {}, {}, WRITER)
check("без права модерации очередь закрыта", s == 403, s)
s, q = api.handle("GET", "/api/admin/moderation", {}, {}, ADMIN)
check("владелец видит очередь", s == 200 and len(q["posts"]) == 1, q)
check("модератору виден настоящий автор", q["posts"][0]["author_id"] == 10, q["posts"][0])
s, _ = api.handle("POST", f"/api/admin/posts/{anon_id}/approve", {}, {}, ADMIN)
check("одобрение сработало", s == 200, s)
s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
shown = [p for p in f["posts"] if p["id"] == anon_id]
check("пост появился в ленте", len(shown) == 1, f["total"])
check("подпись — «Анонимно»", shown[0]["author_label"] == "Анонимно", shown[0])
check("автор наружу не отдан", shown[0]["author_id"] is None, shown[0])

print("\n8. Право публиковать анонимно без очереди")
api.handle("POST", "/api/admin/users/10/role", {},
           {"role": "moderator", "perms": ["posts_write", "posts_anon"],
            "sections": []}, ADMIN)
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Сразу анонимно", "anon": True}, WRITER)
check("публикуется сразу", r["post"]["status"] == "published", r["post"])
check("но подпись всё равно скрыта",
      r["post"]["author_label"] == "Анонимно", r["post"])

print("\n9. Отклонённый пост в ленту не попадает")
api.handle("POST", "/api/admin/users/10/role", {},
           {"role": "moderator", "perms": ["posts_write"], "sections": []}, ADMIN)
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Это отклонят", "anon": True}, WRITER)
bad_id = r["post"]["id"]
api.handle("POST", f"/api/admin/posts/{bad_id}/reject", {}, {}, ADMIN)
s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
check("отклонённого в ленте нет", all(p["id"] != bad_id for p in f["posts"]), f)

print("\n10. Картинки")
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "С картинкой",
                   "image": "data:image/png;base64," + base64.b64encode(PNG).decode()},
                  WRITER)
check("пост с картинкой создан", s == 200 and r["post"]["media"], r["post"])
name = r["post"]["media"]
blob, mime = media.read(name)
check("файл сохранён и читается", blob == PNG and mime == "image/png", mime)
check("имя файла — хеш содержимого", name.endswith(".png") and len(name) == 36, name)
check("тот же файл не дублируется", media.store(PNG) == name)
s, _ = api.handle("POST", "/api/posts", {},
                  {"text": "Не картинка",
                   "image": base64.b64encode(
                       "<html>вредное</html>".encode("utf-8")).decode()},
                  WRITER)
check("не-картинка отвергнута", s == 400, s)
check("выход за пределы хранилища закрыт",
      media.read("../users.db") == (None, None))
check("кривое имя не читается", media.read("не-хеш.png") == (None, None))

print("\n11. Удаление и закрепление")
s, r = api.handle("POST", "/api/posts", {}, {"text": "Временный"}, WRITER)
tmp_id = r["post"]["id"]
s, _ = api.handle("POST", f"/api/posts/{tmp_id}/delete", {}, {}, PIN)
check("чужой пост не удалить", s == 403, s)
s, _ = api.handle("POST", f"/api/posts/{tmp_id}/delete", {}, {}, WRITER)
check("свой пост автор удаляет сам", s == 200, s)
s, _ = api.handle("GET", f"/api/posts/{tmp_id}", {}, {}, PIN)
check("удалённого больше нет", s == 404, s)
s, _ = api.handle("POST", f"/api/posts/{open_id}/pin", {}, {"pinned": True}, PIN)
check("закреплять без права нельзя", s == 403, s)
api.handle("POST", "/api/admin/users/10/role", {},
           {"role": "moderator", "perms": ["posts_write", "posts_pin"],
            "sections": []}, ADMIN)
api.handle("POST", f"/api/posts/{open_id}/pin", {}, {"pinned": True}, WRITER)
s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
check("закреплённый сверху", f["posts"][0]["id"] == open_id, f["posts"][0]["id"])

print("\n12. Новости с miet.ru")
check("новость добавилась", posts.add_news("200399", "Конференция ППС", "",
                                           "https://www.miet.ru/news/200399"))
check("та же новость второй раз не добавится",
      not posts.add_news("200399", "Конференция ППС", "",
                         "https://www.miet.ru/news/200399"))
posts.update_news("200399", "Текст новости пришёл позже", "")
s, f = api.handle("GET", "/api/feed", {}, {}, EN)
news = [p for p in f["posts"] if p["kind"] == "news"]
check("новость в общей ленте", len(news) == 1, len(news))
check("текст дописался", news[0]["text"] == "Текст новости пришёл позже", news[0])
check("подписана университетом", news[0]["author_label"] == "МИЭТ", news[0])
posts.update_news("200399", "", "")
s, f = api.handle("GET", "/api/feed", {}, {}, EN)
check("пустое обновление не затирает текст",
      [p for p in f["posts"] if p["kind"] == "news"][0]["text"]
      == "Текст новости пришёл позже")

print("\n13. Блокировка закрывает ленту")
analytics.set_blocked(30, True)
s, _ = api.handle("GET", "/api/feed", {}, {}, EN)
check("заблокированному лента закрыта", s == 403, s)
s, _ = api.handle("POST", f"/api/posts/{open_id}/react", {}, {"emoji": "👍"}, EN)
check("и реакции тоже", s == 403, s)
analytics.set_blocked(30, False)
s, _ = api.handle("GET", "/api/feed", {}, {}, EN)
check("после разблокировки лента вернулась", s == 200, s)

print("\n14. Счётчики ленты в статистике")
s, st = api.handle("GET", "/api/admin/stats", {}, {}, ADMIN)
check("сводка по ленте есть", "feed" in st and st["feed"]["posts"] > 0, st.get("feed"))
check("отклонённые не считаются опубликованными",
      st["feed"]["pending"] == 0, st["feed"])

print("\n15. У владельца нет слепых зон")
# Владелец сидит без группы вовсе — и всё равно должен видеть адресные
# объявления: это его приложение, и лента в нём не должна ничего прятать.
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Только для ЭН-24", "groups": ["ЭН-24"]}, WRITER)
only_en = r["post"]["id"]

s, f = api.handle("GET", "/api/feed", {}, {}, ADMIN)
check("владелец видит чужое адресное объявление",
      any(p["id"] == only_en for p in f["posts"]), f["total"])
s, p_one = api.handle("GET", f"/api/posts/{only_en}", {}, {}, ADMIN)
check("и открывает его по ссылке", s == 200, s)
check("видно, кому оно адресовано", p_one["groups"] == ["ЭН-24"], p_one["groups"])
s, _ = api.handle("POST", f"/api/posts/{only_en}/react", {}, {"emoji": "👍"}, ADMIN)
check("и может поставить реакцию", s == 200, s)

s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
check("посторонней группе оно по-прежнему не видно",
      all(p["id"] != only_en for p in f["posts"]), f["total"])

# Права на анонимность это не расширяет: одно дело видеть все объявления,
# другое — знать, кто написал скрытно. Автора выдаёт только модерация.
api.handle("POST", "/api/admin/users/10/role", {},
           {"role": "moderator", "perms": ["posts_write"], "sections": []}, ADMIN)
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Скрытно и адресно", "anon": True,
                   "groups": ["ЭН-24"]}, WRITER)
hidden = r["post"]["id"]
api.handle("POST", f"/api/admin/posts/{hidden}/approve", {}, {}, ADMIN)
s, f = api.handle("GET", "/api/feed", {}, {}, ADMIN)
shown = [p for p in f["posts"] if p["id"] == hidden]
check("владелец видит и скрытный адресный пост", len(shown) == 1, f["total"])
check("но подпись остаётся «Анонимно»",
      shown[0]["author_label"] == "Анонимно", shown[0]["author_label"])


print("\n16. Комментарии")
from . import notify                                               # noqa: E402
from . import posts as posts_mod                                   # noqa: E402

# Паузу между комментариями на время проверки снимаем: она про живых
# людей, которые жмут кнопку дважды, а не про скорость тестов.
posts_mod.COMMENT_PAUSE = 0

s, r = api.handle("POST", "/api/posts", {}, {"text": "Пост под обсуждение"}, WRITER)
talk_id = r["post"]["id"]

s, c = api.handle("POST", f"/api/posts/{talk_id}/comments", {},
                  {"text": "А во сколько начало?"}, PIN)
check("комментарий добавлен", s == 200 and c["comment"]["text"] == "А во сколько начало?",
      (s, c))
check("подписан должностью", c["comment"]["author_label"] == "Студент",
      c["comment"]["author_label"])
check("и именем из Telegram", c["comment"]["author_name"] == "Студент ПИН",
      c["comment"]["author_name"])
check("счётчик в посте вырос", c["post"]["comments"] == 1, c["post"]["comments"])

api.handle("POST", f"/api/posts/{talk_id}/comments", {}, {"text": "В десять"}, EN)
s, lst = api.handle("GET", f"/api/posts/{talk_id}/comments", {}, {}, PIN)
check("список отдался по порядку",
      [x["text"] for x in lst["comments"]] == ["А во сколько начало?", "В десять"],
      lst["comments"])

s, _ = api.handle("POST", f"/api/posts/{talk_id}/comments", {}, {"text": "   "}, PIN)
check("пустой комментарий отвергнут", s == 400, s)

api.handle("POST", f"/api/posts/{talk_id}/comments", {}, {"text": "раз"}, PIN)
posts_mod.COMMENT_PAUSE = 5
s, _ = api.handle("POST", f"/api/posts/{talk_id}/comments", {}, {"text": "два"}, PIN)
check("очередь одинаковых сообщений придержана", s == 400, s)
posts_mod.COMMENT_PAUSE = 0

s, f = api.handle("GET", "/api/feed", {}, {}, PIN)
in_feed = [p for p in f["posts"] if p["id"] == talk_id][0]
check("счётчик виден в ленте", in_feed["comments"] == 3, in_feed["comments"])

print("\n17. Комментарии закрытого поста")
s, r = api.handle("POST", "/api/posts", {},
                  {"text": "Только ПИН-31", "groups": ["ПИН-31"]}, WRITER)
private_id = r["post"]["id"]
s, _ = api.handle("POST", f"/api/posts/{private_id}/comments", {},
                  {"text": "Я не из этой группы"}, EN)
check("чужой не прокомментирует", s == 404, s)
s, _ = api.handle("GET", f"/api/posts/{private_id}/comments", {}, {}, EN)
check("и комментариев не увидит", s == 404, s)
s, _ = api.handle("GET", f"/api/posts/{private_id}/comments", {}, {}, ADMIN)
check("владельцу видно и здесь", s == 200, s)

print("\n18. Уборка комментариев")
s, c = api.handle("POST", f"/api/posts/{talk_id}/comments", {},
                  {"text": "Удалю сам"}, EN)
mine_id = c["comment"]["id"]
s, _ = api.handle("POST", f"/api/comments/{mine_id}/delete", {}, {}, PIN)
check("чужой комментарий не удалить", s == 403, s)
s, _ = api.handle("POST", f"/api/comments/{mine_id}/delete", {}, {}, EN)
check("свой удаляется", s == 200, s)
check("и правда исчез", posts_mod.comment_one(mine_id) is None)

s, c = api.handle("POST", f"/api/posts/{talk_id}/comments", {},
                  {"text": "Уберёт модерация"}, EN)
bad_id = c["comment"]["id"]
api.handle("POST", "/api/admin/users/20/role", {},
           {"role": "moderator", "perms": ["comments_delete"], "sections": []}, ADMIN)
s, _ = api.handle("POST", f"/api/comments/{bad_id}/delete", {}, {}, PIN)
check("с правом удаляются чужие", s == 200, s)
api.handle("POST", "/api/admin/users/20/role", {},
           {"role": "none", "perms": [], "sections": []}, ADMIN)
s, _ = api.handle("POST", "/api/comments/999999/delete", {}, {}, ADMIN)
check("несуществующий — 404", s == 404, s)

print("\n19. Автору поста приходит письмо")
letters = []
notify.bind(lambda uid, text: letters.append((uid, text)))
api.handle("POST", f"/api/posts/{talk_id}/comments", {}, {"text": "Спасибо!"}, EN)
check("автор получил уведомление", letters and letters[0][0] == 10, letters[:1])
check("в письме видно, кто и что написал",
      letters and "Спасибо!" in letters[0][1] and "Студент ЭН" in letters[0][1],
      letters[:1])
letters.clear()
api.handle("POST", f"/api/posts/{talk_id}/comments", {}, {"text": "Сам себе"}, WRITER)
check("сам себе бот не пишет", not letters, letters)

# Имя из невидимых символов в Telegram не редкость: на боевом сервере
# подпись владельца показалась пустым местом. Пусто быть не должно.
analytics.touch({"id": 30, "first_name": chr(65039), "username": "en24"})
posts_mod.add_comment(talk_id, 30, "Кто я?")
check("невидимое имя заменяется ником",
      posts_mod.comments_of(talk_id)[-1]["author_name"] == "@en24",
      posts_mod.comments_of(talk_id)[-1]["author_name"])
check("без ника остаётся общее слово",
      posts_mod._display_name(chr(8203), "") == "Студент",
      posts_mod._display_name(chr(8203), ""))
letters.clear()
notify.bind(None)

s, r = api.handle("POST", "/api/posts", {}, {"text": "Пост на удаление"}, WRITER)
gone_id = r["post"]["id"]
api.handle("POST", f"/api/posts/{gone_id}/comments", {}, {"text": "останусь?"}, PIN)
api.handle("POST", f"/api/posts/{gone_id}/delete", {}, {}, WRITER)
check("вместе с постом уходят и комментарии",
      posts_mod.comments_of(gone_id) == [], posts_mod.comments_of(gone_id))


print("\n20. Ответы на комментарии")
posts_mod.COMMENT_PAUSE = 0
s, r = api.handle("POST", "/api/posts", {}, {"text": "Пост с веткой"}, WRITER)
tree_id = r["post"]["id"]

s, root = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                     {"text": "Когда сдавать?"}, PIN)
root_id = root["comment"]["id"]
check("корневой без родителя", root["comment"]["reply_to"] is None, root["comment"])

s, ans = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                    {"text": "До пятницы", "reply_to": root_id}, EN)
check("ответ привязан", ans["comment"]["reply_to"] == root_id, ans["comment"])

s, deep = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                     {"text": "Спасибо!", "reply_to": ans["comment"]["id"]}, PIN)
check("ответ на ответ прикреплён к тому же корню",
      deep["comment"]["reply_to"] == root_id, deep["comment"])

api.handle("POST", f"/api/posts/{tree_id}/comments", {}, {"text": "Ещё вопрос"}, EN)
s, lst = api.handle("GET", f"/api/posts/{tree_id}/comments", {}, {}, PIN)
check("порядок: корень, его ответы, следующий корень",
      [c["text"] for c in lst["comments"]]
      == ["Когда сдавать?", "До пятницы", "Спасибо!", "Ещё вопрос"],
      [c["text"] for c in lst["comments"]])

s, _ = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                  {"text": "Чужому посту", "reply_to": 999999}, PIN)
check("ответ несуществующему отвергнут", s == 400, s)
s, other_post = api.handle("POST", "/api/posts", {}, {"text": "Другой пост"}, WRITER)
s, _ = api.handle("POST", f"/api/posts/{other_post['post']['id']}/comments", {},
                  {"text": "Не отсюда", "reply_to": root_id}, PIN)
check("ответ на комментарий чужого поста отвергнут", s == 400, s)

api.handle("POST", f"/api/comments/{root_id}/delete", {}, {}, PIN)
s, lst = api.handle("GET", f"/api/posts/{tree_id}/comments", {}, {}, PIN)
check("вместе с корнем ушли и ответы",
      [c["text"] for c in lst["comments"]] == ["Ещё вопрос"],
      [c["text"] for c in lst["comments"]])

print("\n21. Кто написал — видно владельцу")
s, c = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                  {"text": "Найди меня"}, EN)
s, lst = api.handle("GET", f"/api/posts/{tree_id}/comments", {}, {}, ADMIN)
last = lst["comments"][-1]
check("владельцу приходит контакт", last.get("contact") == {"username": "en24", "id": 30},
      last.get("contact"))
check("и признак, что контакты доступны", lst["contacts"] is True, lst)

s, lst = api.handle("GET", f"/api/posts/{tree_id}/comments", {}, {}, PIN)
check("обычному человеку контактов не отдают",
      all("contact" not in c for c in lst["comments"]), lst["comments"][:1])
check("и признак выключен", lst["contacts"] is False, lst)

api.handle("POST", "/api/admin/users/20/role", {},
           {"role": "moderator", "perms": ["comments_delete"], "sections": []}, ADMIN)
s, lst = api.handle("GET", f"/api/posts/{tree_id}/comments", {}, {}, PIN)
check("тому, кто убирает комментарии, контакт нужен и приходит",
      lst["comments"][-1].get("contact", {}).get("username") == "en24",
      lst["comments"][-1].get("contact"))
api.handle("POST", "/api/admin/users/20/role", {},
           {"role": "none", "perms": [], "sections": []}, ADMIN)

print("\n22. Письмо тому, кому ответили")
letters2 = []
notify.bind(lambda uid, text: letters2.append((uid, text)))
s, base = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                     {"text": "Вопрос от ПИН"}, PIN)
letters2.clear()
api.handle("POST", f"/api/posts/{tree_id}/comments", {},
           {"text": "Отвечаю", "reply_to": base["comment"]["id"]}, EN)
who = {uid for uid, _ in letters2}
check("автор комментария получил письмо", 20 in who, who)
check("автор поста тоже", 10 in who, who)
check("писем ровно два", len(letters2) == 2, letters2)

letters2.clear()
# Автор поста отвечает сам себе на свой же комментарий — писем быть не должно.
s, own = api.handle("POST", f"/api/posts/{tree_id}/comments", {},
                    {"text": "Своё"}, WRITER)
letters2.clear()
api.handle("POST", f"/api/posts/{tree_id}/comments", {},
           {"text": "И ответ себе", "reply_to": own["comment"]["id"]}, WRITER)
check("сам себе писем не шлём", not letters2, letters2)
notify.bind(None)


print("\n" + "=" * 58)
print(f"пройдено {ok}, провалено {fail}")
print("=" * 58)
sys.exit(1 if fail else 0)
