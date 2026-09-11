# -*- coding: utf-8 -*-
"""
Отправляет промо-карточку с подписью себе в Telegram.

    python promo/send.py           → карточка + подпись на премиум-эмодзи
    python promo/send.py --plain   → то же обычными значками

Зачем отдельный скрипт: пост набирается один раз, а отправить его себе
нужно каждый раз, когда меняется текст или картинка, — и отправить
именно так, как его увидит читатель, вместе с премиум-эмодзи. Копировать
разметку руками в этом случае бесполезно: Telegram Desktop вставит её
как обычный текст.

Значки берутся из `bot/emoji.py` — того же набора, что бот рисует в
расписании. Человек видит одни и те же иконки в посте и внутри бота, и
это читается как одно целое. Если Telegram премиум-эмодзи не примет
(их разрешают не всякому имени бота), скрипт отправит те же строки
запасными обычными: набор хранит пару как раз для этого.
"""
from __future__ import annotations

import io
import json
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from bot import emoji as em                                    # noqa: E402

# Кому слать. Свой же id: это черновик поста, а не рассылка.
OWNER = int(os.environ.get("PROMO_TO") or 5133646963)

CARD = os.path.join(HERE, "mietapp-card.png")

# Строки списка: (значок, текст). Порядок — по тому, как часто этим
# пользуются, а не по тому, чем приятнее хвастаться.
ROWS = [
    ("calendar", "расписание всех 346 групп и ближайшая пара"),
    ("time", "окна между парами — видно, сколько ждать"),
    ("bell", "утром в 7:30 бот сам пришлёт день"),
    ("list", "задания и сроки из ОРИОКС"),
    ("other", "файлы преподавателей: условия, методички"),
    ("teacher", "где сейчас преподаватель и свободна ли аудитория"),
    ("star", "калькулятор БРС — сколько ещё набрать"),
    ("people", "новости, кружки, чаты и доска взаимопомощи"),
    ("chat", "работает в любом чате: @mietapp_bot и группа"),
]


def token() -> str:
    for line in io.open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        if line.startswith("BOT_TOKEN"):
            return line.split("=", 1)[1].strip()
    sys.exit("В .env нет BOT_TOKEN")


def caption(custom: bool = True) -> str:
    ico = lambda name: em.ico(name, custom)                    # noqa: E731
    body = "\n".join(f"{ico(name)} {text};" for name, text in ROWS)
    return (
        f"{ico('graduate')} <b>МИЭТ проще с одним ботом</b>\n\n"
        "<i>Если надоело искать расписание по чатам, выяснять, в какой "
        "аудитории сидит преподаватель, и по сто раз заходить в ОРИОКС — "
        "попробуй @mietapp_bot.</i>\n\n"
        f"{ico('sparkle')} <b>Внутри уже есть:</b>\n\n"
        f"<blockquote>{body}</blockquote>\n\n"
        "<b>Короче, всё важное для студента МИЭТ — в одном месте.</b>\n\n"
        f"{ico('app')} Открыть: @mietapp_bot"
    )


def main() -> int:
    plain = "--plain" in sys.argv
    if not os.path.exists(CARD):
        sys.exit(f"Нет картинки {CARD} — собери её: python promo/render.py")

    # Сначала с премиум-эмодзи, при отказе — обычными. Второй заход
    # нужен редко, но узнать об отказе постфактум неоткуда: Telegram
    # отклоняет сообщение целиком, а не заменяет значки.
    for custom in ((False,) if plain else (True, False)):
        text = caption(custom)
        with open(CARD, "rb") as f:
            r = requests.post(
                f"https://api.telegram.org/bot{token()}/sendPhoto",
                data={"chat_id": OWNER, "caption": text, "parse_mode": "HTML"},
                files={"photo": ("mietapp-card.png", f, "image/png")},
                timeout=120)
        out = r.json()
        if out.get("ok"):
            kind = "обычными значками" if not custom else "с премиум-эмодзи"
            print(f"отправлено {kind}: сообщение {out['result']['message_id']}")
            return 0
        print("не прошло:", json.dumps(out, ensure_ascii=False)[:200])
    return 1


if __name__ == "__main__":
    sys.exit(main())
