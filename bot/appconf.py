# -*- coding: utf-8 -*-
"""
Настройки приложения, которые владелец меняет на ходу.

Не переменные окружения: те требуют перезапуска контейнера и правки в
панели Amvera. Здесь то, что переключают по обстановке — например,
открыть ленту всем перед началом семестра и закрыть обратно, если пошёл
поток мусора.

Значения лежат в базе, а не в памяти: перезапуск бота не должен молча
возвращать ленту в прежний режим.
"""
from __future__ import annotations

from .db import conn

# Ключ → (значение по умолчанию, подпись для админки, пояснение).
# Порядок задаёт вид экрана настроек.
FLAGS = {
    "posts_open": (
        False,
        "Писать посты могут все",
        "Иначе — только те, кому выдано право «Писать посты в ленту»",
    ),
    "posts_premoderate": (
        False,
        "Все посты — после одобрения",
        "Каждая запись попадает в очередь модерации, включая не анонимные. "
        "На тех, кто сам одобряет посты, не распространяется",
    ),
}

DEFAULTS = {k: v[0] for k, v in FLAGS.items()}


def all_flags() -> dict:
    """Текущие значения. Неизвестные ключи из базы игнорируются."""
    saved = dict(conn().execute(
        "SELECT key, value FROM index_meta WHERE key LIKE 'flag:%'"))
    out = {}
    for key, (default, _, _) in FLAGS.items():
        raw = saved.get("flag:" + key)
        out[key] = default if raw is None else raw == "1"
    return out


def get(key: str) -> bool:
    return all_flags().get(key, DEFAULTS.get(key, False))


def set_flag(key: str, value: bool) -> None:
    if key not in FLAGS:
        raise KeyError(key)
    conn().execute(
        """INSERT INTO index_meta (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        ("flag:" + key, "1" if value else "0"))


def described() -> list:
    """Настройки в виде, пригодном для показа: значение плюс подписи."""
    now = all_flags()
    return [{"key": key, "value": now[key], "title": title, "note": note}
            for key, (_, title, note) in FLAGS.items()]
