# -*- coding: utf-8 -*-
"""Сжимает фото и собирает data/app.json для мини-приложения."""
import json, os, re, sys, shutil, datetime
from PIL import Image

import icons_map

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_raw")
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_IMG = os.path.join(PROJ, "img")
OUT_DATA = os.path.join(PROJ, "data")
os.makedirs(OUT_IMG, exist_ok=True)
os.makedirs(OUT_DATA, exist_ok=True)

# Карточки на телефоне — 350–420 px шириной, даже с retina хватает 800.
# Лишние килобайты тут не бесплатны: студенты открывают приложение с мобильного.
MAXW = 800
raw = json.load(open(os.path.join(SRC, "miet.json"), encoding="utf-8"))
clubs_raw = json.load(open(os.path.join(SRC, "clubs.json"), encoding="utf-8"))["pages"]

# ─────────────── сжатие картинок ───────────────
mapping, kept = {}, 0
before = after = 0
for f in sorted(os.listdir(os.path.join(SRC, "img"))):
    p = os.path.join(SRC, "img", f)
    if not os.path.isfile(p):
        continue
    before += os.path.getsize(p)
    if f.lower().endswith(".svg"):
        shutil.copy(p, os.path.join(OUT_IMG, f))
        mapping[f] = f
        after += os.path.getsize(p)
        kept += 1
        continue
    try:
        im = Image.open(p)
        im.load()
    except Exception:
        continue
    if im.width < 120 or im.height < 90:      # иконки-обрезки, соцсети
        continue
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    name = os.path.splitext(f)[0] + ".jpg"
    op = os.path.join(OUT_IMG, name)
    if not os.path.exists(op):
        im.save(op, "JPEG", quality=72, optimize=True, progressive=True)
    mapping[f] = name
    after += os.path.getsize(op)
    kept += 1

print(f"картинок: {kept}   {before/1e6:.1f}MB → {after/1e6:.1f}MB")
mp = lambda f: mapping.get(f)
mps = lambda lst: [x for x in (mp(f) for f in (lst or [])) if x]


def phone(v):
    """Нормализует телефон и отбрасывает внутренние/факс-хвосты."""
    if not v:
        return None
    v = re.split(r",\s*(?:Внутренний|Факс)", v)[0].strip(" ,;")
    return v or None


def inner(v):
    m = re.search(r"Внутренний телефон:\s*([\d\-,\s]+)", v or "")
    return m.group(1).strip(" ,") if m else None


def mail(v):
    if not v:
        return None
    return re.split(r"[;,]", v)[0].strip()


SHORT = re.compile(r"\(([^)]{2,16})\)\s*$")


def split_short(name):
    """Отделяет аббревиатуру в хвостовых скобках: «… (ИнЭл)» → («…», «ИнЭл»)."""
    m = SHORT.search(name)
    if not m:
        return name, ""
    inner = m.group(1)
    caps = sum(1 for ch in inner if ch.isupper())
    if caps < 2 or (" " in inner.strip() and caps < 3):
        return name, ""
    return SHORT.sub("", name).strip(), inner.strip()

# ─────────────── институты ───────────────
institutes = []
for i, ins in enumerate(raw["institutes"]):
    name = ins["name"].strip()
    if not name:
        continue
    base, short = split_short(name)
    institutes.append({
        "id": f"inst{i}",
        "name": base,
        "short": short,
        "director": ins["info"].get("директор"),
        "phone": phone(ins["info"].get("телефон")),
        "inner": inner(ins["info"].get("телефон")),
        "room": ins["info"].get("аудитория"),
        "email": mail(ins["info"].get("e-mail")),
        "about": ins.get("about", "")[:700],
        "departments": ins.get("departments", [])[:20],
        "photo": mp(ins.get("photo")),
        "url": ins["url"],
    })
print("институтов:", len(institutes))

# ─────────────── новости ───────────────
MONTHS = {m: i + 1 for i, m in enumerate(
    ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
     "августа", "сентября", "октября", "ноября", "декабря"])}


def iso(d):
    m = re.match(r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})", (d or "").lower())
    if not m:
        return None
    return f"{m.group(3)}-{MONTHS.get(m.group(2), 1):02d}-{int(m.group(1)):02d}"


news = []
for n in raw["news"]:
    tags = [t.lstrip("#").strip() for t in n.get("tags", []) if 2 < len(t) < 34]
    news.append({
        "id": n["id"],
        "title": n["title"],
        "date": n["date"],
        "iso": iso(n["date"]),
        "cover": mp(n.get("cover")),
        "text": n.get("text", ""),
        "tags": list(dict.fromkeys(tags))[:4],
        "gallery": mps(n.get("gallery")),
        "url": n["url"],
    })
news = [n for n in news if n["title"]]
print("новостей:", len(news), "| с текстом:", sum(1 for n in news if n["text"]))

# ─────────────── кружки и секции ───────────────
def cp(key, **kw):
    p = clubs_raw.get(key, {})
    info = p.get("info", {})
    d = {
        "about": p.get("text", "")[:1500],
        "photos": mps(p.get("photos")),
        "url": p.get("url"),
        "lead": info.get("директор") or info.get("руководитель"),
        "phone": phone(info.get("телефон")),
        "email": mail(info.get("e-mail")),
        "room": info.get("аудитория"),
    }
    d.update(kw)
    return d


# Секции при подразделениях — у них свои страницы в структуре сайта.
# Хор и профком сюда не попадают: они есть среди студенческих сообществ
# ниже, там описание богаче и указаны соцсети.
clubs = [
    cp("theatre", id="theatre", title="Театральная студия «ПОЭМИМЫ»", cat="Творчество",
       emoji="🎭", tagline="Студенческий театр, основан в 1982 году", place="ДК МИЭТ"),
    cp("dance", id="dance", title="Школа танцев Виталия Сурмы", cat="Творчество",
       emoji="💃", tagline="Бальные танцы, подготовка к Балу МИЭТ",
       place="ДК МИЭТ", free="Бесплатно по студенческому"),
    cp("pool", id="pool", title="Бассейн", cat="Спорт", emoji="🏊",
       tagline="25 метров, 6 дорожек", place="Спорткомплекс"),
    cp("halls", id="halls", title="Игровые залы и площадки", cat="Спорт", emoji="⚽",
       tagline="Футбол, волейбол, баскетбол, большой теннис", place="Спорткомплекс"),
    cp("sport_ab", id="sport", title="Спорткомплекс МИЭТ", cat="Спорт", emoji="🏟",
       tagline="Стадион, тренажёрные залы, шейпинг, единоборства",
       place="Корпус 5, ауд. 5110"),
]

# ── студенческие сообщества (индекс /page/113391) ──
# Категории и краткие описания проставлены вручную: сайт классификацию
# даёт текстом в общем описании, а не полем у каждого объединения.
SC_META = {
    "Велоклуб Transmission": ("Спорт", "🚴", "Любительский и профессиональный велоспорт"),
    "Движение КВН МИЭТ": ("Творчество", "🎤", "Команда-чемпион открытой лиги КВН"),
    "Киберспортивное движение MIET Esports": ("Спорт", "🎮", "Турниры, тренировки, сборные университета"),
    "Клуб болельщиков «Электроток»": ("Спорт", "📣", "Поддержка сборных МИЭТ на играх"),
    "Клуб йоги «ОМ»": ("Спорт", "🧘", "Занятия в Студгородке по понедельникам и четвергам"),
    "Клуб настольных игр «Рудник»": ("Досуг", "🎲", "Настолки как интеллектуальный отдых"),
    "Клуб туризма и альпинизма «Полупроводник»": ("Спорт", "🏔", "Походы, альпинизм, сплавы, ориентирование"),
    "ПО «Движение Первых» НИУ МИЭТ": ("Объединения", "🚩", "Первичное отделение движения в МИЭТ"),
    "Студенческий академический хор МИЭТ": ("Творчество", "🎼", "Классика и эстрада, коллектив с 2000 года"),
    "Студенческий патриотический клуб «Я Горжусь»": ("Объединения", "🎖", "Патриотические проекты и акции памяти"),
    "Студенческое научное общество": ("Наука", "🔬", "Исследования, конференции, научные проекты"),
    "Студклуб РСМ": ("Объединения", "🤝", "Российский союз молодёжи в МИЭТ"),
    "Экологическое движение МИЭТ": ("Добро", "♻️", "Эко-просвещение и раздельный сбор"),
    "Вожатский отряд «БиТ»": ("Добро", "🏕", "Вожатская работа в лагерях с 2011 года"),
    "Спортивный клуб «Электрон»": ("Спорт", "🏅", "Сборные МИЭТ, соревнования, АССК"),
    "Клуб интеллектуальных игр": ("Досуг", "🧠", "«Что? Где? Когда?», брейн-ринг, своя игра"),
    "Донорское движение": ("Добро", "🩸", "Дни донора и донорские акции"),
    "ИНверсия": ("Медиа", "📰", "Студенческая газета, выходит с 2001 года"),
    "Фотоклуб inFocus": ("Медиа", "📷", "Съёмки, разборы, фотовыставки"),
    "МИЭТ-ТВ": ("Медиа", "🎬", "Видеостудия университета"),
    "Профком": ("Объединения", "🛡", "Защита прав, матпомощь, путёвки"),
    "Добро.Центр": ("Добро", "💚", "Волонтёрство и социальные проекты"),
    "Студенческий совет МИЭТ": ("Объединения", "🗳", "Самоуправление, ауд. 3352"),
}

# контакты подразделений, к которым сообщество приписано
SC_CONTACTS = {
    "Студенческий академический хор МИЭТ": ("dk", "ДК МИЭТ"),
    "Профком": ("uvd", "Ауд. 1206"),
}

sc_path = os.path.join(SRC, "student_clubs.json")
if os.path.exists(sc_path):
    sc_raw = json.load(open(sc_path, encoding="utf-8"))
    for key, v in sc_raw.items():
        name = v.get("name", "").strip()
        cat, emoji, tagline = SC_META.get(name, ("Объединения", "✨", ""))
        entry = {
            "id": key,
            "title": name,
            "cat": cat,
            "emoji": emoji,
            "tagline": tagline,
            "about": re.sub(r"\s*\n\s*\n\s*", "\n\n", v.get("text", "")).strip(),
            "photos": mps(v.get("photos")),
            "social": v.get("social", [])[:3],
            "url": v.get("url"),
            "email": v.get("email"),
            "room": v.get("room"),
            "lead": None,
            "phone": None,
        }
        sec_key, place = SC_CONTACTS.get(name, (None, None))
        if sec_key:
            sec = raw["sections"].get(sec_key, {})
            si = sec.get("info", {})
            entry["place"] = place
            entry["lead"] = si.get("директор") or si.get("руководитель")
            entry["phone"] = phone(si.get("телефон"))
            entry["email"] = entry["email"] or mail(si.get("e-mail"))
            entry["room"] = entry["room"] or si.get("аудитория")
        clubs.append(entry)
else:
    print("! student_clubs.json не найден — запусти tools/student_clubs.py")

for c in clubs:
    c["about"] = re.sub(r"\s*\n\s*\n\s*", "\n\n", c.get("about", "")).strip()
    c.setdefault("social", [])
    c["icon"] = icons_map.CLUBS.get(
        c["title"], icons_map.CLUB_CATEGORY.get(c["cat"], "sparkles"))

CAT_ORDER = ["Спорт", "Творчество", "Медиа", "Наука", "Добро", "Досуг", "Объединения"]
clubs.sort(key=lambda c: (CAT_ORDER.index(c["cat"]) if c["cat"] in CAT_ORDER else 99,
                          c["title"]))
from collections import Counter as _C
print("кружков:", len(clubs), "|", dict(_C(c["cat"] for c in clubs)))

# ─────────────── кампус ───────────────
CAMPUS_META = {
    "library":    ("Библиотека", "📚", "500 тыс. изданий, читальные залы, электронный каталог"),
    "canteen":    ("Столовая", "🍽", "Залы и 7 буфетов по корпусам"),
    "dorm":       ("Общежития", "🏠", "Ул. Юности 7–15, 15 минут до МИЭТа"),
    "health":     ("Здравпункт", "🩺", "Медпомощь для студентов и сотрудников"),
    "sanatorium": ("Санаторий-профилакторий", "🌿", "Оздоровление без отрыва от учёбы"),
    "career":     ("Центр развития карьеры", "💼", "Стажировки, вакансии, консультации"),
    "scholarship":("Стипендии", "💰", "Виды стипендий и порядок назначения"),
    "social":     ("Социальная поддержка", "🛟", "Льготы, матпомощь, поддержка студентов"),
    "sport":      ("Спорткомплекс", "🏟", "Бассейн, залы, стадион"),
    "dk":         ("Дом культуры", "🎭", "Зал на 640 мест, кружки и коллективы"),
}
campus = []
for key, (title, emoji, sub) in CAMPUS_META.items():
    s = raw["sections"].get(key)
    if not s:
        continue
    info = s.get("info", {})
    campus.append({
        "id": key, "title": title, "emoji": emoji, "sub": sub,
        "icon": icons_map.CAMPUS.get(key, "building"),
        "lead": info.get("директор") or info.get("руководитель") or info.get("начальник"),
        "phone": phone(info.get("телефон")),
        "inner": inner(info.get("телефон")),
        "email": mail(info.get("e-mail")),
        "room": info.get("аудитория"),
        "text": re.sub(r"\s*\n\s*\n\s*", "\n\n", s.get("text", "")).strip()[:2200],
        "photos": mps(s.get("photos")),
        "links": s.get("links", [])[:12],
        "url": s["url"],
    })
print("разделов кампуса:", len(campus))

# ─────────────── университет ───────────────
about = clubs_raw.get("today", {}).get("text", "")
university = {
    "name": "Национальный исследовательский университет «МИЭТ»",
    "short": "НИУ МИЭТ",
    "full": "Федеральное государственное автономное образовательное учреждение высшего "
            "образования «Национальный исследовательский университет «Московский институт "
            "электронной техники»",
    "founded": "9 декабря 1965",
    "address": "124498, Москва, Зеленоград, площадь Шокина, дом 1",
    "phone": "+7 (499) 720-85-88",
    "email": "kanc@miee.ru",
    "site": "https://www.miet.ru",
    "about": about[:1400],
    "facts": [
        {"k": "1965", "v": "год основания"},
        {"k": "16", "v": "институтов"},
        {"k": "346", "v": "учебных групп"},
        {"k": "500 тыс.", "v": "изданий в библиотеке"},
    ],
}

# ─────────────── полезные ссылки ───────────────
# Проверены запросом: /sport/, /dk/ и /contacts/ на сайте отдают 404,
# поэтому вместо них стоят реальные страницы этих подразделений.
LINKS = [
    ("Сервисы", "⚡", [
        ("ОРИОКС", "Оценки, баллы и учебный процесс", "https://orioks.miet.ru/main/login", "📊"),
        ("Личный кабинет", "Справки, заявления, оплата", "https://account.miet.ru/", "🔑"),
        ("Расписание на сайте", "Первоисточник, miet.ru/schedule", "https://www.miet.ru/schedule/", "📅"),
        ("Электронная библиотека", "Полнотекстовый доступ, elib.miet.ru", "https://elib.miet.ru/MegaPro2/Web", "📖"),
        ("Электронные ресурсы", "Подписные базы библиотеки", "https://www.miet.ru/structure/s/322/e/20118/102", "🗄"),
    ]),
    ("Учёба", "🎓", [
        ("Образовательные программы", "Направления и профили подготовки", "https://www.miet.ru/page/55899", "📚"),
        ("Документы", "Приказы, положения, регламенты", "https://www.miet.ru/sveden/document", "📄"),
        ("Сведения об образовательной организации", "Обязательный раздел", "https://miet.ru/sveden/", "📋"),
        ("Методические документы", "Обеспечение учебного процесса", "https://www.miet.ru/page/56599", "📝"),
        ("Перевод и восстановление", "Между программами и из другого вуза", "https://miet.ru/page/104684", "🔀"),
        ("Стипендии", "Виды и порядок назначения", "https://www.miet.ru/page/34799", "💰"),
        ("Частые вопросы", "ЧаВо для студентов", "https://www.miet.ru/page/106431", "❓"),
    ]),
    ("Студенту", "🎒", [
        ("Портал «Студентам»", "Все студенческие сервисы", "https://www.miet.ru/special/students", "🧭"),
        ("Студенческий офис", "Справки и документы", "https://www.miet.ru/structure/s/320", "🏢"),
        ("Студенческий совет", "Самоуправление, ауд. 3352", "https://miet.ru/page/105283", "🗳"),
        ("Студенческие сообщества", "Каталог клубов и объединений", "https://miet.ru/page/113391", "✨"),
        ("Молодёжный центр", "Мероприятия и проекты", "https://www.miet.ru/structure/s/3451/e/155021/446", "🎪"),
        ("Психологическая служба", "Бесплатная помощь студентам", "https://www.miet.ru/page/149790", "🧠"),
        ("Здоровый МИЭТ", "Программы здоровья", "https://www.miet.ru/page/154625", "💚"),
        ("Поддержка студенческих семей", "Льготы и помощь", "https://www.miet.ru/page/168223", "👨‍👩‍👧"),
        ("Открытый диалог", "Вопрос администрации напрямую", "https://www.miet.ru/page/149507", "💬"),
        ("Оплата услуг университета", "Как и за что платить", "https://www.miet.ru/page/156737", "💳"),
        ("Привет, МИЭТ", "Проект для первокурсников", "https://privet-miet.ru/", "👋"),
    ]),
    ("Общежитие", "🏠", [
        ("Студгородок", "Ул. Юности 7–15", "https://www.miet.ru/structure/s/353", "🏘"),
        ("Поселение в общежитие", "Порядок и документы", "https://miet.ru/page/146275", "🔑"),
        ("Положение о Студгородке", "Правила проживания", "https://www.miet.ru/structure/s/353/e/53374/112", "📜"),
    ]),
    ("Поступающим", "📥", [
        ("Приёмная комиссия", "abit.miet.ru · 8 (800) 600-56-89", "https://abit.miet.ru/", "📨"),
        ("Списки поступающих", "Ранжированные списки", "https://abit.miet.ru/main_pages/lists.php", "📊"),
        ("Абитуриенту", "abiturient.ru", "https://www.abiturient.ru/", "🎯"),
        ("Школьникам", "Олимпиады, курсы, кружки", "https://www.miet.ru/special/school", "🏫"),
    ]),
    ("Университет", "🏛", [
        ("Сайт МИЭТ", "miet.ru", "https://www.miet.ru/", "🌐"),
        ("Новости", "Лента университета", "https://www.miet.ru/news/", "📰"),
        ("Организационная структура", "Институты, кафедры, отделы", "https://www.miet.ru/structure/", "🗂"),
        ("Контактная информация", "Реквизиты и телефоны", "https://www.miet.ru/page/1127", "📞"),
        ("Библиотека", "Фонды и читальные залы", "https://www.miet.ru/structure/s/322", "📚"),
        ("Спортивный комплекс", "Бассейн, залы, стадион", "https://www.miet.ru/structure/s/355", "🏟"),
        ("Дом культуры", "Зал на 640 мест", "https://www.miet.ru/structure/s/354", "🎭"),
        ("Центр развития карьеры", "Стажировки и вакансии", "https://www.miet.ru/structure/s/3450", "💼"),
        ("Выпускникам", "miet.pro", "http://miet.pro/", "🎓"),
    ]),
]

links = [{
    "title": group,
    "emoji": emoji,
    "icon": icons_map.LINK_GROUPS.get(group, "link"),
    "items": [{"title": t, "sub": s, "url": u, "emoji": e,
               "icon": icons_map.BY_EMOJI.get(e, "link")}
              for t, s, u, e in items],
} for group, emoji, items in LINKS]
print("ссылок:", sum(len(g["items"]) for g in links), "в", len(links), "группах")

app = {
    "meta": {
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "https://www.miet.ru",
        "schedule_api": "https://miet.ru/schedule",
    },
    "university": university,
    "news": news,
    "institutes": institutes,
    "clubs": clubs,
    "campus": campus,
    "links": links,
    "groups": raw["groups"],
}
p = os.path.join(OUT_DATA, "app.json")
json.dump(app, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"\ndata/app.json — {os.path.getsize(p)/1024:.0f} KB")
print("групп:", len(app["groups"]))
