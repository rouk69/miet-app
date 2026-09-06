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

import json
import logging
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import analytics, auth, storage

log = logging.getLogger("miet.api")

# Amvera пускает наружу только 80-й порт — там домен проекта и заканчивается.
# Локально его слушать нельзя без прав администратора, поэтому при отладке
# порт переопределяется переменной PORT (см. .env.example).
PORT = int(os.environ.get("PORT") or 80)

# Откуда разрешено обращаться. По умолчанию любой источник: личных данных
# API не отдаёт никому, кроме владельца подписанной initData, а мини-апп
# может открываться и с github.io, и с локального сервера при отладке.
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "*").strip() or "*"

MAX_BODY = 64 * 1024


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
        return 200, {"ok": True}

    who = _actor(init_data)
    if not who:
        return 401, {"error": "Подпись Telegram не сошлась"}
    user, me = who
    uid = int(user["id"])

    if path == "/api/me" and method == "GET":
        return 200, _me(user, me)

    if path == "/api/track" and method == "POST":
        return _track(user, me, body)

    if path.startswith("/api/admin/"):
        return _admin(path, method, query, body, uid, me)

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
        # Группа с сервера: человек выбрал её в боте — приложение подхватит
        # её на другом устройстве, и наоборот.
        "group": saved.get("group"),
    }


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
        for ev in events[:50]:
            if not isinstance(ev, dict):
                continue
            kind = str(ev.get("kind") or "")
            if kind in ("open", "tab", "screen"):
                analytics.note(uid, kind, ev.get("name") or "")
    return 200, {"ok": True}


USER_PATH = re.compile(r"^/api/admin/users/(\d+)(/role|/block)?$")


def _admin(path: str, method: str, query: dict, body: dict, uid: int, me: dict):
    if not analytics.can(me, "stats"):
        return 403, {"error": "Нет доступа"}

    if path == "/api/admin/stats" and method == "GET":
        days = min(60, max(7, int(query.get("days", ["14"])[0] or 14)))
        return 200, analytics.overview(days)

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
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
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
        self._run("GET")

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
            if length > MAX_BODY:
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
