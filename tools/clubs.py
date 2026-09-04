# -*- coding: utf-8 -*-
"""Кружки, секции и студенческие объединения МИЭТ."""
import json, os, re, sys, hashlib
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://www.miet.ru"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
S = requests.Session(); S.headers.update({"User-Agent": UA})
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "_raw"); IMG = os.path.join(DATA, "img")


def clean(t): return re.sub(r"\s+", " ", t or "").strip()


def get(url):
    try:
        r = S.get(url, timeout=35)
    except Exception as e:
        print("ERR", url, e); return None
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "html.parser")


def download(src, prefix):
    if not src: return None
    url = urljoin(BASE, src)
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"): ext = ".jpg"
    name = f"{prefix}-{hashlib.md5(url.encode()).hexdigest()[:10]}{ext}"
    p = os.path.join(IMG, name)
    if os.path.exists(p): return name
    try:
        r = S.get(url, timeout=45)
        if r.status_code == 200 and len(r.content) > 900:
            open(p, "wb").write(r.content); return name
    except Exception: pass
    return None


def page(url, prefix):
    """Достаёт заголовок, текст, контакты и фото со страницы подразделения."""
    s = get(url)
    if not s: return None
    h = s.find("h1")
    info = {}
    for it in s.select(".info-contacts__item"):
        t = clean(it.get_text(" "))
        m = re.match(r"(Руководитель|Директор|Начальник|Заведующий|Телефон|E-?mail|"
                     r"Аудитория|Внутренний телефон|Адрес|Часы работы)\s*:?\s*(.+)", t, re.I)
        if m: info[m.group(1).lower()] = m.group(2)
    paras = [clean(p.get_text()) for p in s.find_all("p")]
    photos = []
    for im in s.select('img[src*="/upload/"]'):
        f = download(im.get("src"), prefix)
        if f and f not in photos and len(photos) < 4: photos.append(f)
    return {
        "title": clean(h.get_text()) if h else "",
        "url": url,
        "info": info,
        "text": "\n\n".join([p for p in paras if len(p) > 45][:8])[:2200],
        "photos": photos,
    }


TARGETS = {
    "choir":    ("Академический хор МИЭТа", f"{BASE}/structure/s/354/e/32354/113"),
    "theatre":  ("Театральная студия «ПОЭМИМЫ»", f"{BASE}/structure/s/354/e/153336/113"),
    "dance":    ("Школа танцев Виталия Сурмы", f"{BASE}/structure/s/354/e/153344/113"),
    "dk_sched": ("Расписание занятий в ДК", f"{BASE}/structure/s/354/e/158540/113"),
    "pool":     ("Бассейн", f"{BASE}/structure/s/355/e/82090/114"),
    "halls":    ("Залы и спортивные площадки", f"{BASE}/structure/s/355/e/82095/114"),
    "sport_ab": ("О спорткомплексе", f"{BASE}/structure/s/355/e/4109/114"),
    "dorm_ab":  ("О студгородке", f"{BASE}/structure/s/353/e/4084/112"),
    "canteen_ab": ("О столовой", f"{BASE}/structure/s/357/e/4119/116"),
    "prof":     ("Профком студентов", f"{BASE}/structure/s/1905/e/50497/355"),
    "lib_rules": ("Правила пользования библиотекой", f"{BASE}/structure/s/322/e/3282/102"),
    "today":    ("МИЭТ сегодня", f"{BASE}/page/104640"),
}

out = {}
for k, (title, url) in TARGETS.items():
    r = page(url, k)
    if r:
        r["label"] = title
        out[k] = r
        print(f"{k:11} {(r['title'] or title)[:46]:48} фото={len(r['photos'])} "
              f"текст={len(r['text'])}")

# ── поиск студенческих объединений по сайту ──
print("\n── поиск студобъединений")
found = []
for q in ["студенческие объединения", "студенческий совет", "студенческий актив"]:
    s = get(f"{BASE}/search/?q={requests.utils.quote(q)}")
    if not s: continue
    for a in s.select("a[href]"):
        t, h = clean(a.get_text()), a.get("href", "")
        if 12 < len(t) < 110 and ("/page/" in h or "/structure/" in h):
            u = urljoin(BASE, h)
            if not any(f[1] == u for f in found):
                found.append((t, u))
for t, u in found[:25]:
    print("  ", t[:70], "|", u)

json.dump({"pages": out, "search": found[:25]},
          open(os.path.join(DATA, "clubs.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nсохранено clubs.json")
