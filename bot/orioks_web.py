# -*- coding: utf-8 -*-
"""
Веб-версия ОРИОКС: то, чего нет в официальном API.

Студенческое API отдаёт у мероприятия ровно пять полей — alias, name,
type, week, max_grade. Ни текста задания, ни файлов, ни комментария
преподавателя там нет, и соседних разделов с ними тоже (проверено: все
404). А в веб-версии это есть, потому что студент их там читает.

**Пароль здесь не сохраняется никогда.** Он живёт в памяти ровно на
время входа, обменивается на cookie сессии, и дальше работа идёт с ней.
Сессию человек может убить, выйдя из ОРИОКС, и она протухает сама.

Это компромисс, и называть его надо честно: cookie сессии — это доступ к
личному кабинету, пусть и временный. Поэтому раздел включается только по
явному действию человека, а отключение стирает сессию немедленно.
"""
from __future__ import annotations

import http.cookiejar
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger("miet.orioks.web")

BASE = "https://orioks.miet.ru"
TIMEOUT = 25

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


class WebError(Exception):
    """Ошибка, которую можно показать человеку."""


def _opener():
    """
    Свой обработчик cookie на каждый вход: общий держал бы чужие сессии
    в одной банке, а это ровно тот случай, когда путаница недопустима.
    Прокси обходим — на машине автора он заворачивает такие адреса.
    """
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.ProxyHandler({})), jar


def _get(opener, path: str) -> str:
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise WebError(f"ОРИОКС ответил {e.code} на {path}")
    except Exception as e:                              # noqa: BLE001
        raise WebError(f"ОРИОКС недоступен ({type(e).__name__})")


def login_form() -> dict:
    """
    Как устроена форма входа: куда отправлять и какие поля заполнять.

    Разведка без пароля — нужна, чтобы не гадать имена полей: у разных
    версий ОРИОКС они назывались по-разному.
    """
    opener, _ = _opener()
    html = _get(opener, "/")
    forms = re.findall(r"<form[^>]*>[\s\S]*?</form>", html, re.I)
    out = []
    for f in forms[:4]:
        action = re.search(r'action=["\']([^"\']*)["\']', f, re.I)
        method = re.search(r'method=["\']([^"\']*)["\']', f, re.I)
        fields = re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', f, re.I)
        types = re.findall(r'<input[^>]*type=["\']([^"\']+)["\']', f, re.I)
        out.append({
            "action": action.group(1) if action else "",
            "method": (method.group(1) if method else "GET").upper(),
            "fields": fields,
            "types": types,
        })
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    return {
        "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "",
        "forms": out,
        "length": len(html),
    }
