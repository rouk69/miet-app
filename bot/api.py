# -*- coding: utf-8 -*-
"""
HTTP-API мини-приложения: приём событий и всё, что показывает админка.

Живёт внутри процесса бота отдельным потоком. Отдельный сервис не заводим
намеренно: данные у них общие (одна SQLite в DATA_DIR), а два процесса,
пишущих в одну базу на сетевом томе, — это блокировки на ровном месте.

Кто ты — решает подпись Telegram, а не наше слово. Каждый запрос из
приложения несёт заголовок X-Init-Data (строка Telegram.WebApp.initData),
она проверяется HMAC на токене бота (bot/auth.py). Ни кук, ни сессий,
ни собственных токенов здесь нет: подделать initData без токена бота
нельзя, а срок жизни у неё ограничен.

Права проверяются ТОЛЬКО здесь. Мини-приложение прячет кнопку админки,
но это украшение: любой может открыть её вручную, поэтому каждый
admin-маршрут сам спрашивает роль.
"""
from __future__ import annotations

import base64
import binascii
import gzip
import json
import logging
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import analytics, appconf, auth, directory, help_board, notify
from . import orioks, orioks_watch, orioks_web, posts
from . import paths, render, storage
from . import rich
from . import schedule_api as schedule
from . import media as mediastore

log = logging.getLogger("miet.api")

# Amvera пускает наружу только 80-й порт — там домен проекта и заканчивается.
# Локально его слушать нельзя без прав администратора, поэтому при отладке
# порт переопределяется переменной PORT (см. .env.example).
PORT = int(os.environ.get("PORT") or 80)

# Откуда разрешено обращаться. По умолчанию любой источник: личных данных
# API не отдаёт никому, кроме владельца подписанной initData, а мини-апп
# может открываться и с github.io, и с локального сервера при отладке.
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "*").strip() or "*"

# Обычный запрос — это несколько сотен байт JSON. Крупное тело бывает
# ровно в одном месте: пост с картинкой, приезжающей строкой base64
# (плюс треть объёма на кодирование к пяти мегабайтам файла).
MAX_BODY = 64 * 1024
MAX_BODY_UPLOAD = 8 * 1024 * 1024
UPLOAD_PATHS = ("/api/posts",)


def admin_ids() -> set:
    """
    Корневые админы из переменной окружения: ADMIN_IDS=123,456.

    Читается на каждый запрос, а не один раз при импорте, — чтобы правка
    переменной в панели Amvera подхватывалась перезапуском контейнера, а в
    тестах её можно было подменить без перезагрузки модуля.
    """
    out = set()
    for chunk in re.split(r"[,\s]+", os.environ.get("ADMIN_IDS", "")):
        if chunk.strip().lstrip("-").isdigit():
            out.add(int(chunk))
    return out


# ─────────────────────────── маршруты ───────────────────────────

def _actor(init_data: str):
    """Возвращает (профиль Telegram, права) или None, если подпись не сошлась."""
    token = os.environ.get("BOT_TOKEN", "").strip()
    user = auth.validate_init_data(init_data, token)
    if not user:
        return None
    return user, analytics.identity(int(user.get("id") or 0), admin_ids())


def handle(method: str, path: str, query: dict, body: dict, init_data: str):
    """
    Разбор запроса без единого обращения к сокету — чтобы то же самое можно
    было прогнать в тестах, не поднимая сервер и не ходя через localhost
    (на машине автора он завёрнут в системный прокси и отвечает 502).

    Возвращает (код ответа, объект для JSON).
    """
    if path == "/api/health":
        # Заодно версия клиента, которую знает бот: по ней видно, дошла
        # ли выкладка до контейнера, — иначе это выясняется только по
        # адресу кнопки меню, то есть через Telegram.
        return 200, {"ok": True, "webapp": paths.webapp_version()}

    who = _actor(init_data)
    if not who:
        return 401, {"error": "Подпись Telegram не сошлась"}
    user, me = who
    uid = int(user["id"])

    if path == "/api/me" and method == "GET":
        return 200, _me(user, me)

    if path == "/api/track" and method == "POST":
        return _track(user, me, body)

    if path.startswith("/api/directory/") and method == "GET":
        return _directory(path, query)

    if path.startswith("/api/orioks"):
        return _orioks(path, method, body, uid, me)

    if path == "/api/help" or path.startswith("/api/help/"):
        if method == "POST" and not me["blocked"]:
            analytics.touch(user, source="app")
        return _help(path, method, query, body, uid, me)

    if path.startswith("/api/admin/"):
        return _admin(path, method, query, body, uid, me)

    if (path == "/api/feed" or path.startswith("/api/posts")
            or path.startswith("/api/comments")):
        # Всё, что человек оставляет после себя, подписано им: профиль
        # должен быть в базе до того, как понадобится. Раньше он попадал
        # туда только вместе с событиями, и у автора комментария, чей
        # клиент не успел их отправить, не было даже ника.
        if method == "POST" and not me["blocked"]:
            analytics.touch(user, source="app")
        return _feed(path, method, query, body, uid, me)

    return 404, {"error": "Нет такого маршрута"}


def _me(user: dict, me: dict) -> dict:
    saved = storage.get_user(int(user["id"]))
    return {
        "id": me["id"],
        "role": me["role"],
        "perms": me["perms"],
        "sections": me["sections"],
        "blocked": me["blocked"],
        "is_admin": me["is_admin"],
        "can_stats": analytics.can(me, "stats"),
        # Право писать даёт либо выданное разрешение, либо режим
        # «писать могут все», включённый владельцем.
        "can_write": _may_write(me),
        "premoderate": _waits_approval(me),
        "can_moderate": analytics.can(me, "posts_moderate"),
        "can_anon": analytics.can(me, "posts_anon"),
        "can_delete": analytics.can(me, "posts_delete"),
        "can_pin": analytics.can(me, "posts_pin"),
        "can_clean_comments": analytics.can(me, "comments_delete"),
        "orioks": bool(orioks.token_of(me["id"])),
        "label": _label(me),
        # Группа с сервера: человек выбрал её в боте — приложение подхватит
        # её на другом устройстве, и наоборот.
        "group": saved.get("group"),
    }


def _may_write(me: dict) -> bool:
    return analytics.can(me, "posts_write") or appconf.get("posts_open")


def _waits_approval(me: dict) -> bool:
    """
    Пойдёт ли пост этого человека в очередь.

    Режим премодерации не распространяется на тех, кто сам разбирает
    очередь: отправлять пост на одобрение самому себе бессмысленно, а
    очередь из собственных записей мешает увидеть чужие.
    """
    return (appconf.get("posts_premoderate")
            and not analytics.can(me, "posts_moderate"))


def _label(me: dict) -> str:
    """Как подписывается автор поста: должностью, а не именем."""
    if me["root"]:
        return "Владелец"
    if me["is_admin"]:
        return "Админ"
    if me["role"] == "moderator":
        return "Модератор"
    return "Студент"


def _directory(path: str, query: dict):
    """
    Справочник преподавателей и аудиторий. Открыт всем, кто вошёл: это
    то же расписание, что и так лежит на miet.ru, только повёрнутое
    другой стороной.
    """
    q = (query.get("q", [""])[0] or "").strip()
    name = (query.get("name", [""])[0] or "").strip()

    if path == "/api/directory/teachers":
        return 200, {"teachers": directory.teachers(q), "meta": directory.meta()}

    if path == "/api/directory/teacher" and name:
        found = directory.teacher_schedule(name)
        if not found["slots"]:
            return 404, {"error": "Такого преподавателя в расписании нет"}
        return 200, found

    if path == "/api/directory/rooms":
        return 200, {"rooms": directory.rooms(q), "meta": directory.meta()}

    if path == "/api/directory/room" and name:
        found = directory.room_schedule(name)
        if not found["slots"]:
            return 404, {"error": "Такой аудитории в расписании нет"}
        return 200, found

    return 404, {"error": "Нет такого маршрута"}


def _orioks(path: str, method: str, body: dict, uid: int, me: dict):
    """
    Личное подключение к ОРИОКС: задания, сроки и баллы.

    Данные здесь строго свои: токен привязан к человеку, и чужие задания
    получить нельзя даже владельцу — в ОРИОКС ходим под токеном того, кто
    спрашивает, и ничьим больше.
    """
    if me["blocked"]:
        return 403, {"error": "Доступ закрыт"}

    if path == "/api/orioks" and method == "GET":
        token = orioks.token_of(uid)
        if not token:
            return 200, {"linked": False}
        watch = orioks_watch.notify_on(uid)
        try:
            return 200, {"linked": True, "notify": watch,
                         "tasks": orioks.with_materials(uid, orioks.tasks(token))}
        except orioks.OrioksError as e:
            # Токен мог протухнуть или быть отозван — тогда честнее
            # предложить подключиться заново, чем показывать ошибку.
            return 200, {"linked": True, "notify": watch, "error": str(e)}

    if path == "/api/orioks/link" and method == "POST":
        login = (body.get("login") or "").strip()
        password = body.get("password") or ""
        if not login or not password:
            return 400, {"error": "Нужны логин и пароль от ОРИОКС"}
        try:
            token = orioks.get_token(login, password)
        except orioks.OrioksError as e:
            return 400, {"error": str(e)}
        orioks.save_token(uid, token)
        # Второй вход — в веб-версию: текст домашнего задания есть только
        # там, API отдаёт голое название. Не вышло — не беда, задания
        # покажутся без текста, поэтому подключение из-за этого не рвём.
        try:
            orioks.save_cookie(uid, orioks_web.sign_in_cookie(login, password))
        except orioks_web.WebError as e:
            log.info("веб-версия ОРИОКС не пустила: %s", e)
        # Пароль дальше этой строки не идёт: в базе только токен и cookie.
        del password
        try:
            return 200, {"ok": True, "linked": True,
                         "tasks": orioks.with_materials(uid, orioks.tasks(token))}
        except orioks.OrioksError as e:
            return 200, {"ok": True, "linked": True, "error": str(e)}

    if path == "/api/orioks/news":
        # Объявления преподавателей — то, что студент и называет
        # домашним заданием. Ходим под сессией того, кто спрашивает:
        # чужие объявления недоступны никому, включая владельца.
        cookie = orioks.cookie_of(uid)
        if not cookie:
            return 200, {"web": False, "news": []}
        item = (body.get("item") or "").strip()
        try:
            if item:
                return 200, {"web": True,
                             "item": orioks_web.news_item(cookie, item)}
            return 200, {"web": True, "news": orioks.announcements(uid)}
        except orioks_web.SessionExpired:
            orioks.drop_cookie(uid)
            return 200, {"web": False, "news": [],
                         "error": "Доступ к сайту ОРИОКС кончился — "
                                  "подключи его заново"}
        except orioks_web.WebError as e:
            return 200, {"web": True, "news": [], "error": str(e)}

    if path == "/api/orioks/notify" and method == "POST":
        # Подписка на объявления преподавателей. Отдельным маршрутом, а
        # не полем настроек: она про чужой сервис и живёт рядом с
        # доступом к нему — отключил ОРИОКС, и подписка ушла с ним.
        if not orioks.token_of(uid):
            return 400, {"error": "ОРИОКС не подключён"}
        on = bool(body.get("on"))
        orioks_watch.set_notify(uid, on)
        return 200, {"ok": True, "notify": on}

    if path == "/api/orioks/raw" and method == "GET":
        # Свои же данные в сыром виде: нужно, когда экран показывает
        # непонятное и надо увидеть, что на самом деле прислал ОРИОКС.
        token = orioks.token_of(uid)
        if not token:
            return 400, {"error": "ОРИОКС не подключён"}
        return 200, orioks.raw_dump(token)

    if path == "/api/orioks/unlink" and method == "POST":
        token = orioks.token_of(uid)
        if token:
            orioks.revoke(token)
        orioks.forget(uid)
        orioks.forget_materials(uid)
        # Память о показанных объявлениях уходит вместе с доступом:
        # держать её после отключения не за чем, а при следующем
        # подключении она бы молча съела первую рассылку.
        orioks_watch.forget(uid)
        return 200, {"ok": True, "linked": False}

    return 404, {"error": "Нет такого маршрута"}


HELP_PATH = re.compile(r"^/api/help/(\d+)/(close|reopen|delete)$")


def _help(path: str, method: str, query: dict, body: dict, uid: int, me: dict):
    """Доска взаимопомощи. Читают все вошедшие, пишут тоже — это её смысл."""
    if me["blocked"]:
        return 403, {"error": "Доступ закрыт"}
    manager = analytics.can(me, "help_manage")

    if path == "/api/help" and method == "GET":
        out = help_board.board(kind=(query.get("kind", [""])[0] or ""),
                               q=(query.get("q", [""])[0] or "").strip())
        out["mine"] = help_board.mine(uid)
        out["can_manage"] = manager
        return 200, out

    if path == "/api/help" and method == "POST":
        try:
            offer = help_board.create(
                uid, body.get("kind") or "need", body.get("subject") or "",
                body.get("text") or "", body.get("price") or "free")
        except help_board.Refused as e:
            return 400, {"error": str(e)}
        return 200, {"ok": True, "offer": offer}

    m = HELP_PATH.match(path)
    if m and method == "POST":
        offer_id, what = int(m.group(1)), m.group(2)
        offer = help_board.one(offer_id)
        if not offer:
            return 404, {"error": "Объявление не найдено"}
        # Своё объявление человек ведёт сам: закрыть, открыть заново,
        # убрать. Чужие — только тот, кому выдана уборка раздела.
        if offer["author_id"] != uid and not manager:
            return 403, {"error": "Это чужое объявление"}
        if what == "close":
            help_board.close(offer_id)
        elif what == "reopen":
            help_board.reopen(offer_id)
        else:
            help_board.delete(offer_id)
        return 200, {"ok": True}

    return 404, {"error": "Нет такого маршрута"}


def _track(user: dict, me: dict, body: dict):
    """Приём событий из приложения. Заблокированным ничего не пишем."""
    if me["blocked"]:
        return 403, {"error": "Доступ закрыт"}
    analytics.touch(user, source="app")
    uid = int(user["id"])

    group = (body.get("group") or "").strip()
    if group:
        storage.set_group(uid, group, user.get("username"))

    events = body.get("events")
    if isinstance(events, list):
        # Пачку ограничиваем: подписанная initData живёт сутки, и без
        # потолка ею можно было бы залить базу событиями за один запрос.
        batch = [(ev.get("kind"), ev.get("name") or "")
                 for ev in events[:50]
                 if isinstance(ev, dict)
                 and ev.get("kind") in ("open", "tab", "screen")]
        analytics.note_many(uid, batch)
    return 200, {"ok": True}


POST_PATH = re.compile(
    r"^/api/posts/(\d+)(/read|/react|/vote|/pin|/delete|/comments)?$")
COMMENT_PATH = re.compile(r"^/api/comments/(\d+)/delete$")


def _feed(path: str, method: str, query: dict, body: dict, uid: int, me: dict):
    """Лента и всё, что с постами делают: чтение, реакции, голоса, правка."""
    if me["blocked"]:
        return 403, {"error": "Доступ закрыт"}
    group = storage.get_user(uid).get("group") or ""
    # Автор анонимного поста виден только тем, кто разбирает жалобы.
    deep = analytics.can(me, "posts_moderate")
    # Полный админ видит ленту целиком, включая адресные объявления чужим
    # группам: это его приложение, и слепых зон в нём быть не должно.
    # Права на чужую анонимность это по-прежнему не даёт — она отдельно.
    everything = me["is_admin"]

    if path == "/api/feed" and method == "GET":
        return 200, posts.feed(
            uid, group,
            limit=int(query.get("limit", ["20"])[0] or 20),
            offset=int(query.get("offset", ["0"])[0] or 0),
            can_see_authors=deep, see_all=everything)

    if path == "/api/posts" and method == "POST":
        if not _may_write(me):
            return 403, {"error": "Нет права писать посты"}
        media = ""
        if body.get("image"):
            try:
                media = _save_image(body["image"])
            except ValueError as e:
                return 400, {"error": str(e)}
        try:
            post = posts.create(
                uid,
                body.get("text") or "",
                title=body.get("title") or "",
                groups=body.get("groups") or [],
                options=body.get("options") or [],
                anon=bool(body.get("anon")),
                media=media,
                author_label=_label(me),
                may_publish_anon=analytics.can(me, "posts_anon"),
                premoderate=_waits_approval(me))
        except posts.Refused as e:
            return 400, {"error": str(e)}
        return 200, {"ok": True, "post": post,
                     "pending": post["status"] == "pending"}

    m = COMMENT_PATH.match(path)
    if m and method == "POST":
        return _delete_comment(int(m.group(1)), uid, me)

    m = POST_PATH.match(path)
    if not m:
        return 404, {"error": "Нет такого маршрута"}
    post_id, tail = int(m.group(1)), m.group(2)

    # Видимость проверяется до всего остального: закрытый пост нельзя ни
    # прочитать, ни отметить реакцией, ни проголосовать в нём.
    #
    # Послабление только для уборки и закрепления: записи со статусом
    # pending и rejected обычную проверку не проходят, и без этого мусор
    # из очереди нельзя было даже удалить — отклонить можно, а
    # отклонённое лежало в базе вечно. На чтение это не распространяется:
    # иначе модератор получил бы доступ к адресным постам чужих групп,
    # которых он видеть не должен.
    keeper = (tail in ("/delete", "/pin")
              and (analytics.can(me, "posts_moderate")
                   or analytics.can(me, "posts_delete")
                   or analytics.can(me, "posts_pin")))
    post = posts.one(post_id, uid, group, can_see_authors=deep,
                     see_all=everything, force=keeper)
    if not post:
        return 404, {"error": "Пост не найден"}

    if tail is None and method == "GET":
        return 200, post

    if tail == "/read" and method == "POST":
        posts.mark_read(post_id, uid)
        return 200, {"ok": True}

    if tail == "/react" and method == "POST":
        try:
            now = posts.react(post_id, uid, body.get("emoji") or "")
        except posts.Refused as e:
            return 400, {"error": str(e)}
        return 200, {"ok": True, "my_reaction": now,
                     "post": posts.one(post_id, uid, group, can_see_authors=deep, see_all=everything)}

    if tail == "/vote" and method == "POST":
        try:
            posts.vote(post_id, uid, int(body.get("option") or 0))
        except (posts.Refused, ValueError, TypeError) as e:
            return 400, {"error": str(e) or "Неверный вариант"}
        return 200, {"ok": True,
                     "post": posts.one(post_id, uid, group, can_see_authors=deep, see_all=everything)}

    if tail == "/comments":
        # Комментировать может любой, кто видит пост: право на чтение и
        # право на голос здесь одно и то же. Заблокированные отсечены выше.
        # Ник автора комментария — для связи, когда нужно разобраться:
        # владельцу и тем, кому выдана уборка комментариев.
        contacts = me["is_admin"] or analytics.can(me, "comments_delete")
        if method == "GET":
            return 200, {"comments": posts.comments_of(post_id,
                                                       with_contacts=contacts),
                         "can_moderate": analytics.can(me, "comments_delete"),
                         "contacts": contacts}
        if method == "POST":
            try:
                comment = posts.add_comment(post_id, uid, body.get("text") or "",
                                            author_label=_label(me),
                                            reply_to=body.get("reply_to"))
            except posts.Refused as e:
                return 400, {"error": str(e)}
            # Если автор поста и автор комментария, на который отвечают,
            # — один человек, письмо должно уйти одно.
            _tell_author(post, comment, skip=_tell_parent(comment))
            return 200, {"ok": True, "comment": comment,
                         "post": posts.one(post_id, uid, group,
                                           can_see_authors=deep,
                                           see_all=everything)}

    if tail == "/pin" and method == "POST":
        if not analytics.can(me, "posts_pin"):
            return 403, {"error": "Нет права закреплять посты"}
        posts.set_pinned(post_id, bool(body.get("pinned")))
        return 200, {"ok": True, "pinned": bool(body.get("pinned"))}

    if tail == "/delete" and method == "POST":
        # Свой пост человек убирает сам — это не модерация, а право на своё.
        if not (post["mine"] or analytics.can(me, "posts_delete")):
            return 403, {"error": "Нет права удалять посты"}
        media = post.get("media")
        posts.delete(post_id)
        if media:
            mediastore.forget(media)
        return 200, {"ok": True}

    return 404, {"error": "Нет такого маршрута"}


def _delete_comment(comment_id: int, uid: int, me: dict):
    """Свой комментарий убирает автор, чужие — тот, кому выдано право."""
    comment = posts.comment_one(comment_id)
    if not comment:
        return 404, {"error": "Комментарий не найден"}
    if comment["author_id"] != uid and not analytics.can(me, "comments_delete"):
        return 403, {"error": "Нет права удалять комментарии"}
    posts.delete_comment(comment_id)
    return 200, {"ok": True}


def _tell_author(post: dict, comment: dict, skip=frozenset()) -> None:
    """
    Сообщает автору поста, что его прокомментировали.

    Себе не пишем, новостям с сайта писать некому, а у анонимного поста
    автор известен серверу — он и получит письмо: скрыт он от читателей,
    а не от собственного приложения.
    """
    author = post.get("author_id")
    if not author or author == comment["author_id"] or author in skip:
        return
    head = (post.get("title") or post.get("text") or "").strip()
    notify.to_user(author,
                   "💬 <b>Новый комментарий</b>\n\n"
                   f"{render.esc(comment['author_name'])}: "
                   f"{render.esc(comment['text'][:300])}\n\n"
                   f"К записи: {render.esc(head[:120]) or 'без заголовка'}")


def _tell_parent(comment: dict) -> set:
    """Сообщает человеку, что ему ответили. Возвращает, кому написали."""
    if not comment.get("reply_to"):
        return set()
    parent = posts.comment_one(comment["reply_to"])
    if not parent or parent["author_id"] == comment["author_id"]:
        return set()
    notify.to_user(parent["author_id"],
                   "↩️ <b>Вам ответили</b>\n\n"
                   f"{render.esc(comment['author_name'])}: "
                   f"{render.esc(comment['text'][:300])}\n\n"
                   f"На ваш комментарий: {render.esc(parent['text'][:120])}")
    return {parent["author_id"]}


def _save_image(raw: str) -> str:
    """
    Принимает картинку строкой base64 (с префиксом data: или без).

    Не multipart намеренно: разбор multipart в http.server пришлось бы
    писать руками, а весь остальной API говорит на JSON. Плата — треть
    лишнего объёма на кодирование, и она учтена в лимите.
    """
    payload = raw.split(",", 1)[1] if raw.startswith("data:") else raw
    if len(payload) > mediastore.MAX_BYTES * 4 // 3 + 1024:
        raise ValueError("Файл слишком большой")
    try:
        blob = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("Картинка не разобралась")
    return mediastore.store(blob)


USER_PATH = re.compile(r"^/api/admin/users/(\d+)(/role|/block)?$")
MOD_PATH = re.compile(r"^/api/admin/posts/(\d+)/(approve|reject)$")


def _moderation(path: str, method: str, body: dict, uid: int, me: dict):
    """Очередь анонимных постов: одобрить или отклонить."""
    if not analytics.can(me, "posts_moderate"):
        return 403, {"error": "Нет права одобрять посты"}

    if path == "/api/admin/moderation" and method == "GET":
        return 200, {"posts": posts.pending(uid)}

    m = MOD_PATH.match(path)
    if m and method == "POST":
        post_id, what = int(m.group(1)), m.group(2)
        post = posts.one(post_id, uid, force=True, can_see_authors=True)
        if not post:
            return 404, {"error": "Пост не найден"}
        posts.set_status(post_id, "published" if what == "approve" else "rejected")
        return 200, {"ok": True, "status": "published" if what == "approve"
                     else "rejected"}

    return 404, {"error": "Нет такого маршрута"}


def _admin(path: str, method: str, query: dict, body: dict, uid: int, me: dict):
    # Модерация — единственная часть админки, доступная без права на
    # статистику: одобрять посты и смотреть, кто чем пользуется, — разные
    # занятия, и выдаются они порознь.
    if path.startswith("/api/admin/posts") or path == "/api/admin/moderation":
        return _moderation(path, method, body, uid, me)

    if not analytics.can(me, "stats"):
        return 403, {"error": "Нет доступа"}

    if path == "/api/admin/stats" and method == "GET":
        days = min(60, max(7, int(query.get("days", ["14"])[0] or 14)))
        out = analytics.overview(days)
        out["feed"] = posts.stats()
        out["help"] = help_board.stats()
        out["hours"] = analytics.by_hours(days)
        out["weekdays"] = analytics.by_weekday()
        return 200, out

    if path == "/api/admin/settings":
        if method == "GET":
            return 200, {"flags": appconf.described()}
        if method == "POST":
            if not me["is_admin"]:
                return 403, {"error": "Настройки меняет только полный админ"}
            key = str(body.get("key") or "")
            try:
                appconf.set_flag(key, bool(body.get("value")))
            except KeyError:
                return 400, {"error": "Неизвестная настройка"}
            return 200, {"ok": True, "flags": appconf.described()}

    if path == "/api/admin/orioks-web" and method == "GET":
        # Как устроена форма входа веб-версии: имена полей и адрес
        # отправки. Пароль для этого не нужен.
        try:
            return 200, orioks_web.login_form()
        except orioks_web.WebError as e:
            return 200, {"error": str(e)}

    if path == "/api/admin/orioks-web-dump" and method == "GET":
        # Что лежит в личном кабинете: нужно один раз, чтобы понять, на
        # какой странице живёт текст задания. Ходим ТОЛЬКО под своей
        # сессией — сессия владельца открывает кабинет владельца, чужие
        # кабинеты сюда не попадают ни при каких правах.
        cookie = orioks.cookie_of(me["id"])
        if not cookie:
            return 200, {"error": "Сессия веб-версии не сохранена — "
                                  "переподключи ОРИОКС в разделе заданий"}
        page = (query.get("page", [""])[0] or "").strip()
        try:
            if query.get("try"):
                # Проверка догадок разом: какой из адресов вообще
                # отвечает под нашей сессией.
                out = {}
                for guess in (query.get("try", [""])[0] or "").split(","):
                    guess = guess.strip()
                    if not guess.startswith("/"):
                        continue
                    try:
                        html = orioks_web.get_page(cookie, guess)
                        out[guess] = {"ok": True,
                                      "title": orioks_web._title(html),
                                      "строк": len(orioks_web.re.findall(
                                          r"(?i)<tr[\s>]", html))}
                    except orioks_web.WebError as e:
                        out[guess] = {"ok": False, "ошибка": str(e)}
                return 200, out
            find = (query.get("find", [""])[0] or "").strip()
            if find:
                return 200, orioks_web.find_in(
                    cookie, page or "/", find)
            if query.get("form"):
                # Поля фильтра: пустая таблица — это либо «данных нет»,
                # либо «фильтр их прячет», и различить можно только так.
                return 200, orioks_web.form_fields(
                    cookie, page or "/student/homework/list")
            if query.get("urls"):
                # Куда ходит сам кабинет: адреса источников данных лежат
                # в его скриптах, а не в разметке.
                return 200, orioks_web.endpoints(
                    cookie, page or orioks_web.STUDY_PATH)
            if query.get("study"):
                # Сводка по данным учёбы: что из полей веб-версии
                # заполнено на живом аккаунте, а что пустое всегда.
                return 200, orioks_web.study_report(
                    orioks_web.study_json(cookie))
            if page:
                # Одна конкретная страница целиком: обход по ссылкам
                # показывает, что раздел есть, а разбирать приходится
                # уже его содержимое.
                if not page.startswith("/"):
                    return 400, {"error": "Адрес должен начинаться с /"}
                html = orioks_web.get_page(cookie, page)
                return 200, {"href": page, "title": orioks_web._title(html),
                             "text": orioks_web.text_of(html)[:6000],
                             "links": [{"href": h, "text": t}
                                       for h, t in orioks_web._links(html)[:80]]}
            return 200, orioks_web.explore(cookie)
        except orioks_web.WebError as e:
            return 200, {"error": str(e)}

    if path == "/api/admin/orioks-watch" and method == "GET":
        # Сторож объявлений вживую: что он видит и что бы отправил.
        # Нужно потому, что иначе проверить его можно только подождав
        # полтора часа и понадеявшись, что преподаватель как раз написал.
        # Ходим ТОЛЬКО под своей сессией — как и вся разведка ОРИОКС.
        if query.get("demo"):
            # «Покажи, как это выглядит»: собираем сообщение из того, что
            # уже известно, и отправляем. Память при этом не трогаем —
            # иначе показ обернулся бы повтором настоящей рассылки.
            shown = orioks.announcements(me["id"])[:1]
            body = orioks_watch.message(shown) if shown else ""
            if body:
                notify.to_user(me["id"], body)
            return 200, {"demo": True, "sent": bool(body), "preview": body}

        send = bool(query.get("send"))
        known = len(orioks_watch.seen_ids(me["id"]))
        fresh = orioks_watch.check_user(me["id"], send=send)
        return 200, {
            "known_before": known,
            "notify": orioks_watch.notify_on(me["id"]),
            "daytime": orioks_watch.daytime(),
            "watchers": len(orioks_watch.watchers()),
            "sent": send and bool(fresh),
            "fresh": [{"discipline": n.get("discipline"),
                       "title": n.get("title"),
                       "date": n.get("date")} for n in fresh],
            "preview": orioks_watch.message(fresh) if fresh else "",
        }

    if path == "/api/admin/day-preview" and method == "GET":
        # Что бот показывает на самом деле. Проверить рендер иначе можно
        # только написав боту и посмотрев глазами — а половина правок
        # расписания (окна, значки, подгруппы) видна как раз в тексте
        # карточки, и увидеть её со стороны было нечем.
        group = (query.get("group", [""])[0] or "").strip()
        if not group:
            return 400, {"error": "Нужна группа: ?group=ПИН-31"}
        week = max(0, min(3, int(query.get("week", ["0"])[0] or 0)))
        day = max(1, min(6, int(query.get("day", ["1"])[0] or 1)))
        try:
            sched = schedule.fetch_schedule(group)
        except Exception as e:                          # noqa: BLE001
            return 200, {"error": f"{type(e).__name__}: {e}"}
        slots = schedule.slots_of(sched, week, day)
        return 200, {
            "group": group, "week": week, "day": day,
            "semestr": sched.get("semestr", ""),
            "pairs": len(slots),
            "gaps": schedule.gaps_of(slots),
            "text": render.schedule_card(group, sched, week, day, week,
                                         custom=False),
            "rich": rich.day_html(group, sched, week, day, week,
                                  custom=False, buttons=False),
        }

    if path == "/api/admin/orioks-probe" and method == "GET":
        # Видит ли наш сервер ОРИОКС вообще: с адресов вне России он
        # рвёт TLS, и проверить это можно только оттуда, где живёт бот.
        return 200, {"probe": orioks.probe(),
                     "linked": orioks.linked_count()}

    if path == "/api/admin/days" and method == "GET":
        days = min(90, max(7, int(query.get("days", ["30"])[0] or 30)))
        return 200, {"days": analytics.days_list(days)}

    if path == "/api/admin/day" and method == "GET":
        date = (query.get("date", [""])[0] or "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            return 400, {"error": "Нужна дата вида 2026-09-07"}
        return 200, analytics.day_detail(date)

    if path == "/api/admin/users" and method == "GET":
        return 200, analytics.users_page(
            q=(query.get("q", [""])[0] or "").strip(),
            limit=int(query.get("limit", ["50"])[0] or 50),
            offset=int(query.get("offset", ["0"])[0] or 0))

    if path == "/api/admin/perms" and method == "GET":
        return 200, {"perms": [{"id": p, "label": t} for p, t in analytics.PERMS],
                     "roles": list(analytics.ROLES)}

    m = USER_PATH.match(path)
    if m:
        target = int(m.group(1))
        tail = m.group(2)

        if tail is None and method == "GET":
            card = analytics.user_card(target)
            if not card:
                return 404, {"error": "Такого пользователя нет"}
            card["access"] = analytics.identity(target, admin_ids())
            return 200, card

        if tail == "/role" and method == "POST":
            # Роли раздаёт только полный админ: право «блокировать» не должно
            # превращаться в способ выписать себе все остальные.
            if not me["is_admin"]:
                return 403, {"error": "Роли меняет только полный админ"}
            if target in admin_ids():
                return 403, {"error": "Владельца из ADMIN_IDS менять нельзя"}
            role = str(body.get("role") or "none")
            if role not in analytics.ROLES:
                return 400, {"error": "Неизвестная роль"}
            analytics.set_role(target, role,
                               body.get("perms") or [], body.get("sections") or [])
            return 200, {"ok": True, "access": analytics.identity(target, admin_ids())}

        if tail == "/block" and method == "POST":
            if not analytics.can(me, "users_block"):
                return 403, {"error": "Нет права блокировать"}
            if target in admin_ids():
                return 403, {"error": "Владельца из ADMIN_IDS блокировать нельзя"}
            if target == uid:
                return 400, {"error": "Себя заблокировать нельзя"}
            analytics.set_blocked(target, bool(body.get("blocked")))
            return 200, {"ok": True, "blocked": bool(body.get("blocked"))}

    return 404, {"error": "Нет такого маршрута"}


# ─────────────────────────── сервер ───────────────────────────

class Handler(BaseHTTPRequestHandler):
    server_version = "miet-api"
    protocol_version = "HTTP/1.1"

    def _send(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        encoding = None
        # Лента с тремя десятками постов — это полсотни килобайт текста,
        # который жмётся впятеро. На мобильной сети разница заметнее, чем
        # доли миллисекунды на сжатие. Мелочь трогать незачем.
        if len(raw) > 1400 and "gzip" in self.headers.get("Accept-Encoding", ""):
            raw = gzip.compress(raw, 6)
            encoding = "gzip"
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if encoding:
            self.send_header("Content-Encoding", encoding)
            # Иначе промежуточный кеш может отдать сжатый ответ клиенту,
            # который про gzip не просил.
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(raw)))
        self._cors()
        self.end_headers()
        self.wfile.write(raw)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", ALLOW_ORIGIN)
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Init-Data")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self) -> None:
        # Предварительный запрос браузера. Без него мини-апп с github.io не
        # смог бы прислать собственный заголовок X-Init-Data.
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path.startswith("/media/"):
            return self._media(url.path[len("/media/"):])
        self._run("GET")

    def _media(self, name: str) -> None:
        """
        Раздача картинок постов.

        Единственное место без проверки подписи, и по необходимости: в
        `<img src>` свой заголовок не поставить, а тащить картинки через
        JavaScript ради этого — значит остаться без ленивой загрузки и
        браузерного кеша. Защита здесь — неугадываемое имя: 32 знака
        хеша содержимого. Прямая ссылка на картинку закрытого поста
        утекает только вместе с самой картинкой, текст и опрос остаются
        за проверкой прав.
        """
        blob, mime = mediastore.read(name)
        if blob is None:
            self._send(404, {"error": "Файл не найден"})
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(blob)))
        # Имя — хеш содержимого, значит файл по этому адресу не меняется
        # никогда: кешируем надолго и не дёргаем сервер при каждом заходе.
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self._cors()
        self.end_headers()
        self.wfile.write(blob)

    def do_POST(self) -> None:
        self._run("POST")

    def _run(self, method: str) -> None:
        url = urlparse(self.path)
        body = {}
        if method == "POST":
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            cap = MAX_BODY_UPLOAD if url.path in UPLOAD_PATHS else MAX_BODY
            if length > cap:
                self._send(413, {"error": "Слишком большой запрос"})
                return
            if length:
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self._send(400, {"error": "Тело запроса не разобрано"})
                    return
            if not isinstance(body, dict):
                body = {}
        try:
            status, payload = handle(method, url.path, parse_qs(url.query), body,
                                     self.headers.get("X-Init-Data", ""))
        except Exception:
            # Падение одного запроса не должно ронять поток сервера, иначе
            # вместе с админкой замолчит и приём событий.
            log.exception("ошибка обработки %s %s", method, url.path)
            status, payload = 500, {"error": "Внутренняя ошибка"}
        self._send(status, payload)

    def log_message(self, fmt, *args) -> None:
        # Стандартный лог пишет строку на каждый запрос в stderr и забивает
        # панель Amvera. Ошибки и так видно по ответам.
        pass


def serve_in_background() -> threading.Thread | None:
    """Поднимает сервер отдельным потоком. Ошибка старта бота не валит."""
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    except OSError as e:
        log.warning("API не поднялся на порту %s: %s — админка и статистика "
                    "работать не будут", PORT, e)
        return None
    t = threading.Thread(target=srv.serve_forever, name="api", daemon=True)
    t.start()
    log.info("API слушает порт %s", PORT)
    return t
