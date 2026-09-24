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

import contextlib
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
    # Комментарии. Автор хранится идентификатором, а подпись — отдельной
    # строкой на момент написания: роль человека потом меняется, а «кто это
    # сказал тогда» меняться не должно.
    """CREATE TABLE IF NOT EXISTS comments (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id      INTEGER NOT NULL,
        user_id      INTEGER NOT NULL,
        author_label TEXT,
        text         TEXT NOT NULL,
        created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS comments_post ON comments(post_id, id)",
    "CREATE INDEX IF NOT EXISTS comments_user ON comments(user_id, id)",
    # Плоский слепок расписания всех групп: по нему ищутся преподаватели и
    # аудитории. miet.ru отдаёт расписание только по группе, поэтому вопрос
    # «где сейчас Иванов» без такого индекса требует 346 запросов к сайту.
    # Таблица целиком пересобирается раз в сутки — история тут не нужна.
    """CREATE TABLE IF NOT EXISTS lessons_index (
        teacher    TEXT NOT NULL,
        room       TEXT,
        subject    TEXT,
        kind       TEXT,
        group_name TEXT NOT NULL,
        day        INTEGER NOT NULL,
        week       INTEGER NOT NULL,
        pair       INTEGER,
        t_from     TEXT,
        t_to       TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS lessons_teacher ON lessons_index(teacher)",
    "CREATE INDEX IF NOT EXISTS lessons_room ON lessons_index(room)",
    "CREATE INDEX IF NOT EXISTS lessons_when ON lessons_index(week, day, pair)",
    # Когда индекс собран и по какому семестру: смена семестра означает,
    # что старые данные показывать уже нельзя.
    """CREATE TABLE IF NOT EXISTS index_meta (
        key   TEXT PRIMARY KEY,
        value TEXT
    )""",
    # Доска взаимопомощи: «нужна помощь по матанализу» и «могу помочь с
    # схемотехникой». Отдельно от ленты намеренно — у объявления другая
    # жизнь: оно закрывается, когда вопрос решён, и не имеет смысла в
    # хронологическом потоке рядом с новостями.
    """CREATE TABLE IF NOT EXISTS help_offers (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        kind       TEXT NOT NULL DEFAULT 'need',
        subject    TEXT NOT NULL,
        text       TEXT,
        price      TEXT NOT NULL DEFAULT 'free',
        status     TEXT NOT NULL DEFAULT 'open',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        closed_at  TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS help_open ON help_offers(status, kind, id)",
    "CREATE INDEX IF NOT EXISTS help_author ON help_offers(user_id, status)",
    # Связь с ОРИОКС. Здесь лежит ТОЛЬКО токен: пароль проходит через
    # сервер один раз при подключении и нигде не остаётся. Токен студент
    # может отозвать сам — и отсюда, и в любом другом клиенте ОРИОКС.
    """CREATE TABLE IF NOT EXISTS orioks_links (
        user_id   INTEGER PRIMARY KEY,
        token     TEXT NOT NULL,
        linked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    # Когда поднимался процесс. Нужно, чтобы отличить «оборвалось у
    # человека по дороге» от «в эту секунду перезапускался контейнер»:
    # снаружи оба случая выглядят одинаково — закрытым соединением.
    """CREATE TABLE IF NOT EXISTS starts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS starts_when ON starts(at)",
    # Какие объявления преподавателей человеку уже показывали. Память
    # нужна в базе, а не в счётчике «последнего id»: объявления приходят
    # по разным дисциплинам вперемешку, и «всё, что новее» о них сказать
    # нельзя. Хранится один номер — ни заголовка, ни текста.
    # Поломки на стороне клиента. Строка на ОТПЕЧАТОК ошибки, а не на
    # случай: одна и та же беда у двухсот человек — это одна запись со
    # счётчиком, иначе первая же мелочь вытеснит из таблицы всё
    # остальное. Личного тут не хранится: текст ошибки, экран, версия
    # сборки; user_id — только последний, чтобы было кого переспросить.
    """CREATE TABLE IF NOT EXISTS client_errors (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint TEXT NOT NULL,
        message     TEXT NOT NULL,
        source      TEXT,
        line        INTEGER,
        stack       TEXT,
        build       TEXT,
        screen      TEXT,
        platform    TEXT,
        version     TEXT,
        user_id     INTEGER,
        count       INTEGER NOT NULL DEFAULT 1,
        first_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS client_errors_key "
    "ON client_errors(fingerprint)",
    "CREATE INDEX IF NOT EXISTS client_errors_when ON client_errors(last_at)",
    # Приглашения по реферальной ссылке. Строка на ПРИГЛАШЁННОГО, а не
    # на пару: человек закрепляется за тем, по чьей ссылке пришёл первым,
    # и второй ссылкой его уже не перетянуть — иначе двое приглашающих
    # могли бы перекидывать одного и того же друг у друга. Зачёт отложен:
    # переход считается, только когда человек дошёл до выбора группы,
    # поэтому состояние живёт здесь, а не выводится из users.
    """CREATE TABLE IF NOT EXISTS raffle_invites (
        user_id    INTEGER PRIMARY KEY,
        inviter_id INTEGER NOT NULL,
        source     TEXT NOT NULL DEFAULT 'bot',
        state      TEXT NOT NULL DEFAULT 'waiting',
        reason     TEXT,
        flags      TEXT NOT NULL DEFAULT '',
        manual     TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        counted_at TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS raffle_by_inviter ON raffle_invites(inviter_id, state)",
    "CREATE INDEX IF NOT EXISTS raffle_when ON raffle_invites(created_at)",
    """CREATE TABLE IF NOT EXISTS orioks_seen (
        user_id INTEGER NOT NULL,
        news_id TEXT NOT NULL,
        seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, news_id)
    )""",
    # Баллы ОРИОКС, какими их видел сторож: по строке на контрольную
    # точку. Самого балла здесь нет — только отпечаток (`sig`), чтобы
    # заметить перемену; число показываем из свежего ответа ОРИОКС.
    # `changed_at` пуст у того, что застали при первом обходе: это не
    # «новый балл», а то, что уже было.
    # Когда у группы обед — от этого зависит время 3-й пары (12:00 или
    # 12:30). Выбирает человек, и выбор общий у бота и приложения. Ключ —
    # пара (человек, группа): у старосты может быть выбрана и соседняя.
    """CREATE TABLE IF NOT EXISTS group_lunch (
        user_id    INTEGER NOT NULL,
        grp        TEXT NOT NULL,
        lunch      TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, grp)
    )""",
    """CREATE TABLE IF NOT EXISTS orioks_grades (
        user_id    INTEGER NOT NULL,
        key        TEXT NOT NULL,
        sig        TEXT NOT NULL,
        changed_at TEXT,
        PRIMARY KEY (user_id, key)
    )""",
]

# Столбцы, доросшие к таблицам позже. У баз, созданных раньше, их нет —
# ALTER TABLE ADD COLUMN дешёвый и на живой базе безопасен. Держим по
# таблицам, чтобы дописать столбец к любой из них можно было одинаково.
ADDED_COLUMNS = {
    "users": [
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
        # Утренняя карточка дня приходит всем, у кого выбрана группа,
        # и отключается кнопкой под самим сообщением. Поэтому в базе
        # хранится отказ, а не согласие: пустое значение означает
        # «шлём», и новым людям ничего включать не нужно.
        ("morning_off", "INTEGER DEFAULT 0"),
        # Старый столбец согласия. Остался, чтобы не терять тех, кто
        # успел включить рассылку, пока она была по подписке.
        ("morning", "INTEGER DEFAULT 0"),
        # Дата последней отправки, чтобы перезапуск контейнера не
        # обернулся вторым «добрым утром» в тот же день.
        ("morning_at", "TEXT"),
        # Каким входом человек открывает приложение. Пусто — прямым, к
        # Amvera; единица — через запасной (воркер Cloudflare). Выбор
        # личный и хранится: у кого прямой путь оборвался, у того он
        # оборвётся и завтра, а спрашивать об этом каждый раз — значит
        # не починить ничего.
        ("entry_mirror", "INTEGER DEFAULT 0"),
        # Код в реферальной ссылке. Не user_id: тот светил бы в каждом
        # сообщении, которое человек кидает в чат группы, а по нему в
        # Telegram ищется аккаунт. Заводится при первом открытии раздела
        # розыгрыша и дальше не меняется — ссылку уже разослали.
        ("ref_code", "TEXT"),
    ],
    # Ответ на комментарий. Ветка ровно одна: ответ на ответ прикрепляется
    # к тому же корню — дерево произвольной глубины в ленте объявлений
    # читать невозможно, а рисовать больно.
    "comments": [
        ("reply_to", "INTEGER"),
    ],
    # Cookie сессии веб-версии ОРИОКС. Пароля здесь по-прежнему нет: он
    # обменивается на сессию в момент подключения и не переживает
    # запроса. Сессия нужна затем, что текст домашнего задания есть
    # только на сайте — студенческое API отдаёт голые названия.
    "orioks_links": [
        ("web_cookie", "TEXT"),
        ("web_at", "TEXT"),
        # Сообщать ли о новых объявлениях преподавателей. По умолчанию
        # да: подключают ОРИОКС ровно за этим, а выключить можно одним
        # переключателем в разделе «Учёба».
        ("notify", "INTEGER DEFAULT 1"),
    ],
}


# Индексы по столбцам из ADDED_COLUMNS. Отдельным списком потому, что
# SCHEMA выполняется раньше ALTER TABLE: на базе, созданной прошлой
# версией, столбца в этот момент ещё не существует, и CREATE INDEX упал
# бы на каждом запуске.
LATE_INDEXES = [
    # Код в реферальной ссылке обязан быть один на весь бот: совпадение
    # означало бы, что приглашённые уходят чужому человеку. Проверять это
    # запросом мало — два одновременных открытия раздела разошлись бы
    # между проверкой и вставкой.
    "CREATE UNIQUE INDEX IF NOT EXISTS users_ref_code ON users(ref_code) "
    "WHERE ref_code IS NOT NULL",
]


def _lower_ru(value):
    """Нижний регистр с кириллицей. NULL остаётся NULL, как в SQL."""
    return value.lower() if isinstance(value, str) else value


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
            # LIKE в SQLite приводит к нижнему регистру только латиницу:
            # «матан» не находил «Матанализ», а «иванов» — «Иванова».
            # Своя функция чинит это для всего поиска сразу; индекс на ней
            # не работает, но таблицы здесь маленькие, а полный скан
            # десятка тысяч строк — доли миллисекунды.
            self._raw.create_function("lower_ru", 1, _lower_ru,
                                      deterministic=True)
            for stmt in SCHEMA:
                self._raw.execute(stmt)
            for table, columns in ADDED_COLUMNS.items():
                have = {r[1] for r in
                        self._raw.execute(f"PRAGMA table_info({table})")}
                for name, decl in columns:
                    if name not in have:
                        self._raw.execute(
                            f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
            for stmt in LATE_INDEXES:
                self._raw.execute(stmt)

    def execute(self, sql: str, args=()) -> Rows:
        with self._lock:
            cur = self._raw.execute(sql, args)
            rows = cur.fetchall() if cur.description else []
            return Rows(rows, cur.lastrowid, cur.rowcount)

    def executemany(self, sql: str, seq) -> Rows:
        with self._lock:
            cur = self._raw.executemany(sql, seq)
            return Rows([], cur.lastrowid, cur.rowcount)

    @contextlib.contextmanager
    def transaction(self):
        """
        Несколько запросов одной транзакцией, под одним замком.

        Замок держится всё время: иначе между BEGIN и COMMIT сюда попадёт
        чужая запись из соседнего потока — а при откате она пропадёт
        вместе с нашей. Внутри отдаётся сырое соединение, потому что
        собственный execute снова полез бы за тем же (нерекурсивным для
        других потоков) замком.
        """
        with self._lock:
            self._raw.execute("BEGIN")
            try:
                yield self._raw
            except Exception:
                self._raw.execute("ROLLBACK")
                raise
            self._raw.execute("COMMIT")

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
