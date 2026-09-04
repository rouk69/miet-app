# -*- coding: utf-8 -*-
"""Сбор данных и фотографий с miet.ru для Telegram Mini App."""
import json, os, re, sys, time, hashlib
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.miet.ru"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "_raw")
IMG = os.path.join(DATA, "img")
os.makedirs(IMG, exist_ok=True)

_cache = {}


def soup_of(url):
    if url in _cache:
        return _cache[url]
    try:
        r = S.get(url, timeout=35)
    except Exception as e:
        print("  ERR", url, e)
        return None
    r.encoding = "utf-8"
    s = BeautifulSoup(r.text, "html.parser")
    _cache[url] = s
    return s


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def download(src, prefix):
    """Скачивает картинку, возвращает локальное имя файла."""
    if not src:
        return None
    url = urljoin(BASE, src)
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
        ext = ".jpg"
    name = f"{prefix}-{hashlib.md5(url.encode()).hexdigest()[:10]}{ext}"
    path = os.path.join(IMG, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return name
    try:
        r = S.get(url, timeout=45)
        if r.status_code == 200 and len(r.content) > 900:
            open(path, "wb").write(r.content)
            return name
    except Exception as e:
        print("  imgERR", url, e)
    return None


# ─────────────────────────── 1. Новости ───────────────────────────
def harvest_news(pages=3, full=26):
    items, seen = [], set()
    for p in range(1, pages + 1):
        url = f"{BASE}/news/" if p == 1 else f"{BASE}/news/?PAGEN_1={p}"
        s = soup_of(url)
        if not s:
            continue
        for it in s.select(".news-list__item"):
            a = it.select_one(".news-list__item-title a")
            if not a:
                continue
            href = a.get("href", "")
            if href in seen:
                continue
            seen.add(href)
            img = it.select_one(".news-list__item-image img")
            d = it.select_one(".news-list__item-date")
            items.append({
                "id": re.sub(r"\D", "", href),
                "url": urljoin(BASE, href),
                "title": clean(a.get_text()),
                "date": clean(d.get_text()) if d else "",
                "cover_src": img.get("src") if img else None,
            })
        print(f"  новости стр.{p}: всего {len(items)}")
    # обложки + полный текст первых N
    for i, n in enumerate(items):
        n["cover"] = download(n.pop("cover_src"), "news")
        if i < full:
            s = soup_of(n["url"])
            if s:
                body = s.select_one(".news-detail, .detail-text, .article-content, .content")
                paras = []
                for pnode in (body or s).find_all("p"):
                    t = clean(pnode.get_text())
                    if len(t) > 40:
                        paras.append(t)
                n["text"] = "\n\n".join(paras[:14])
                n["tags"] = [clean(t.get_text()) for t in s.select('a[href*="/news/tag/"]')][:6]
                gal = []
                for im in (body or s).select("img"):
                    src = im.get("src", "")
                    if "/upload/" in src and len(gal) < 4:
                        f = download(src, "news")
                        if f and f != n["cover"]:
                            gal.append(f)
                n["gallery"] = gal
    return items


# ─────────────────────────── 2. Институты ───────────────────────────
def harvest_institutes():
    s = soup_of(f"{BASE}/structure/s/2775")
    out = []
    if not s:
        return out
    for a in s.select(".university-list__item a, .university-list__item-container__title a"):
        name, href = clean(a.get_text()), a.get("href", "")
        if not name or not href or len(name) < 6:
            continue
        if any(o["name"] == name for o in out):
            continue
        out.append({"name": name, "url": urljoin(BASE, href)})
    for ins in out:
        s2 = soup_of(ins["url"])
        if not s2:
            continue
        h = s2.find("h1")
        if h:
            ins["name"] = clean(h.get_text())
        info = {}
        for it in s2.select(".info-contacts__item"):
            txt = clean(it.get_text(" "))
            m = re.match(r"(Директор|Телефон|E-?mail|Аудитория|Внутренний телефон)\s*:?\s*(.+)",
                         txt, re.I)
            if m:
                info[m.group(1).lower()] = m.group(2)
        ins["info"] = info
        paras = [clean(p.get_text()) for p in s2.find_all("p")]
        ins["about"] = " ".join([p for p in paras if len(p) > 60][:3])[:900]
        sub = []
        for a in s2.select(".site-sidebar__item-subnav__item a, .university-list__item a"):
            t = clean(a.get_text())
            if 4 < len(t) < 120 and t not in sub:
                sub.append(t)
        ins["departments"] = sub[:24]
        im = s2.select_one('.content img[src*="/upload/"], img[src*="/upload/"]')
        ins["photo"] = download(im.get("src"), "inst") if im else None
        print("  институт:", ins["name"][:60])
    return out


# ─────────────────────── 3. Разделы-страницы ───────────────────────
SECTIONS = [
    ("dk",        "Дом культуры",            "/structure/s/354"),
    ("sport",     "Спортивный комплекс",     "/structure/s/355"),
    ("dorm",      "Студгородок",             "/structure/s/353"),
    ("library",   "Библиотека",              "/structure/s/322"),
    ("canteen",   "Столовая",                "/structure/s/357"),
    ("health",    "Здравпункт",              "/structure/s/359"),
    ("sanatorium","Санаторий-профилакторий", "/structure/s/358"),
    ("career",    "Центр развития карьеры",  "/structure/s/3450"),
    ("uvd",       "Управление внеучебной деятельности", "/structure/s/1905"),
    ("scholarship","Стипендии",              "/page/34799"),
    ("social",    "Социальная поддержка",    "/page/1962"),
    ("contacts",  "Контактная информация",   "/page/1127"),
    ("today",     "МИЭТ сегодня",            "/page/104640"),
    ("history",   "История",                 "/page/1128"),
    ("brand",     "Символика и брендбук",    "/page/107250"),
]


def harvest_sections():
    out = {}
    for key, title, path in SECTIONS:
        s = soup_of(urljoin(BASE, path))
        if not s:
            continue
        h = s.find("h1")
        info = {}
        for it in s.select(".info-contacts__item"):
            txt = clean(it.get_text(" "))
            m = re.match(r"(Директор|Начальник|Руководитель|Заведующий|Телефон|E-?mail|"
                         r"Аудитория|Внутренний телефон|Адрес|Часы работы)\s*:?\s*(.+)", txt, re.I)
            if m:
                info[m.group(1).lower()] = m.group(2)
        paras = [clean(p.get_text()) for p in s.find_all("p")]
        links = []
        for a in s.select(".site-sidebar__item-subnav__item a, .site-sidebar__item-link"):
            t = clean(a.get_text())
            if 3 < len(t) < 120 and not any(l["title"] == t for l in links):
                links.append({"title": t, "url": urljoin(BASE, a.get("href", ""))})
        photos = []
        for im in s.select('img[src*="/upload/"]'):
            f = download(im.get("src"), key)
            if f and f not in photos and len(photos) < 6:
                photos.append(f)
        out[key] = {
            "key": key,
            "title": clean(h.get_text()) if h else title,
            "url": urljoin(BASE, path),
            "info": info,
            "text": "\n\n".join([p for p in paras if len(p) > 50][:10])[:2600],
            "links": links[:20],
            "photos": photos,
        }
        print(f"  раздел: {out[key]['title'][:50]:50} фото={len(photos)} ссылок={len(links)}")
    return out


# ─────────────────────── 4. Общие фото / логотип ───────────────────────
def harvest_media():
    files = []
    s = soup_of(BASE + "/")
    if s:
        for im in s.select("img"):
            f = download(im.get("src"), "home")
            if f and f not in files:
                files.append(f)
    for extra in ["/img/logo.svg", "/img/fav/apple-touch-icon.png"]:
        f = download(extra, "brand")
        if f and f not in files:
            files.append(f)
    return files


if __name__ == "__main__":
    t0 = time.time()
    res = {}
    print("── новости");      res["news"] = harvest_news()
    print("── институты");    res["institutes"] = harvest_institutes()
    print("── разделы");      res["sections"] = harvest_sections()
    print("── медиа");        res["media"] = harvest_media()
    r = S.get("https://miet.ru/schedule/groups", timeout=30); r.encoding = "utf-8"
    res["groups"] = r.json()
    print("  групп:", len(res["groups"]))

    json.dump(res, open(os.path.join(DATA, "miet.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n_img = len(os.listdir(IMG))
    print(f"\nГОТОВО за {time.time()-t0:.0f}с — новостей {len(res['news'])}, "
          f"институтов {len(res['institutes'])}, разделов {len(res['sections'])}, "
          f"картинок {n_img}, групп {len(res['groups'])}")
