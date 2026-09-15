# -*- coding: utf-8 -*-
"""
Сколько бот живёт с последнего старта и как часто он поднимается.

Понадобилось после жалобы «приложение не открывается,
ERR_CONNECTION_CLOSED». Так выглядит оборванное соединение, и причин у
него ровно две: либо не дошёл маршрут до нас (чужой VPN, оператор),
либо в эту секунду поднимался контейнер — пока процесс не слушает
порт, envoy рвёт входящие. Снаружи эти два случая неразличимы, а
разводить их надо: первое лечится вторым путём до сервера, второе —
на стороне Amvera, и делать одно вместо другого бессмысленно.

Логи Amvera показывают только последний запуск и только владельцу в
панели, поэтому отметка о старте кладётся в базу. Тогда на вопрос
«падал ли ты сегодня» отвечает обычный запрос к /api/health, без
браузера и без панели.

Хранится одно время на запуск, ничего больше. Старше месяца — убираем:
запись нужна, чтобы увидеть ближайшие сутки, а не историю за семестр.
"""
from __future__ import annotations

import logging
import time

from .db import MSK, conn

log = logging.getLogger("miet.uptime")

# Когда поднялся этот процесс. Время машины, не базы: здесь нужен не
# календарь, а разница — сколько секунд назад это было.
STARTED = time.time()

KEEP_DAYS = 30


def note_start() -> None:
    """
    Отмечает, что процесс поднялся, и подчищает старые отметки.

    Ошибку глотаем: бот, не сумевший записать строку о собственном
    запуске, обязан всё равно запуститься.
    """
    try:
        conn().execute("INSERT INTO starts (at) VALUES (CURRENT_TIMESTAMP)")
        conn().execute("DELETE FROM starts WHERE at < datetime('now', ?)",
                       ("-%d days" % KEEP_DAYS,))
    except Exception:                                   # noqa: BLE001
        log.exception("отметка о запуске не записалась")


def recent(hours: int = 24) -> list:
    """Времена запусков за последние часы, по Москве, свежие сверху."""
    rows = conn().execute(
        """SELECT datetime(at, ?) FROM starts
           WHERE at >= datetime('now', ?) ORDER BY at DESC LIMIT 50""",
        (MSK, "-%d hours" % hours))
    return [r[0] for r in rows]


def state() -> dict:
    """
    Здоровье процесса в том виде, в каком его отдаёт /api/health.

    Отдаётся без подписи Telegram, поэтому здесь нет ничего личного:
    сколько секунд живём и когда поднимались. По этим двум числам и
    видно, наш ли это обрыв.
    """
    alive = int(time.time() - STARTED)
    try:
        starts = recent(24)
    except Exception:                                   # noqa: BLE001
        log.exception("история запусков не прочиталась")
        starts = []
    return {
        "uptime": alive,
        "uptime_h": round(alive / 3600, 1),
        "starts_24h": len(starts),
        "started_at": starts[0] if starts else None,
        "prev_start": starts[1] if len(starts) > 1 else None,
    }
