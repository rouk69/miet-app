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
import os
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


# Где живёт приложение. Раньше это был GitHub Pages, но у части
# операторов соединение к github.io рвётся — человек видит «не удалось
# загрузить» вместо расписания. Теперь клиент раздаёт сам бот, и адрес
# по умолчанию — его собственный.
SELF_URL = "https://miet-bot-rouk.amvera.io"


def app_url() -> str:
    """
    Адрес мини-приложения — один на бота, кнопки и рассылку.

    Считается здесь, а не в каждом месте по-своему: разъехавшись, они
    дают кнопку меню на одном домене и кнопку под утренней карточкой на
    другом. Переопределяется переменной APP_URL; старая WEBAPP_URL
    осталась для тех, кто раздаёт клиент где-то ещё, но на github.io мы
    больше не ведём — именно от него и уходили.
    """
    for name in ("APP_URL", "WEBAPP_URL"):
        got = (os.environ.get(name) or "").strip()
        if got and "github.io" not in got:
            return got.rstrip("/")
    return SELF_URL


def mirror_url() -> str:
    """
    Запасной вход — воркер Cloudflare, проксирующий к нам же
    (`mirror/worker.js`). Пусто, пока переменная MIRROR_URL не задана в
    панели Amvera: без выложенного воркера предлагать человеку нечего.
    """
    got = (os.environ.get("MIRROR_URL") or "").strip()
    return got.rstrip("/") if got.startswith("https://") else ""


def app_url_for(user_id: int | None) -> str:
    """
    Каким адресом открывать приложение ЭТОМУ человеку.

    Почти всем — прямым: он короче и работает. Но у кого прямой путь
    оборвался (чужой VPN, оператор), тому одна и та же кнопка не
    откроется и завтра, поэтому его выбор хранится в базе и кнопки
    собираются под него. Импорт внутри функции намеренно: storage тянет
    за собой базу, а адрес приложения спрашивают и там, где базы нет —
    в проверках клиента и в setup_bot.
    """
    mirror = mirror_url()
    if not mirror or not user_id:
        return app_url()
    try:
        from .storage import mirror_on
        return mirror if mirror_on(user_id) else app_url()
    except Exception:                                   # noqa: BLE001
        log.exception("не удалось узнать вход для %s", user_id)
        return app_url()


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


def run_in_background(url: str, on_check=None) -> threading.Thread:
    """
    Следит за меткой выложенного клиента.

    `on_check` зовётся КАЖДЫЙ круг, а не только при смене метки: разовая
    установка кнопки меню могла не удаться (Telegram ответил «слишком
    часто», сеть моргнула), и тогда чинить её было бы некому — метка-то
    не менялась. Пусть решает тот, кто ставит: он видит, куда кнопка
    ведёт сейчас.
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
                if on_check:
                    on_check(version())
            except Exception:                           # noqa: BLE001
                log.exception("проверка метки приложения сорвалась")
            time.sleep(EVERY)

    t = threading.Thread(target=loop, name="webapp-version", daemon=True)
    t.start()
    return t
