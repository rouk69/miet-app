# -*- coding: utf-8 -*-
"""
Соединение с SQLite и вся схема в одном месте.

Раньше единственную таблицу заводил storage.py прямо в своём _conn(). С
появлением админки данных стало больше: кроме группы и сдвига недели база
держит профиль человека, поток событий и роли. Схема, размазанная по
модулям, рано или поздно расходится — поэтому все CREATE TABLE и миграции
собраны здесь, а модули пишут только запросы.

Соединение одно на процесс, доступ к нему по очереди (см. Shared). Своё
на поток не годится: HTTP-сервер заводит поток на каждый запрос, и
соединения копились бы десятками, каждое — со своим прогоном схемы.

Время в базе всегда UTC (CURRENT_TIMESTAMP, datetime('now')), потому что в
облаке часовой пояс контейнера UTC, а на ноутбуке — московский, и хранить
«местное» значило бы получить базу с двумя разными шкалами. Для показа и
группировки по дням прибавляем MSK — иначе сутки в отчёте резались бы в
три часа ночи.
"""
from __future__ import annotations

import sqlite3
import threading

from . import paths

DB_PATH = paths.path("users.db")

# Сдвиг московского времени для SQL-функций дат. Города МИЭТа — Зеленоград,
# отчёты смотрят по местному времени, а не по UTC.
MSK = "+3 hours"

SCHEMA = [
    # Настройки и профиль человека. Строка появляется, как только он написал
    # боту или открыл мини-приложение, — то есть это же и список «юзеров».
    """CREATE TABLE IF NOT EXISTS users (
        user_id    INTEGER PRIMARY KEY,
        group_name TEXT,
        week_shift INTEGER DEFAULT 0,
        username   TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    # Поток событий: заходы в приложение, открытия вкладок и экранов,
    # команды боту. Из него считается вся статистика.
    """CREATE TABLE IF NOT EXISTS events (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        kind    TEXT NOT NULL,
        name    TEXT,
        ts      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS events_ts ON events(ts)",
    "CREATE INDEX IF NOT EXISTS events_user ON events(user_id, ts)",
    "CREATE INDEX IF NOT EXISTS events_kind ON events(kind, ts)",
    # Роли и доступы. Отдельной таблицей, а не столбцами в users: строка
    # здесь есть только у тех, кому что-то выдали, — их единицы.
    """CREATE TABLE IF NOT EXISTS roles (
        user_id    INTEGER PRIMARY KEY,
        role       TEXT NOT NULL DEFAULT 'none',
        perms      TEXT NOT NULL DEFAULT '[]',
        sections   TEXT NOT NULL DEFAULT '[]',
        blocked    INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    # Лента: и написанные людьми посты, и новости, притащенные с miet.ru.
    # Одна таблица на оба вида намеренно — читаются они вместе, сортируются
    # вместе, и реакции с прочтениями у них общие. Различает их kind.
    """CREATE TABLE IF NOT EXISTS posts (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        kind         TEXT NOT NULL DEFAULT 'post',
        author_id    INTEGER,
        author_label TEXT,
        anon         INTEGER NOT NULL DEFAULT 0,
        title        TEXT,
        text         TEXT,
        media        TEXT,
        source_url   TEXT,
        external_id  TEXT,
        audience     TEXT NOT NULL DEFAULT 'all',
        status       TEXT NOT NULL DEFAULT 'published',
        pinned       INTEGER NOT NULL DEFAULT 0,
        created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        published_at TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS posts_feed ON posts(status, pinned, id)",
    # Новость с сайта не должна попасть в ленту дважды, даже если сбор
    # запустится параллельно: уникальность гарантирует база, а не проверка.
    "CREATE UNIQUE INDEX IF NOT EXISTS posts_external ON posts(external_id) "
    "WHERE external_id IS NOT NULL",
    # Кому виден пост. Строки есть только у постов с audience='groups'.
    """CREATE TABLE IF NOT EXISTS post_groups (
        post_id    INTEGER NOT NULL,
        group_name TEXT NOT NULL,
        PRIMARY KEY (post_id, group_name)
    )""",
    "CREATE INDEX IF NOT EXISTS post_groups_name ON post_groups(group_name)",
    # Варианты опроса. Опрос живёт внутри поста, отдельной сущности нет:
    # опрос без поста в этой ленте не бывает.
    """CREATE TABLE IF NOT EXISTS poll_options (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        text    TEXT NOT NULL,
        pos     INTEGER NOT NULL DEFAULT 0
    )""",
    "CREATE INDEX IF NOT EXISTS poll_options_post ON poll_options(post_id, pos)",
    # Голос один на человека: ключ по (post_id, user_id), а не по варианту, —
    # переголосование заменяет строку, а не добавляет вторую.
    """CREATE TABLE IF NOT EXISTS poll_votes (
        post_id   INTEGER NOT NULL,
        user_id   INTEGER NOT NULL,
        option_id INTEGER NOT NULL,
        ts        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (post_id, user_id)
    )""",
    # Прочтения: строка на человека, поэтому счётчик — это «сколько людей»,
    # а не «сколько раз открыли».
    """CREATE TABLE IF NOT EXISTS post_reads (
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        ts      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (post_id, user_id)
    )""",
    # Реакция тоже одна на человека — как в Telegram: новая заменяет старую,
    # повторный тап по той же снимает её.
    """CREATE TABLE IF NOT EXISTS post_reactions (
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        emoji   TEXT NOT NULL,
        ts      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (post_id, user_id)
    )""",
]

# Столбцы, доросшие к users позже. У баз, созданных до админки, их нет —
# ALTER TABLE ADD COLUMN дешёвый и на живой базе безопасен.
ADDED_COLUMNS = [
    ("shift_semestr", "TEXT"),
    ("first_name", "TEXT"),
    ("last_name", "TEXT"),
    ("photo_url", "TEXT"),
    ("language", "TEXT"),
    ("is_premium", "INTEGER DEFAULT 0"),
    ("first_seen", "TEXT"),
    ("last_seen", "TEXT"),
    ("opens", "INTEGER DEFAULT 0"),
    ("seen_bot", "INTEGER DEFAULT 0"),
    ("seen_app", "INTEGER DEFAULT 0"),
]


class Rows(list):
    """
    Результат запроса, вычитанный целиком.

    Курсор наружу отдавать нельзя: его итерация — это обращение к базе, и
    происходило бы оно уже вне замка, то есть параллельно с чужой записью.
    Поэтому строки материализуются сразу, а привычные `fetchone` и
    `fetchall` остаются, чтобы вызывающий код не переписывать.
    """

    def __init__(self, rows, lastrowid=None, rowcount=-1):
        super().__init__(rows)
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchone(self):
        return self[0] if self else None

    def fetchall(self):
        return list(self)


class Shared:
    """
    Одно соединение на процесс, доступ по очереди.

    Раньше соединение заводилось на поток (`threading.local`), и это было
    незаметной бомбой: `ThreadingHTTPServer` создаёт **новый поток на
    каждый запрос**, а значит каждый запрос открывал новое соединение и
    прогонял всю схему — два десятка `CREATE TABLE IF NOT EXISTS`, то
    есть DDL, которому нужна эксклюзивная блокировка записи. Пока лента
    считалась, соседний запрос стоял в очереди, упирался в
    `busy_timeout` и отваливался ровно через десять секунд. Снаружи это
    выглядело как «лента иногда не грузится».

    Общее соединение снимает и вторую половину беды: старые соединения
    больше не копятся, потому что новых не заводится.

    Режим автофиксации (`isolation_level=None`) здесь обязателен: с
    общим соединением незакрытая транзакция одного потока подхватывала
    бы записи другого, и `commit()` фиксировал бы чужое недоделанное.
    Вызовы `commit()` в коде остаются — в этом режиме они безвредны.
    """

    def __init__(self, path: str):
        self._raw = sqlite3.connect(path, timeout=10, check_same_thread=False,
                                    isolation_level=None)
        self._lock = threading.RLock()
        with self._lock:
            # WAL: чтение не ждёт запись. NORMAL вместо FULL — на каждой
            # записи не дёргаем fsync, а на сетевом диске Amvera это
            # разница между «мгновенно» и «десятки миллисекунд».
            self._raw.execute("PRAGMA journal_mode=WAL")
            self._raw.execute("PRAGMA synchronous=NORMAL")
            self._raw.execute("PRAGMA busy_timeout=5000")
            for stmt in SCHEMA:
                self._raw.execute(stmt)
            have = {r[1] for r in self._raw.execute("PRAGMA table_info(users)")}
            for name, decl in ADDED_COLUMNS:
                if name not in have:
                    self._raw.execute(f"ALTER TABLE users ADD COLUMN {name} {decl}")

    def execute(self, sql: str, args=()) -> Rows:
        with self._lock:
            cur = self._raw.execute(sql, args)
            rows = cur.fetchall() if cur.description else []
            return Rows(rows, cur.lastrowid, cur.rowcount)

    def executemany(self, sql: str, seq) -> Rows:
        with self._lock:
            cur = self._raw.executemany(sql, seq)
            return Rows([], cur.lastrowid, cur.rowcount)

    def commit(self) -> None:
        """В режиме автофиксации фиксировать нечего — оставлено для кода."""

    def close(self) -> None:
        with self._lock:
            self._raw.close()


_shared: Shared | None = None
_make_lock = threading.Lock()


def conn() -> Shared:
    """Общее соединение. Схема применяется один раз за жизнь процесса."""
    global _shared
    if _shared is None:
        with _make_lock:
            if _shared is None:
                _shared = Shared(DB_PATH)
    return _shared


def reset_for_tests(path: str) -> None:
    """
    Переключает модуль на другую базу. Нужен только тестам: они не должны
    писать в живую users.db, иначе прогон испортит настоящую статистику.
    """
    global DB_PATH, _shared
    DB_PATH = path
    if _shared is not None:
        _shared.close()
        _shared = None
