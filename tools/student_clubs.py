# -*- coding: utf-8 -*-
"""
Студенческие сообщества МИЭТ — 20+ клубов с отдельными страницами.
Индекс живёт на /page/113391 (портал «Студенту» → «Студенческая жизнь»),
в структуре сайта его нет, поэтому и не находился раньше.
"""
import hashlib, json, os, re, sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://www.miet.ru"
INDEX = "https://miet.ru/page/113391"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "_raw")
IMG = os.path.join(DATA, "img")
os.makedirs(IMG, exist_ok=True)

clean = lambda t: re.sub(r"\s+", " ", t or "").strip()


def soup_of(url):
    try:
        r = S.get(url, timeout=35)
    except Exception as e:
        print("  ERR", url, e)
        return None
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "html.parser")


def download(src, prefix):
    if not src:
        return None
    url = urljoin(BASE, src)
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    name = f"{prefix}-{hashlib.md5(url.encode()).hexdigest()[:10]}{ext}"
    path = os.path.join(IMG, name)
    if os.path.exists(path):
        return name
    try:
        r = S.get(url, timeout=45)
        if r.status_code == 200 and len(r.content) > 3000:
            open(path, "wb").write(r.content)
            return name
    except Exception:
        pass
    return None


# Хлебные крошки и общий каркас есть на каждой странице — не считаем их
# содержимым конкретного клуба.
SKIP_TITLES = {"НИУ МИЭТ", "Студенту", "Студенческая жизнь", "Общие сведения",
               "Студенческие сообщества", "Полная версия", "Войти", "Школьникам",
               "Поступающим", "Студентам", "Преподавателям", "Сотрудникам",
               "Партнерам", "Выпускникам"}


def club_page(url, key):
    s = soup_of(url)
    if not s:
        return None
    for junk in s.select("script, style, .site-header, .header-menu, "
                         ".toggable-list, .site-footer, footer, header, "
                         ".page-navigation, .site-sidebar"):
        junk.decompose()

    h1 = s.find("h1")
    title = clean(h1.get_text()) if h1 else ""

    paras = []
    for p in s.find_all(["p", "li"]):
        t = clean(p.get_text())
        if len(t) > 45 and t not in paras:
            paras.append(t)
    text = "\n\n".join(paras[:10])[:2000]

    photos = []
    for im in s.select('img[src*="/upload/"]'):
        f = download(im.get("src"), key)
        if f and f not in photos and len(photos) < 4:
            photos.append(f)

    # соцсети клуба — обычно единственный живой способ туда попасть
    social = []
    for a in s.find_all("a", href=True):
        h = a["href"]
        if re.search(r"(vk\.com|t\.me|telegram\.me|instagram\.com|youtube\.)", h):
            label = ("ВКонтакте" if "vk.com" in h
                     else "Telegram" if "t.me" in h or "telegram" in h
                     else "YouTube" if "youtube" in h else "Соцсеть")
            if not any(x["url"] == h for x in social):
                social.append({"label": label, "url": h})

    contacts = {}
    body = s.get_text(" ", strip=True)
    m = re.search(r"аудитори[июя]\s*№?\s*([0-9]{3,4}[а-яА-Я]?)", body, re.I)
    if m:
        contacts["room"] = m.group(1)
    m = re.search(r"[\w.\-]+@[\w.\-]+\.\w{2,}", body)
    if m:
        contacts["email"] = m.group(0)

    return {"title": title, "url": url, "text": text, "photos": photos,
            "social": social[:3], **contacts}


def page_links(soup):
    """Все ссылки вида /page/N на странице."""
    out = {}
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if re.match(r"^/page/\d+", h):
            t = clean(a.get_text())
            if len(t) >= 4:
                out.setdefault(h, t)
    return out


def main():
    s = soup_of(INDEX)
    if not s:
        sys.exit("Индекс сообществ не открылся")

    # Шапка и подвал одинаковы на всех страницах сайта, а «своих» ссылок
    # у обычной страницы нет — поэтому вычитаем её набор из набора индекса
    # и получаем ровно список сообществ, без хардкода id.
    chrome = soup_of(f"{BASE}/page/1127")
    common = set(page_links(chrome)) if chrome else set()

    links = [(t, urljoin(BASE, h))
             for h, t in page_links(s).items()
             if h not in common and t not in SKIP_TITLES]

    print(f"нашлось сообществ: {len(links)}\n")
    out = {}
    for i, (name, url) in enumerate(links):
        key = f"sc{i}"
        r = club_page(url, key)
        if not r:
            continue
        r["name"] = name
        out[key] = r
        print(f"  {name[:44]:46} фото={len(r['photos'])} "
              f"текст={len(r['text']):>4} соцсети={len(r['social'])}")

    # студсовет — не в списке сообществ, но это их зонтичный орган
    sov = club_page("https://miet.ru/page/105283", "studsovet")
    if sov:
        sov["name"] = "Студенческий совет МИЭТ"
        out["studsovet"] = sov
        print(f"  {'Студенческий совет МИЭТ':46} фото={len(sov['photos'])} "
              f"текст={len(sov['text'])}")

    p = os.path.join(DATA, "student_clubs.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nсохранено: {p} — {len(out)} сообществ")


if __name__ == "__main__":
    main()
