# -*- coding: utf-8 -*-
"""
Проверяет все ссылки, вшитые в экраны приложения.

Каталог ссылок собирается скриптами и проверяется links_probe.py, а вот
адреса, записанные прямо в JavaScript — официальные каналы, справочник
первокурсника, контакты кураторов, — не проверял никто. Такие ссылки
тихо умирают: канал переименовали, страницу перенесли, и приложение
годами ведёт человека в никуда.

    python tools/check_links.py

Прогон трогает чужие сайты, поэтому в обычный набор проверок он не
входит: гонять его стоит перед выкладкой, когда правил эти экраны.
"""
import os
import re
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})

# Ссылки внутри кода, а не в данных: data/app.json проверяет links_probe.
LINK = re.compile(r"https?://[^\s'\"`<>)]+")

# Служебные адреса, которые ссылками не являются.
SKIP = ("telegram.org/js", "fonts.googleapis", "fonts.gstatic",
        "miet-bot-rouk.amvera.io", "yandex.ru/maps/?text=",
        "localhost", "127.0.0.1")

# Адреса, которые снаружи не проверяются, хотя работают у студентов.
# ОРИОКС рвёт TLS-соединение с чужих адресов — та же защита, из-за
# которой miet.ru молчит через VPN (см. CLAUDE.md). Считать их мёртвыми
# нельзя: проверка станет вечно красной и её перестанут запускать.
UNVERIFIABLE = {
    "orioks.miet.ru": "рвёт TLS с внешних адресов, у студентов работает",
    "account.miet.ru": "личный кабинет закрыт снаружи",
}


def collect() -> dict:
    found = {}
    for base, _, names in os.walk(os.path.join(ROOT, "js")):
        for name in sorted(names):
            if not name.endswith(".js"):
                continue
            path = os.path.join(base, name)
            with open(path, encoding="utf-8") as f:
                for url in LINK.findall(f.read()):
                    url = url.rstrip(".,;")
                    # Шаблонные строки вида t.me/${username} — это не адрес,
                    # а заготовка: подставлять в неё нечего.
                    if "${" in url or any(s in url for s in SKIP):
                        continue
                    found.setdefault(url, set()).add(
                        os.path.relpath(path, ROOT).replace("\\", "/"))
    return found


def main() -> int:
    links = collect()
    print(f"ссылок в коде: {len(links)}\n")
    dead, skipped = [], []
    for url, where in sorted(links.items()):
        excuse = next((why for host, why in UNVERIFIABLE.items() if host in url),
                      None)
        if excuse:
            print(f"  ~ пропуск {url}")
            print(f"            {excuse}")
            skipped.append(url)
            continue
        try:
            r = S.get(url, timeout=25, allow_redirects=True)
            code = r.status_code
        except Exception as e:                      # noqa: BLE001
            code = type(e).__name__
        ok = code == 200
        print(f"  {'✓' if ok else '✗'} {code} {url}")
        if not ok:
            dead.append((url, code, ", ".join(sorted(where))))

    print()
    if skipped:
        print(f"не проверялись (см. UNVERIFIABLE): {len(skipped)}")
    if dead:
        print(f"НЕ ОТКРЫВАЮТСЯ — {len(dead)}:")
        for url, code, where in dead:
            print(f"  {code}  {url}\n        в {where}")
        return 1
    print("все ссылки живы")
    return 0


if __name__ == "__main__":
    sys.exit(main())
