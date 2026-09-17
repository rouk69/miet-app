# -*- coding: utf-8 -*-
"""
Режет справочник на то, что нужно сразу, и то, что нужно потом.

`data/app.json` весит 166 КБ, и приложение ждало его целиком, прежде чем
нарисовать первый экран. Внутри — 107 КБ длинных текстов: полные тексты
шестидесяти новостей, описания двадцати восьми кружков, рассказы про
кампус и институты. Всё это читают ровно в одном случае — когда открыли
конкретную карточку, то есть почти никогда на старте.

Скрипт собирает из него два файла:

  data/core.json   то же самое без длинных полей — с ним открывается
                   приложение;
  data/texts.json  только длинные поля, ключ «вид:номер» — грузится
                   фоном после первого экрана.

`data/app.json` остаётся нетронутым: он исходник, его собирают
`tools/harvest.py` и соседи, и он же запасной путь для клиента, который
не смог получить core.

Зовётся из `tools/stamp.py` перед каждой выкладкой — вместе со сборкой
модулей, чтобы разрез не мог отстать от данных.

    python tools/split_texts.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Какие поля считаем длинными. Проверено по составу файла: на них
# приходится 64% его веса, и ни одно не нужно ни на главной, ни в
# списках — только в открытой карточке.
LONG = {
    "news": ("text",),
    "clubs": ("about",),
    "campus": ("text",),
    # departments не выносим: список институтов показывает их число
    # прямо в плитке, и без них там был бы пустой чип. Три
    # килобайта того не стоят.
    "institutes": ("about",),
}

# Короче этого не выносим: ключ в texts.json и сам займёт место, а
# лишний поход в сеть за двумя строчками ничего не сэкономит.
MIN_LEN = 200


def key_of(kind: str, item: dict, pos: int) -> str:
    """
    Чем адресуется текст. Свой `id` записи, если он есть, иначе позиция.

    Позиция — запасной путь и слабое место: пересортируй справочник, и
    тексты разъедутся. Поэтому у всего, что собирают скрипты, `id` есть.
    """
    got = item.get("id")
    return f"{kind}:{got if got not in (None, '') else pos}"


def split(app: dict) -> tuple:
    core = dict(app)
    texts = {}
    for kind, fields in LONG.items():
        items = app.get(kind)
        if not isinstance(items, list):
            continue
        short = []
        for pos, item in enumerate(items):
            if not isinstance(item, dict):
                short.append(item)
                continue
            copy = dict(item)
            for field in fields:
                value = copy.get(field)
                raw = value if isinstance(value, str) else (
                    json.dumps(value, ensure_ascii=False) if value else "")
                if not raw or len(raw) < MIN_LEN:
                    continue
                texts[f"{key_of(kind, item, pos)}:{field}"] = value
                copy.pop(field, None)
            short.append(copy)
        core[kind] = short
    return core, texts


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.join(ROOT, "data", "app.json")
    with open(src, encoding="utf-8") as f:
        app = json.load(f)

    core, texts = split(app)
    out = {}
    for name, payload in (("core.json", core), ("texts.json", texts)):
        path = os.path.join(ROOT, "data", name)
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        out[name] = len(body.encode("utf-8"))

    was = os.path.getsize(src)
    print(f"было {was // 1024} КБ → на старте {out['core.json'] // 1024} КБ, "
          f"текстов {out['texts.json'] // 1024} КБ ({len(texts)} шт.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
