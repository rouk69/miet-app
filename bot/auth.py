# -*- coding: utf-8 -*-
"""
Проверка подписи Telegram WebApp initData — единственная серверная вещь,
которую нельзя сделать неправильно: без неё любой может подделать чужого
пользователя.

Сейчас мини-приложение работает без бэкенда и личных данных не запрашивает,
так что функция здесь про запас — она понадобится в тот момент, когда
появится сервер, отдающий что-то персональное (оценки, заявления, оплату).

Сам бот живёт в bot/main.py.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data: str, bot_token: str, max_age: int = 86400):
    """
    Проверяет подпись Telegram WebApp initData.
    Возвращает словарь пользователя или None, если подпись не сходится.

    Telegram считает HMAC от отсортированных пар «ключ=значение», где ключом
    служит HMAC('WebAppData') от токена бота. Сравнивать нужно постоянным
    по времени сравнением, иначе подпись можно подобрать по таймингам.
    """
    if not init_data or not bot_token:
        return None

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Сравниваем байтами: compare_digest на строке с не-ASCII символами
    # бросает TypeError, и подпись вида hash=деадбиф роняла бы обработчик
    # вместо честного отказа. Настоящий hash шестнадцатеричный, так что всё,
    # что не кодируется в ASCII, заведомо не подходит.
    try:
        given = received_hash.encode("ascii")
    except UnicodeEncodeError:
        return None
    if not hmac.compare_digest(expected.encode("ascii"), given):
        return None

    # Просроченный initData принимать нельзя: перехваченную строку иначе
    # можно переиспользовать сколько угодно долго.
    try:
        if max_age and time.time() - int(pairs.get("auth_date", 0)) > max_age:
            return None
    except (TypeError, ValueError):
        return None

    try:
        return json.loads(pairs["user"])
    except (KeyError, json.JSONDecodeError):
        return None
