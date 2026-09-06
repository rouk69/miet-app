# -*- coding: utf-8 -*-
"""
Публикация постов из бота: команда /post.

Зачем это, когда в приложении есть полноценный редактор: писать в ленту
чаще всего нужно на ходу и коротко — «завтра пар нет», «сбор в 10 у
главного». Открывать для этого мини-приложение дольше, чем отправить
сообщение боту.

Разговор ведётся простым состоянием на пользователя, без FSM-библиотек:
шагов три, живут они минуты, и тащить ради этого зависимость незачем.
Состояние в памяти процесса — незаконченный черновик переживать
перезапуск не обязан.

Картинка: если к посту нужна фотография, человек просто отправляет её
следующим сообщением — Telegram отдаёт файл, бот забирает и кладёт в то
же хранилище, куда складывает картинки мини-приложение.
"""
from __future__ import annotations

import logging
import threading
import time

from telebot import types

from . import analytics
from . import media as mediastore
from . import posts

log = logging.getLogger("miet.publish")

# Черновики: user_id → что уже собрано. Под замком, потому что telebot
# обрабатывает сообщения в нескольких потоках.
_drafts: dict[int, dict] = {}
_lock = threading.Lock()

# Брошенный черновик не должен висеть вечно и удивлять человека через
# сутки: «а, я же начинал писать пост».
TTL = 30 * 60


def _now() -> float:
    return time.monotonic()


def draft_of(user_id: int) -> dict | None:
    with _lock:
        d = _drafts.get(user_id)
        if d and _now() - d["at"] > TTL:
            del _drafts[user_id]
            return None
        return d


def start(user_id: int, label: str) -> None:
    with _lock:
        _drafts[user_id] = {"step": "text", "text": "", "media": "",
                            "anon": False, "at": _now()}


def drop(user_id: int) -> None:
    with _lock:
        _drafts.pop(user_id, None)


def _touch(d: dict) -> None:
    d["at"] = _now()


def keyboard_after_text() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("Опубликовать", callback_data="post:go"),
           types.InlineKeyboardButton("Анонимно", callback_data="post:anon"))
    kb.row(types.InlineKeyboardButton("Отмена", callback_data="post:cancel"))
    return kb


def take_text(user_id: int, text: str) -> bool:
    d = draft_of(user_id)
    if not d or d["step"] != "text":
        return False
    d["text"] = text.strip()
    d["step"] = "ready"
    _touch(d)
    return True


def take_photo(user_id: int, blob: bytes) -> bool:
    """Прикрепляет фотографию к черновику. Возвращает False, если его нет."""
    d = draft_of(user_id)
    if not d:
        return False
    try:
        d["media"] = mediastore.store(blob)
    except ValueError as e:
        log.info("фотография не принята: %s", e)
        return False
    _touch(d)
    return True


def publish(user_id: int, me: dict, label: str) -> dict:
    """
    Публикует черновик. Возвращает созданный пост.

    Аудиторию из бота не спрашиваем: выбор из трёхсот сорока шести групп
    кнопками — это отдельный экран, и он уже есть в мини-приложении.
    Пост из бота виден всем; кому нужна выборка, тот пишет из приложения.
    """
    d = draft_of(user_id)
    if not d or not (d["text"] or d["media"]):
        raise posts.Refused("Черновик пуст")
    post = posts.create(
        user_id, d["text"], anon=d["anon"], media=d["media"],
        author_label=label,
        may_publish_anon=analytics.can(me, "posts_anon"))
    drop(user_id)
    return post
