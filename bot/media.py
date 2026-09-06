# -*- coding: utf-8 -*-
"""
Картинки постов: приём, хранение, раздача.

Файлы лежат в `DATA_DIR/media` — то есть в постоянном хранилище Amvera.
Всё, что не там, стирается при следующей выкладке, и лента осталась бы с
битыми картинками через неделю.

Имя файла — хеш содержимого. Так один и тот же снимок, присланный дважды,
занимает место один раз, а имя невозможно подобрать перебором.

Что принимаем и почему так строго: только JPEG, PNG, WebP и GIF, и тип
определяется по первым байтам, а не по расширению или заголовку от
клиента. Присланное имя — это то, что выбрал чужой человек; доверять ему
нельзя, иначе в хранилище окажется .html или .svg со скриптом внутри,
который потом откроется с нашего домена.
"""
from __future__ import annotations

import hashlib
import os

from . import paths

# 5 МБ — фотография с телефона после сжатия в это укладывается, а на
# постоянном хранилище Amvera лишние мегабайты стоят денег.
MAX_BYTES = 5 * 1024 * 1024

# Подписи форматов. Проверяем по содержимому: расширение ничего не значит.
SIGNATURES = [
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"GIF87a", "gif", "image/gif"),
    (b"GIF89a", "gif", "image/gif"),
]


def _sniff(blob: bytes):
    for sig, ext, mime in SIGNATURES:
        if blob.startswith(sig):
            return ext, mime
    # WebP: «RIFF????WEBP» — размер в середине, поэтому не префикс.
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return "webp", "image/webp"
    return None, None


def store(blob: bytes) -> str:
    """
    Сохраняет картинку, возвращает её имя. Бросает ValueError, если это
    не картинка или она слишком большая.
    """
    if not blob:
        raise ValueError("Пустой файл")
    if len(blob) > MAX_BYTES:
        raise ValueError(f"Файл больше {MAX_BYTES // (1024 * 1024)} МБ")
    ext, _ = _sniff(blob)
    if not ext:
        raise ValueError("Это не картинка")
    name = hashlib.sha256(blob).hexdigest()[:32] + "." + ext
    path = paths.path("media", name)
    if not os.path.exists(path):
        # Пишем через временное имя и переименовываем: если процесс умрёт
        # на середине, в хранилище не останется обрезанного файла, который
        # потом молча отдавался бы в ленту.
        tmp = path + ".part"
        with open(tmp, "wb") as f:
            f.write(blob)
        os.replace(tmp, path)
    return name


def read(name: str):
    """
    Отдаёт (содержимое, mime) по имени файла или (None, None).

    Имя проверяется целиком: пришедшее снаружи «../../users.db» иначе
    увело бы чтение за пределы хранилища.
    """
    if not name or not _safe(name):
        return None, None
    path = paths.path("media", name)
    if not os.path.exists(path):
        return None, None
    with open(path, "rb") as f:
        blob = f.read()
    _, mime = _sniff(blob)
    return blob, mime or "application/octet-stream"


def _safe(name: str) -> bool:
    stem, _, ext = name.partition(".")
    return (len(stem) == 32 and all(ch in "0123456789abcdef" for ch in stem)
            and ext in ("jpg", "png", "gif", "webp"))


def forget(name: str) -> None:
    """Убирает файл, если на него больше никто не ссылается."""
    from .db import conn
    if not name or not _safe(name):
        return
    used = conn().execute("SELECT 1 FROM posts WHERE media=? LIMIT 1",
                          (name,)).fetchone()
    if used:
        return
    try:
        os.remove(paths.path("media", name))
    except OSError:
        pass
