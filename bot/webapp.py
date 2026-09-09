# -*- coding: utf-8 -*-
"""
Метка выложенного мини-приложения — и почему бот берёт её из сети.

Telegram кеширует страницу мини-приложения по адресу, поэтому в ссылку
подставляется метка выкладки (`?v=...`): другой адрес — другая
страница. Метку пишет `tools/stamp.py` в `webapp.version`, файл лежит
в том же репозитории.

Раньше бот читал его у себя на диске — и это значило, что **каждая
правка клиента требовала выкладки бота**. А выкладка перезапускает
контейнер: минуту-две бот не отвечает вовсе, потом заново поднимает
опрос. Правок клиента за вечер бывает десяток, и со стороны это
выглядит так, будто бот сломался и тупит.

Теперь метка читается с самой страницы — `WEBAPP_URL/webapp.version`,
раз в четверть часа. Клиент выкладывается сам по себе, бот замечает
это сам и переставляет кнопку меню, не перезапускаясь.

Файл на диске остался запасным: пока сеть не ответила (первые секунды
после старта, недоступный GitHub), в ссылку идёт он.
"""
from __future__ import annotations

import logging
import threading
import time
import urllib.error
import urllib.request

from .paths import webapp_version as version_on_disk

log = logging.getLogger("miet.webapp")

# Четверть часа. Клиент выкладывается пачками по несколько правок, и
# ловить каждую незачем: кнопка меню — не то место, где секунды решают.
EVERY = 15 * 60

TIMEOUT = 15

# Метка, увиденная в сети. Пустая — значит ещё не спрашивали или не
# ответили; тогда берём ту, что лежит на диске.
_seen = {"version": "", "at": 0.0}


def version() -> str:
    """Что подставлять в адрес мини-приложения прямо сейчас."""
    return _seen["version"] or version_on_disk()


def fetch(url: str) -> str:
    """
    Спрашивает у выложенного приложения его метку.

    Пустая строка означает «не смогли»: файла нет, сеть молчит, ответ не
    похож на метку. Ошибку наружу не поднимаем — это фон, и падать ему
    не из-за чего.
    """
    if not url:
        return ""
    src = url.rstrip("/") + "/webapp.version"
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(src, timeout=TIMEOUT) as r:
            got = r.read(64).decode("utf-8", "replace").strip()
    except (urllib.error.URLError, OSError, ValueError) as e:
        log.info("метка приложения не прочиталась: %s", e)
        return ""
    # Метка — восемь шестнадцатеричных знаков. Всё прочее значит, что
    # нам отдали страницу с ошибкой, а не файл.
    if len(got) == 8 and all(c in "0123456789abcdef" for c in got):
        return got
    log.info("метка приложения выглядит странно: %r", got[:32])
    return ""


def run_in_background(url: str, on_change=None) -> threading.Thread:
    """
    Следит за меткой. `on_change` зовётся, когда она сменилась, —
    им бот переставляет кнопку меню на свежий адрес.
    """
    def loop():
        # Первый заход почти сразу: контейнер только что поднялся, и
        # метка на диске могла отстать от выложенного клиента.
        time.sleep(20)
        while True:
            try:
                got = fetch(url)
                if got and got != _seen["version"]:
                    was = _seen["version"] or version_on_disk()
                    _seen["version"] = got
                    _seen["at"] = time.time()
                    if got != was:
                        log.info("клиент обновился: %s → %s", was or "—", got)
                        if on_change:
                            on_change(got)
            except Exception:                           # noqa: BLE001
                log.exception("проверка метки приложения сорвалась")
            time.sleep(EVERY)

    t = threading.Thread(target=loop, name="webapp-version", daemon=True)
    t.start()
    return t
