# -*- coding: utf-8 -*-
"""
Новости с miet.ru: бот сам ходит за ними и кладёт свежие в ленту.

Раньше новости попадали в приложение только через `tools/update.py` —
руками, с пересборкой `data/app.json` и пушем в репозиторий. В облаке так
нельзя: контейнер не коммитит в git, а файлы рядом с кодом стираются при
выкладке. Поэтому свежее берётся здесь и живёт в базе (`posts` с
`kind='news'`), а `data/app.json` остаётся архивом того, что было собрано
на момент сборки. В ленте они лежат вперемешку, по дате.

Разбор — теми же селекторами, что в `tools/harvest.py`: они проверены на
этом сайте. Регулярками по всей странице обойтись не вышло — в текст
новости попадало меню сайта целиком, потому что вёрстка miet.ru щедра на
вложенные блоки.

Свалиться этот модуль не должен ни при каких обстоятельствах: не нашли
новостей — пишем в лог и живём дальше, следующая попытка через несколько
часов. Бот важнее новостей.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import media as mediastore
from . import posts

log = logging.getLogger("miet.news")

BASE = "https://www.miet.ru"
LIST_URL = BASE + "/news/"

# Раз в три часа: новости на сайте появляются пару раз в день, чаще
# ходить незачем — это чужой сервер, а не наш.
EVERY = 3 * 60 * 60

# Сколько новостей забираем за один заход. Первый запуск на пустой базе
# наберёт ленту, дальше почти всегда всё уже будет на месте.
BATCH = 12

# Блок с телом новости. Порядок важен: первый подходящий и берём.
BODY_SELECTORS = ".news-detail, .detail-text, .article-content, .content"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

NEWS_LINK = re.compile(r"^/news/(\d+)/?$")


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def _soup(url: str):
    r = requests.get(url, timeout=25, headers={
        "User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "html.parser")


def _listing() -> list:
    """Новости со страницы /news/: (внешний id, ссылка, заголовок)."""
    s = _soup(LIST_URL)
    out, seen = [], set()

    # Сначала пробуем разметку списка новостей — в ней заголовок отделён от
    # прочего текста. Если вёрстка переехала, ниже есть запасной путь.
    for it in s.select(".news-list__item"):
        a = it.select_one(".news-list__item-title a") or it.select_one("a")
        if not a:
            continue
        m = NEWS_LINK.match(a.get("href", "").split("?")[0])
        title = _clean(a.get_text())
        if not m or m.group(1) in seen or len(title) < 12:
            continue
        seen.add(m.group(1))
        out.append((m.group(1), urljoin(BASE, a["href"]), title))

    if not out:
        for a in s.select('a[href^="/news/"]'):
            m = NEWS_LINK.match(a.get("href", "").split("?")[0])
            title = _clean(a.get_text())
            if not m or m.group(1) in seen or len(title) < 12:
                continue
            seen.add(m.group(1))
            out.append((m.group(1), urljoin(BASE, a["href"]), title))
        if out:
            log.info("список новостей разобран запасным способом — "
                     "вёрстка miet.ru изменилась")
    return out[:BATCH]


def _article(url: str) -> tuple:
    """Текст новости и картинка к ней. Оба необязательны."""
    try:
        s = _soup(url)
    except Exception as e:
        log.warning("новость %s не открылась: %s", url, e)
        return "", ""

    body = s.select_one(BODY_SELECTORS)
    if body is None:
        # Без тела новости брать <p> со всей страницы нельзя: там меню,
        # футер и списки подразделений — в ленте это выглядит как мусор.
        log.info("у новости %s не нашлось блока с текстом", url)
        return "", _cover(s, only_body=False)

    paras = [_clean(p.get_text()) for p in body.find_all("p")]
    text = "\n\n".join(p for p in paras if len(p) > 40)[:3500]
    return text, _cover(body)


def _cover(node, only_body: bool = True) -> str:
    """Первая содержательная картинка. Иконки интерфейса не в /upload/."""
    for im in node.select("img"):
        src = im.get("src", "")
        if "/upload/" not in src:
            continue
        try:
            blob = requests.get(urljoin(BASE, src), timeout=25,
                                headers={"User-Agent": UA}).content
            return mediastore.store(blob)
        except Exception as e:
            log.debug("обложка %s не забралась: %s", src, e)
    return ""


def sync_once() -> int:
    """Один заход за новостями. Возвращает, сколько добавилось."""
    try:
        items = _listing()
    except Exception as e:
        log.warning("список новостей не загрузился: %s", e)
        return 0
    if not items:
        log.warning("на странице новостей ничего не нашлось — возможно, "
                    "изменилась вёрстка miet.ru")
        return 0

    added = 0
    for num, url, title in items:
        # Полный текст тянем только за теми, которых у нас ещё нет: иначе
        # каждый заход означал бы десяток лишних запросов к чужому сайту.
        if not posts.add_news(num, title, "", url):
            continue
        text, media = _article(url)
        posts.update_news(num, text, media)
        added += 1
    if added:
        log.info("новостей с miet.ru добавлено: %d", added)
    return added


def run_in_background() -> threading.Thread:
    """Фоновый сбор. Ошибки не выпускает наружу — бот важнее новостей."""
    def loop():
        # Небольшая задержка на старте: сначала должен подняться опрос
        # Telegram, иначе первый заход за новостями задержит ответы людям.
        time.sleep(20)
        while True:
            try:
                sync_once()
            except Exception:
                log.exception("сбор новостей сорвался")
            time.sleep(EVERY)

    t = threading.Thread(target=loop, name="news", daemon=True)
    t.start()
    return t
