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
import logging
import os
import re

from . import paths

log = logging.getLogger("miet.media")

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


def probe(blob: bytes):
    """
    Размеры картинки — из её же байтов, без сторонних библиотек.

    Нужны они клиенту: зная соотношение сторон, он занимает место под
    картинку заранее. Без этого лента прыгает на каждой подгрузке, а
    единое соотношение «для ровного вида» резало скриншоты расписания
    пополам — а их в студенческой ленте больше, чем фотографий.

    Не разобрали — (0, 0): картинка покажется как раньше, по месту.
    """
    try:
        if blob.startswith(b"\x89PNG\r\n\x1a\n") and blob[12:16] == b"IHDR":
            return (int.from_bytes(blob[16:20], "big"),
                    int.from_bytes(blob[20:24], "big"))

        if blob[:3] == b"\xff\xd8\xff":
            # JPEG: идём по сегментам до того, что описывает кадр (SOFn).
            # Размеры лежат только там, и до него бывает много служебного —
            # превью, цветовой профиль, данные камеры.
            i = 2
            end = len(blob)
            while i + 9 < end:
                if blob[i] != 0xFF:
                    i += 1
                    continue
                marker = blob[i + 1]
                # Пустые заполнители и маркеры без длины пропускаем.
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                length = int.from_bytes(blob[i + 2:i + 4], "big")
                if length < 2:
                    break
                # SOF0…SOF15, кроме 0xC4 (таблицы Хаффмана), 0xC8 и 0xCC.
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    return (int.from_bytes(blob[i + 7:i + 9], "big"),
                            int.from_bytes(blob[i + 5:i + 7], "big"))
                i += 2 + length
            return 0, 0

        if blob[:6] in (b"GIF87a", b"GIF89a"):
            return (int.from_bytes(blob[6:8], "little"),
                    int.from_bytes(blob[8:10], "little"))

        if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
            kind = blob[12:16]
            if kind == b"VP8X":
                return (int.from_bytes(blob[24:27], "little") + 1,
                        int.from_bytes(blob[27:30], "little") + 1)
            if kind == b"VP8L":
                bits = int.from_bytes(blob[21:25], "little")
                return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
            if kind == b"VP8 ":
                return (int.from_bytes(blob[26:28], "little") & 0x3FFF,
                        int.from_bytes(blob[28:30], "little") & 0x3FFF)
    except Exception:                                   # noqa: BLE001
        return 0, 0
    return 0, 0


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
    # Размеры — прямо в имени файла: клиенту они нужны, чтобы занять
    # место под картинку заранее, а имя доезжает до него и так. Отдельная
    # колонка в базе означала бы миграцию ради двух чисел, которые уже
    # есть в самом файле.
    w, h = probe(blob)
    stamp = f"-{w}x{h}" if w and h else ""
    name = hashlib.sha256(blob).hexdigest()[:32] + stamp + "." + ext
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
    # У имени бывает хвост с размерами: «<хеш>-1200x800.jpg».
    stem, _, size = stem.partition("-")
    if size and not re.fullmatch(r"\d{1,5}x\d{1,5}", size):
        return False
    return (len(stem) == 32 and all(ch in "0123456789abcdef" for ch in stem)
            and ext in ("jpg", "png", "gif", "webp"))


def backfill() -> int:
    """
    Дописывает размеры к именам картинок, сохранённых до этой затеи.

    Без них клиент не знает, сколько места занять, и старая лента
    прыгала бы дальше — а это как раз те записи, которые люди листают
    каждый день. Проход дешёвый: имя меняется один раз, файл
    переименовывается на месте, ссылка в записи правится тем же
    запросом.

    Возвращает, сколько картинок получило размеры.
    """
    from .db import conn

    rows = conn().execute(
        "SELECT DISTINCT media FROM posts WHERE media IS NOT NULL AND media<>''")
    fixed = 0
    for (name,) in rows:
        stem, _, ext = str(name).partition(".")
        if "-" in stem or not _safe(name):
            continue
        path = paths.path("media", name)
        try:
            with open(path, "rb") as f:
                # Размеры лежат в начале файла: JPEG иногда прячет их за
                # превью и профилем камеры, но не за сотней килобайт.
                head = f.read(128 * 1024)
        except OSError:
            continue
        w, h = probe(head)
        if not (w and h):
            continue
        fresh = f"{stem}-{w}x{h}.{ext}"
        try:
            os.replace(path, paths.path("media", fresh))
        except OSError:
            continue
        conn().execute("UPDATE posts SET media=? WHERE media=?", (fresh, name))
        fixed += 1
    if fixed:
        log.info("размеры дописаны к картинкам: %d", fixed)
    return fixed


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
