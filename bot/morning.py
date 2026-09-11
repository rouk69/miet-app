# -*- coding: utf-8 -*-
"""
Утренняя карточка дня: что сегодня, во сколько и где.

Расписание человек смотрит в одно и то же время — утром, по дороге, —
и каждый раз это одинаковые пять движений: открыть бота, нажать кнопку,
дождаться, прочитать. Карточка приходит сама, до выхода из дома, и
движений остаётся ноль.

Три правила, из-за которых она устроена именно так:

**Только по просьбе.** Сообщение в половине восьмого утра — вещь
личная: подписка выключена по умолчанию и включается человеком
(переключатель в профиле приложения). Ни одной рассылки «всем, у кого
есть группа».

**Молчим, когда сказать нечего.** В воскресенье и в дни без пар
карточка не приходит вовсе. «Сегодня пар нет» — приятная мелочь ровно
один раз, а дальше это просто будильник ни о чём.

**Один раз в день.** Дата отправки лежит рядом с подпиской: перезапуск
контейнера в восемь утра не должен оборачиваться вторым «добрым
утром».

Вид у карточки тот же, что у обычного расписания: таблица с парами,
премиум-эмодзи, окна между парами — всё, что бот уже умеет рисовать.
Отдельного оформления здесь нет намеренно: человек должен узнавать
своё расписание с первого взгляда, а не разбирать новый макет.
"""
from __future__ import annotations

import datetime as dt
import logging
import threading
import time

from . import emoji as em
from . import render, rich, storage
from . import schedule_api as api

log = logging.getLogger("miet.morning")

# Во сколько будим. Первая пара начинается в девять, дорога занимает
# полчаса-час — половина восьмого попадает в сборы, а не в сон.
HOUR, MINUTE = 7, 30

# Сколько ещё можно отправить, если бот в это время перезапускался.
# После десяти утра карточка бессмысленна: человек уже на паре.
LATEST_HOUR = 10

# Пауза между людьми: Telegram терпит около двадцати сообщений в
# секунду, но торопиться некуда — рассылка не срочная.
PAUSE = 0.12

# Как часто просыпаемся посмотреть на часы.
TICK = 5 * 60


def msk_now() -> dt.datetime:
    return dt.datetime.utcnow() + dt.timedelta(hours=3)


def time_to_send(now: dt.datetime | None = None) -> bool:
    """Пора ли: утро буднего дня, не раньше половины восьмого."""
    now = now or msk_now()
    if now.isoweekday() == 7:                      # воскресенье
        return False
    after_start = (now.hour, now.minute) >= (HOUR, MINUTE)
    return after_start and now.hour < LATEST_HOUR


def card(group: str, uid: int, custom: bool = True) -> tuple[str, str] | None:
    """
    Утренняя карточка: (разметка для rich, текст для обычного письма).

    None означает «сегодня нечего показывать» — выходной или день без
    пар. Решение принимается здесь, а не в рассылке: расписание уже
    загружено, и второй раз ходить за ним незачем.
    """
    sched = api.fetch_schedule(group)
    today = msk_now().date()
    day = today.isoweekday()
    if day > 6:
        return None

    shift = storage.shift_for(uid, sched.get("semestr", ""))
    week = api.week_of_cycle(today, sched.get("semestr", ""), shift)
    slots = api.slots_of(sched, week, day)
    if not slots:
        return None

    first = slots[0]
    gaps = api.gaps_of(slots)
    n = len(slots)

    # Шапка отвечает на то, ради чего письмо и открывают: во сколько
    # выходить и сколько это продлится.
    head = (f'{em.ico("wave", custom)} <b>Доброе утро!</b> '
            f'{api.DAY_NAMES[day]}, {api.human_date(today)}')
    facts = [f'первая в {first["from"]}',
             f'{n} {render.plural(n, "пара", "пары", "пар")}',
             f'до {slots[-1]["to"]}']
    if gaps:
        longest = max(gaps, key=lambda g: g.get("minutes") or 0)
        facts.append(f'окно {render.human_gap(longest["minutes"])}')
    line = " · ".join(facts)

    rich_html = (f'<h3>{head}</h3><p><i>{render.esc(group)} · {line}</i></p>'
                 + f'<table bordered compact>'
                 + rich.lesson_rows(slots, None, custom)
                 + '</table>')

    text = render.schedule_card(group, sched, week, day, week, custom=custom)
    plain = (f'{em.ico("wave", custom)} <b>Доброе утро!</b>\n'
             f'<i>{render.esc(line)}</i>\n\n{text}')
    return rich_html, render.clamp(plain)


def send_all(send_rich, send_plain, now: dt.datetime | None = None) -> int:
    """
    Один утренний круг. Возвращает, скольким ушло.

    Отправку передают снаружи: этот модуль не должен знать про Telegram,
    иначе его нельзя было бы прогнать в проверках.
    """
    now = now or msk_now()
    today = now.date().isoformat()
    sent = 0
    for uid, group, last in storage.morning_list():
        if last == today:
            continue
        try:
            made = card(group, uid)
        except Exception as e:                          # noqa: BLE001
            log.info("расписание для %s не собралось: %s", group, e)
            continue
        if not made:
            # Выходной или день без пар — молчим, но отмечаем день:
            # иначе следующий круг попробует снова.
            storage.morning_sent(uid, today)
            continue
        rich_html, plain = made
        ok = False
        try:
            ok = send_rich(uid, rich_html)
        except Exception as e:                          # noqa: BLE001
            log.info("rich-карточка %s не ушла: %s", uid, e)
        if not ok:
            try:
                ok = send_plain(uid, plain)
            except Exception as e:                      # noqa: BLE001
                log.info("утренняя карточка %s не ушла: %s", uid, e)
        if not ok:
            # Последняя попытка — без премиум-эмодзи: их Telegram
            # отклоняет целиком у тех, кому имя бота не куплено на
            # Fragment, а расписание человеку нужно в любом виде.
            try:
                simple = card(group, uid, custom=False)
                ok = bool(simple) and send_plain(uid, simple[1])
            except Exception as e:                      # noqa: BLE001
                log.info("простая карточка %s не ушла: %s", uid, e)
        if ok:
            storage.morning_sent(uid, today)
            sent += 1
        time.sleep(PAUSE)
    if sent:
        log.info("утренних карточек отправлено: %d", sent)
    return sent


def run_in_background(send_rich, send_plain) -> threading.Thread:
    """Будильник. Просыпается раз в пять минут и смотрит на часы."""
    def loop():
        time.sleep(90)
        while True:
            try:
                if time_to_send():
                    send_all(send_rich, send_plain)
            except Exception:
                log.exception("утренняя рассылка сорвалась")
            time.sleep(TICK)

    t = threading.Thread(target=loop, name="morning", daemon=True)
    t.start()
    return t
