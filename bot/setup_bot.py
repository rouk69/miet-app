# -*- coding: utf-8 -*-
"""
Разовая настройка бота: команды, описание, кнопка меню.
Всё, что можно задать через Bot API, — здесь; включение inline-режима
через API невозможно, его даёт только @BotFather командой /setinline.

    python -m bot.setup_bot
"""
from __future__ import annotations

import sys

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

from .main import BOT_TOKEN, WEBAPP_URL

sys.stdout.reconfigure(encoding="utf-8")
bot = telebot.TeleBot(BOT_TOKEN)

COMMANDS = [
    ("today", "Пары на сегодня"),
    ("tomorrow", "Пары на завтра"),
    ("week", "Вся неделя"),
    ("group", "Сменить группу"),
    ("shift", "Поправка недели цикла"),
    ("help", "Как пользоваться"),
    ("support", "Связаться с автором"),
    ("post", "Написать пост в ленту"),
]

# До 512 символов. Видно в пустом чате с ботом, до первого сообщения.
DESCRIPTION = (
    "Расписание НИУ МИЭТ — прямо с miet.ru, всегда актуальное.\n\n"
    "• Пары на любой день и любую неделю четырёхнедельного цикла\n"
    "• Поиск по всем 346 группам\n"
    "• Работает в любом чате: напиши @mietapp_bot и вставь карточку\n"
    "• Мини-приложение: новости, 28 кружков, институты, кампус\n\n"
    "Нажми «Запустить» и отправь номер своей группы."
)

# До 120 символов. Показывается в профиле бота и в списке чатов.
SHORT_DESCRIPTION = (
    "Расписание МИЭТ с miet.ru: пары, недели цикла, 346 групп, "
    "новости и кружки в мини-приложении."
)


def main() -> None:
    me = bot.get_me()
    print(f"Бот: @{me.username} (id {me.id})\n")

    steps = []

    try:
        bot.set_my_commands([types.BotCommand(c, d) for c, d in COMMANDS])
        steps.append(("команды", f"{len(COMMANDS)} шт."))
    except ApiTelegramException as e:
        steps.append(("команды", f"ОШИБКА: {e}"))

    try:
        bot.set_my_description(DESCRIPTION)
        steps.append(("описание", f"{len(DESCRIPTION)} символов"))
    except ApiTelegramException as e:
        steps.append(("описание", f"ОШИБКА: {e}"))

    try:
        bot.set_my_short_description(SHORT_DESCRIPTION)
        steps.append(("краткое описание", f"{len(SHORT_DESCRIPTION)} символов"))
    except ApiTelegramException as e:
        steps.append(("краткое описание", f"ОШИБКА: {e}"))

    # Кнопка меню слева от поля ввода: либо мини-приложение, либо команды.
    try:
        if WEBAPP_URL:
            bot.set_chat_menu_button(menu_button=types.MenuButtonWebApp(
                type="web_app", text="Приложение",
                web_app=types.WebAppInfo(url=WEBAPP_URL)))
            steps.append(("кнопка меню", f"мини-приложение → {WEBAPP_URL}"))
        else:
            bot.set_chat_menu_button(menu_button=types.MenuButtonCommands(
                type="commands"))
            steps.append(("кнопка меню", "команды (WEBAPP_URL не задан)"))
    except ApiTelegramException as e:
        steps.append(("кнопка меню", f"ОШИБКА: {e}"))

    for name, result in steps:
        mark = "✗" if result.startswith("ОШИБКА") else "✓"
        print(f"  {mark} {name:20} {result}")

    print()
    if me.supports_inline_queries:
        print("✓ inline-режим включён — бот работает в любом чате")
    else:
        print("✗ inline-режим ВЫКЛЮЧЕН. Через API его не включить.")
        print("  Открой @BotFather → /setinline → выбери @" + (me.username or "бота"))
        print("  → задай подсказку, например: группа — расписание")


if __name__ == "__main__":
    main()
