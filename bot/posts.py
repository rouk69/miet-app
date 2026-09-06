# -*- coding: utf-8 -*-
"""
Лента: посты, написанные людьми, и новости, притащенные с miet.ru.

Главное правило здесь одно — **кто что видит, решается на сервере**.
Пост с аудиторией «только эти группы» не должен доехать до чужого
клиента вообще: спрятать его в интерфейсе мало, ответ API можно
прочитать и руками.

Второе правило — анонимность выдаётся, а не берётся. Пост «скрытно»
уходит в очередь и появляется в ленте только после одобрения; до этого
его видит лишь автор. Иначе анонимность превращается в способ написать
что угодно от лица университета.

Опрос, реакции и прочтения живут отдельными таблицами (см. db.py), но
наружу отдаются внутри поста — клиенту удобнее один объект.
"""
from __future__ import annotations

import re

from .db import conn

# Набор реакций фиксирован: произвольные эмодзи от клиента означали бы,
# что в базу можно записать что угодно, а в ленте появлялись бы кнопки,
# которых нет ни у кого больше.
REACTIONS = ["👍", "❤️", "🔥", "😂", "😮"]

KINDS = ("post", "news")
AUDIENCES = ("all", "groups")
STATUSES = ("published", "pending", "rejected")

MAX_TEXT = 4000
MAX_TITLE = 200
MAX_OPTIONS = 6
MAX_OPTION_TEXT = 100


class Refused(Exception):
    """Отказ по смыслу, а не по технике: текст уедет человеку как есть."""


def _clean(s: str, limit: int) -> str:
    return re.sub(r"[ \t]+", " ", str(s or "")).strip()[:limit]


# ─────────────────────────── запись ───────────────────────────

def create(author_id: int, text: str, *, title: str = "", groups=None,
           options=None, anon: bool = False, media: str = "",
           author_label: str = "", may_publish_anon: bool = False) -> dict:
    """
    Заводит пост. Возвращает его же, прочитанным обратно из базы.

    `may_publish_anon` — право публиковать анонимно без одобрения. У
    обычного автора его нет, поэтому анонимный пост встаёт в очередь:
    подпись «Анонимно» снимает ответственность с автора, и раздавать её
    без разбора нельзя.
    """
    text = _clean(text, MAX_TEXT)
    title = _clean(title, MAX_TITLE)
    if not text and not title:
        raise Refused("Пустой пост")

    opts = [_clean(o, MAX_OPTION_TEXT) for o in (options or [])]
    opts = [o for o in opts if o][:MAX_OPTIONS]
    if len(opts) == 1:
        raise Refused("В опросе нужно хотя бы два варианта")

    groups = [g for g in {str(g).strip() for g in (groups or [])} if g]
    audience = "groups" if groups else "all"
    status = "published" if (not anon or may_publish_anon) else "pending"

    c = conn()
    cur = c.execute(
        """INSERT INTO posts (kind, author_id, author_label, anon, title, text,
                              media, audience, status, published_at)
           VALUES ('post', ?, ?, ?, ?, ?, ?, ?, ?,
                   CASE WHEN ?='published' THEN CURRENT_TIMESTAMP END)""",
        (author_id, _clean(author_label, 60), 1 if anon else 0, title, text,
         media or None, audience, status, status))
    post_id = cur.lastrowid
    for g in groups:
        c.execute("INSERT OR IGNORE INTO post_groups (post_id, group_name) "
                  "VALUES (?, ?)", (post_id, g))
    for i, o in enumerate(opts):
        c.execute("INSERT INTO poll_options (post_id, text, pos) VALUES (?, ?, ?)",
                  (post_id, o, i))
    c.commit()
    return one(post_id, author_id, force=True)


def add_news(external_id: str, title: str, text: str, url: str,
             media: str = "") -> bool:
    """
    Кладёт новость с сайта. Возвращает True, если она новая.

    Повторный заход не создаёт дубль: уникальный индекс по external_id
    отклоняет вставку, и это надёжнее проверки «а нет ли уже», которая
    при двух сборах подряд успевает соврать.
    """
    c = conn()
    cur = c.execute(
        """INSERT OR IGNORE INTO posts
             (kind, author_label, title, text, media, source_url, external_id,
              status, published_at)
           VALUES ('news', 'МИЭТ', ?, ?, ?, ?, ?, 'published', CURRENT_TIMESTAMP)""",
        (_clean(title, MAX_TITLE), _clean(text, MAX_TEXT), media or None,
         url, str(external_id)))
    c.commit()
    return cur.rowcount > 0


def update_news(external_id: str, text: str, media: str = "") -> None:
    """
    Дописывает новости текст и обложку.

    Отдельным шагом, потому что заголовок и ссылка берутся из общего
    списка, а текст — со страницы самой новости: сначала заявляем её в
    базе, и только потом ходим за подробностями. Так параллельный сбор не
    утащит одну и ту же новость дважды.
    """
    c = conn()
    c.execute("""UPDATE posts SET text=COALESCE(NULLIF(?, ''), text),
                                  media=COALESCE(NULLIF(?, ''), media)
                 WHERE external_id=?""",
              (_clean(text, MAX_TEXT), media or "", str(external_id)))
    c.commit()


def set_status(post_id: int, status: str) -> None:
    if status not in STATUSES:
        raise Refused("Неизвестное состояние поста")
    c = conn()
    c.execute(
        """UPDATE posts SET status=?,
             published_at = CASE WHEN ?='published' AND published_at IS NULL
                                 THEN CURRENT_TIMESTAMP ELSE published_at END
           WHERE id=?""", (status, status, post_id))
    c.commit()


def set_pinned(post_id: int, pinned: bool) -> None:
    c = conn()
    c.execute("UPDATE posts SET pinned=? WHERE id=?", (1 if pinned else 0, post_id))
    c.commit()


def delete(post_id: int) -> None:
    """Удаляет пост со всем, что к нему прицеплено."""
    c = conn()
    for table in ("post_groups", "poll_options", "poll_votes", "post_reads",
                  "post_reactions"):
        c.execute(f"DELETE FROM {table} WHERE post_id=?", (post_id,))
    c.execute("DELETE FROM posts WHERE id=?", (post_id,))
    c.commit()


def vote(post_id: int, user_id: int, option_id: int) -> None:
    c = conn()
    ok = c.execute("SELECT 1 FROM poll_options WHERE id=? AND post_id=?",
                   (option_id, post_id)).fetchone()
    if not ok:
        raise Refused("Такого варианта в опросе нет")
    c.execute("""INSERT INTO poll_votes (post_id, user_id, option_id)
                 VALUES (?, ?, ?)
                 ON CONFLICT(post_id, user_id) DO UPDATE SET
                   option_id=excluded.option_id, ts=CURRENT_TIMESTAMP""",
              (post_id, user_id, option_id))
    c.commit()


def react(post_id: int, user_id: int, emoji: str) -> str:
    """
    Ставит реакцию. Повторный тап по той же снимает её — как в Telegram.
    Возвращает текущую реакцию человека («» если снял).
    """
    if emoji not in REACTIONS:
        raise Refused("Такой реакции нет")
    c = conn()
    now = c.execute("SELECT emoji FROM post_reactions WHERE post_id=? AND user_id=?",
                    (post_id, user_id)).fetchone()
    if now and now[0] == emoji:
        c.execute("DELETE FROM post_reactions WHERE post_id=? AND user_id=?",
                  (post_id, user_id))
        c.commit()
        return ""
    c.execute("""INSERT INTO post_reactions (post_id, user_id, emoji)
                 VALUES (?, ?, ?)
                 ON CONFLICT(post_id, user_id) DO UPDATE SET
                   emoji=excluded.emoji, ts=CURRENT_TIMESTAMP""",
              (post_id, user_id, emoji))
    c.commit()
    return emoji


def mark_read(post_id: int, user_id: int) -> None:
    c = conn()
    c.execute("INSERT OR IGNORE INTO post_reads (post_id, user_id) VALUES (?, ?)",
              (post_id, user_id))
    c.commit()


# ─────────────────────────── чтение ───────────────────────────

# Условие видимости. Держим одной строкой и подставляем везде: разойдись
# оно между лентой и открытием поста — закрытый пост утёк бы по прямой
# ссылке, а это ровно та ошибка, которую тут нельзя допустить.
VISIBLE = """(
    p.status='published' AND (
        p.audience='all'
        OR EXISTS (SELECT 1 FROM post_groups g
                   WHERE g.post_id=p.id AND g.group_name = :group)
    )
)"""

FIELDS = ("p.id, p.kind, p.author_id, p.author_label, p.anon, p.title, p.text, "
          "p.media, p.source_url, p.audience, p.status, p.pinned, "
          "p.created_at, p.published_at, p.external_id")


def _row(r) -> dict:
    return {
        "id": r[0], "kind": r[1], "author_id": r[2], "author_label": r[3],
        "anon": bool(r[4]), "title": r[5], "text": r[6], "media": r[7],
        "url": r[8], "audience": r[9], "status": r[10], "pinned": bool(r[11]),
        "created_at": r[12], "published_at": r[13] or r[12],
        # id новости на miet.ru: по нему приложение отличает свежую новость
        # от той же самой, лежащей в архивном data/app.json.
        "external_id": r[14],
    }


def _decorate(rows: list, user_id: int, can_see_authors: bool = False) -> list:
    """
    Дописывает к постам всё, что показывается вокруг текста: опрос с
    голосами, реакции, прочтения, аудиторию. Одним запросом на таблицу,
    а не по запросу на пост — иначе лента из тридцати постов означала бы
    полторы сотни обращений к базе.
    """
    if not rows:
        return []
    c = conn()
    ids = [r["id"] for r in rows]
    marks = ",".join("?" * len(ids))
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        r.update(poll=None, reactions=[], my_reaction="", reads=0, read=False,
                 groups=[], votes_total=0)

    options = {}
    for pid, oid, text, pos in c.execute(
            f"SELECT post_id, id, text, pos FROM poll_options "
            f"WHERE post_id IN ({marks}) ORDER BY post_id, pos", ids):
        options.setdefault(pid, []).append({"id": oid, "text": text, "votes": 0})
    counts = {}
    for pid, oid, n in c.execute(
            f"SELECT post_id, option_id, COUNT(*) FROM poll_votes "
            f"WHERE post_id IN ({marks}) GROUP BY post_id, option_id", ids):
        counts[(pid, oid)] = n
    mine = dict(c.execute(
        f"SELECT post_id, option_id FROM poll_votes "
        f"WHERE user_id=? AND post_id IN ({marks})", [user_id] + ids))
    for pid, opts in options.items():
        total = 0
        for o in opts:
            o["votes"] = counts.get((pid, o["id"]), 0)
            total += o["votes"]
        for o in opts:
            # Доля считается на сервере: у клиента иначе разъезжается
            # округление между «100%» и суммой долей.
            o["share"] = round(o["votes"] * 100 / total) if total else 0
        by_id[pid].update(poll={"options": opts, "total": total,
                                "my_option": mine.get(pid)},
                          votes_total=total)

    for pid, emoji, n in c.execute(
            f"SELECT post_id, emoji, COUNT(*) FROM post_reactions "
            f"WHERE post_id IN ({marks}) GROUP BY post_id, emoji", ids):
        by_id[pid]["reactions"].append({"emoji": emoji, "count": n})
    for pid, emoji in c.execute(
            f"SELECT post_id, emoji FROM post_reactions "
            f"WHERE user_id=? AND post_id IN ({marks})", [user_id] + ids):
        by_id[pid]["my_reaction"] = emoji

    for pid, n in c.execute(
            f"SELECT post_id, COUNT(*) FROM post_reads "
            f"WHERE post_id IN ({marks}) GROUP BY post_id", ids):
        by_id[pid]["reads"] = n
    for (pid,) in c.execute(
            f"SELECT post_id FROM post_reads WHERE user_id=? "
            f"AND post_id IN ({marks})", [user_id] + ids):
        by_id[pid]["read"] = True

    for pid, g in c.execute(
            f"SELECT post_id, group_name FROM post_groups "
            f"WHERE post_id IN ({marks}) ORDER BY group_name", ids):
        by_id[pid]["groups"].append(g)

    for r in rows:
        # Автора анонимного поста наружу не отдаём вообще: клиент показывает
        # то, что получил, и «скрытый» автор в JSON перестал бы быть скрытым.
        if r["anon"] and not can_see_authors:
            r["author_id"] = None
            r["author_label"] = "Анонимно"
        r["mine"] = bool(user_id and r["author_id"] == user_id)
    return rows


def feed(user_id: int, group: str = "", limit: int = 20, offset: int = 0,
         can_see_authors: bool = False) -> dict:
    """Лента, видимая этому человеку. Закреплённые сверху, дальше свежие."""
    c = conn()
    args = {"group": group or "", "limit": max(1, min(limit, 50)),
            "offset": max(0, offset)}
    total = c.execute(f"SELECT COUNT(*) FROM posts p WHERE {VISIBLE}",
                      args).fetchone()[0]
    rows = [_row(r) for r in c.execute(
        f"""SELECT {FIELDS} FROM posts p WHERE {VISIBLE}
            ORDER BY p.pinned DESC, COALESCE(p.published_at, p.created_at) DESC,
                     p.id DESC
            LIMIT :limit OFFSET :offset""", args)]
    return {"total": total,
            "posts": _decorate(rows, user_id, can_see_authors),
            "reactions": REACTIONS}


def one(post_id: int, user_id: int, group: str = "", force: bool = False,
        can_see_authors: bool = False) -> dict | None:
    """
    Один пост. `force` пропускает проверку видимости — он для тех мест,
    где право уже проверено выше (админка, модерация, свой свежий пост).
    """
    c = conn()
    args = {"id": post_id, "group": group or ""}
    where = "p.id = :id" if force else f"p.id = :id AND {VISIBLE}"
    row = c.execute(f"SELECT {FIELDS} FROM posts p WHERE {where}", args).fetchone()
    if not row:
        # Свой пост автор видит всегда — иначе он не увидел бы, что его
        # анонимный пост ждёт одобрения.
        row = c.execute(
            f"SELECT {FIELDS} FROM posts p WHERE p.id=:id AND p.author_id=:me",
            {"id": post_id, "me": user_id}).fetchone()
        if not row:
            return None
    return _decorate([_row(row)], user_id, can_see_authors)[0]


def pending(user_id: int, limit: int = 50) -> list:
    """Очередь на одобрение — анонимные посты, ждущие разрешения."""
    rows = [_row(r) for r in conn().execute(
        f"""SELECT {FIELDS} FROM posts p WHERE p.status='pending'
            ORDER BY p.id DESC LIMIT ?""", (max(1, min(limit, 100)),))]
    # Модератор решает судьбу поста и потому видит, кто его написал:
    # анонимность защищает автора от читателей, а не от разбирательства.
    return _decorate(rows, user_id, can_see_authors=True)


def stats() -> dict:
    c = conn()
    one_ = lambda sql: c.execute(sql).fetchone()[0]
    return {
        "posts": one_("SELECT COUNT(*) FROM posts WHERE kind='post' "
                      "AND status='published'"),
        "news": one_("SELECT COUNT(*) FROM posts WHERE kind='news'"),
        "pending": one_("SELECT COUNT(*) FROM posts WHERE status='pending'"),
        "votes": one_("SELECT COUNT(*) FROM poll_votes"),
        "reactions": one_("SELECT COUNT(*) FROM post_reactions"),
        "reads": one_("SELECT COUNT(*) FROM post_reads"),
    }
