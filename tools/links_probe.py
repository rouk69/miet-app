# -*- coding: utf-8 -*-
"""Проверяет присланные ссылки: жива ли, куда ведёт, что за заголовок."""
import sys, requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})

URLS = [
    "https://www.miet.ru/",
    "https://www.miet.ru/special/students",
    "https://www.miet.ru/schedule/",
    "https://www.miet.ru/structure/s/353",
    "https://abit.miet.ru/",
    "https://account.miet.ru/",
    "https://www.miet.ru/structure/",
    "https://www.miet.ru/education/",
    "https://www.miet.ru/news/",
    "https://www.miet.ru/structure/s/322",
    "https://www.miet.ru/sport/",
    "https://www.miet.ru/dk/",
    "https://www.miet.ru/special/entrant",
    "https://www.miet.ru/education/programs/",
    "https://www.miet.ru/education/documents/",
    "https://www.miet.ru/contacts/",
    "https://www.miet.ru/structure/s/353/e/53374/112",
    "https://www.miet.ru/structure/s/322/e/20118/102",
]

for u in dict.fromkeys(URLS):
    try:
        r = S.get(u, timeout=30, allow_redirects=True)
    except Exception as e:
        print(f"[ERR ] {u}\n       {e}")
        continue
    r.encoding = "utf-8"
    s = BeautifulSoup(r.text, "html.parser")
    h1 = s.find("h1")
    title = s.find("title")
    is404 = "IIS" in (title.get_text() if title else "") or r.status_code >= 400
    mark = "404 " if is404 else "OK  "
    final = r.url if r.url.rstrip("/") != u.rstrip("/") else ""
    print(f"[{mark}] {r.status_code} {len(r.text):>7}  {u}")
    if final:
        print(f"       → {final}")
    print(f"       title: {(title.get_text().strip() if title else '-')[:80]}")
    print(f"       h1   : {(h1.get_text(' ', strip=True) if h1 else '-')[:80]}")
