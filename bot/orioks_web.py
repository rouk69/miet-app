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
import json
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


# ─────────────────────────── вход ───────────────────────────

LOGIN_PATH = "/user/login"

# Разведано на живом сайте: форма Yii2 с CSRF-токеном в скрытом поле.
FIELD_LOGIN = "LoginForm[login]"
FIELD_PASSWORD = "LoginForm[password]"
FIELD_CSRF = "_csrf"


def _csrf_of(html: str) -> str:
    """
    Токен из скрытого поля. Порядок атрибутов у Yii2 не закреплён,
    поэтому смотрим оба: и name раньше value, и наоборот.
    """
    for pat in (r"name=[\"']_csrf[\"'][^>]*value=[\"']([^\"']+)[\"']",
                r"value=[\"']([^\"']+)[\"'][^>]*name=[\"']_csrf[\"']"):
        m = re.search(pat, html, re.I)
        if m:
            return m.group(1)
    return ""


def sign_in(login: str, password: str):
    """
    Входит в веб-версию и возвращает opener с живой сессией.

    Пароль не возвращается и никуда не записывается: он нужен ровно на
    один POST и после него остаётся только cookie.
    """
    opener, jar = _opener()
    page = _get(opener, LOGIN_PATH)
    csrf = _csrf_of(page)
    if not csrf:
        raise WebError("Не нашёл форму входа — ОРИОКС изменил страницу")

    data = urllib.parse.urlencode({
        FIELD_CSRF: csrf,
        FIELD_LOGIN: login,
        FIELD_PASSWORD: password,
        "LoginForm[rememberMe]": "1",
    }).encode("utf-8")
    req = urllib.request.Request(
        BASE + LOGIN_PATH, data=data,
        headers={"User-Agent": UA, "Referer": BASE + LOGIN_PATH,
                 "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
            final = r.geturl()
    except urllib.error.HTTPError as e:
        raise WebError(f"ОРИОКС ответил {e.code} при входе")
    except Exception as e:                              # noqa: BLE001
        raise WebError(f"ОРИОКС недоступен ({type(e).__name__})")

    # Признак неудачи — снова форма входа: Yii2 отвечает на неверный
    # пароль той же страницей с сообщением, а не кодом ошибки.
    if FIELD_PASSWORD in body or "/user/login" in final:
        note = re.search(r'class="help-block[^"]*">([^<]+)<', body)
        raise WebError(note.group(1).strip() if note
                       else "ОРИОКС не принял логин или пароль")
    return opener, jar, final


def site_map(opener) -> dict:
    """
    Куда ведут ссылки из меню после входа: нужно, чтобы найти раздел с
    домашними заданиями, а не гадать его адрес.
    """
    html = _get(opener, "/")
    links = {}
    for href, text in re.findall(
            r"<a[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>([\s\S]{0,80}?)</a>",
            html, re.I):
        label = re.sub(r"<[^>]+>", " ", text)
        label = re.sub(r"\s+", " ", label).strip()
        if not label or href.startswith("http") and BASE not in href:
            continue
        links.setdefault(href, label)
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    return {
        "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "",
        "links": [{"href": h, "text": t} for h, t in list(links.items())[:60]],
    }


# ──────────────────────── сессия отдельно от пароля ────────────────────────

def cookie_of(jar) -> str:
    """Печенье одной строкой — в таком виде его и хранит бот."""
    return "; ".join(c.name + "=" + c.value for c in jar)


def sign_in_cookie(login: str, password: str) -> str:
    """
    Пароль на входе, cookie на выходе. Дальше пароль не нужен вовсе —
    ради этого всё и затевалось.
    """
    _, jar, _ = sign_in(login, password)
    cookie = cookie_of(jar)
    if not cookie:
        raise WebError("ОРИОКС не выдал сессию")
    return cookie


def get_page(cookie: str, path: str) -> str:
    """Страница из-под сохранённой сессии."""
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Cookie": cookie})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise WebError("ОРИОКС ответил " + str(e.code) + " на " + path)
    except Exception as e:                              # noqa: BLE001
        raise WebError("ОРИОКС недоступен (" + type(e).__name__ + ")")


def alive(cookie: str) -> bool:
    """Жива ли сессия: протухшая возвращает страницу входа."""
    try:
        return FIELD_PASSWORD not in get_page(cookie, "/")
    except WebError:
        return False


def text_of(html: str) -> str:
    """Голый текст страницы без скриптов и разметки."""
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>|</(p|div|tr|li|h[1-6])>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&quot;", '"').replace("&lt;", "<")
                .replace("&gt;", ">").replace("&#039;", "'"))
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in html.split("\n")]
    return "\n".join(ln for ln in lines if ln)


# Что искать в подписях ссылок: разделы, где вообще могут лежать задания.
INTERESTING = ("задан", "журнал", "дисципл", "учеб", "успева", "контрол",
               "работ", "материал", "курс")


def explore(cookie: str, limit: int = 8) -> dict:
    """
    Обход личного кабинета: какие разделы есть и что в них написано.

    Нужен один раз — чтобы понять, где именно лежит текст домашнего
    задания, вместо угадывания адресов вслепую.
    """
    root = get_page(cookie, "/")
    pages = [{"href": "/", "title": _title(root),
              "text": text_of(root)[:1200]}]

    seen = {"/"}
    for href, label in _links(root):
        if len(pages) > limit:
            break
        low = label.lower()
        if href in seen or not any(w in low for w in INTERESTING):
            continue
        seen.add(href)
        try:
            html = get_page(cookie, href)
        except WebError as e:
            pages.append({"href": href, "title": label, "error": str(e)})
            continue
        pages.append({"href": href, "label": label, "title": _title(html),
                      "text": text_of(html)[:1500]})
    return {"pages": pages}


STUDY_PATH = "/student/student"


def study_json(cookie: str) -> dict:
    """
    Данные учёбы из веб-версии — те же дисциплины, но целиком.

    Страница отдаёт их одним куском JSON прямо в разметке: так её
    рисует Angular. Полей там заметно больше, чем в студенческом API:
    сроки сдачи (date_start, date_end), настройки мероприятия,
    прикреплённые ресурсы (irs) и попытки сдачи. Ради них всё и
    затевалось — API отдаёт голые названия.
    """
    html = get_page(cookie, STUDY_PATH)
    raw = _cut_json(html)
    if not raw:
        raise WebError("Не нашёл данные учёбы — ОРИОКС изменил страницу")
    try:
        return json.loads(raw)
    except ValueError as e:
        raise WebError("Не разобрал данные учёбы (" + str(e) + ")")


def study_report(data: dict) -> dict:
    """
    Что в данных учёбы реально заполнено.

    Разведка по живому аккаунту: поле, которое всегда пустое, полагаться
    на себя не даёт, сколько бы обещаний ни было в его названии.
    """
    filled, total, samples = {}, 0, {}
    for dis in data.get("dises", []):
        for seg in dis.get("segments", []):
            for km in seg.get("allKms", []):
                total += 1
                for key, value in km.items():
                    if value in (None, "", [], {}, 0):
                        continue
                    filled[key] = filled.get(key, 0) + 1
                    if key in ("settings", "irs", "balls", "date_start",
                               "date_end", "attempt") and key not in samples:
                        samples[key] = {"дисциплина": dis.get("name"),
                                        "мероприятие": km.get("name"),
                                        "значение": value}
    return {
        "дисциплин": len(data.get("dises", [])),
        "мероприятий": total,
        "заполнено": dict(sorted(filled.items(), key=lambda p: -p[1])),
        "примеры": samples,
    }


def _cut_json(html: str) -> str:
    """
    Кусок от «{"dises":» до парной закрывающей скобки.

    Регулярным выражением такое не берётся — вложенность произвольная,
    поэтому считаем скобки, пропуская их внутри строк.
    """
    text = html.replace("&quot;", '"').replace("&#34;", '"')
    start = text.find('{"dises"')
    if start < 0:
        return ""
    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return ""


def _title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def _links(html: str):
    out = []
    for href, text in re.findall(
            r"<a[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>([\s\S]{0,120}?)</a>",
            html, re.I):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()
        if label and (href.startswith("/") or href.startswith(BASE)):
            out.append((href.replace(BASE, "") or "/", label))
    return out
