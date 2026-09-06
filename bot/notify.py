# -*- coding: utf-8 -*-
"""
Отправка личных сообщений из серверной части.

HTTP-API живёт в том же процессе, что и бот, но импортировать `main` он не
может: это замкнуло бы круг (main → api → main). Поэтому здесь пустой
почтальон, которого бот при старте заменяет собой.

Пока замены нет — например, в тестах — сообщения просто не уходят, и это
правильно: проверка ленты не должна зависеть от наличия Telegram.
"""
from __future__ import annotations

import logging

log = logging.getLogger("miet.notify")

_send = None


def bind(fn) -> None:
    """Бот отдаёт сюда свою отправку сообщений."""
    global _send
    _send = fn


def to_user(user_id: int, text: str) -> bool:
    """
    Пишет человеку в личку. Возвращает, ушло ли.

    Ошибку не поднимает: уведомление — приятная мелочь, и если человек
    закрыл личку боту или Telegram недоступен, комментарий всё равно
    должен сохраниться.
    """
    if not _send or not user_id:
        return False
    try:
        _send(int(user_id), text)
        return True
    except Exception as e:                        # noqa: BLE001
        log.info("уведомление %s не ушло: %s", user_id, e)
        return False
