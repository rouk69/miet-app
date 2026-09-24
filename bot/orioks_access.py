# -*- coding: utf-8 -*-
"""
Кому открыт раздел «Учёба» (всё, что про ОРИОКС).

С 24.09.2026 по слову владельца раздел закрыт всем, кроме него. Открыть
можно двумя путями, и оба — только в руках владельца из ADMIN_IDS:

- **одному человеку** — «Доступ к разделам» в его карточке в админке
  (раздел `orioks` в `roles.sections`, там же, где кружки). Полному
  админу он сам собой НЕ достаётся — это не право модератора;
- **всем сразу** — настройка `orioks_open` в админке.

Закрытие не стирает подключение: токен и сессия остаются, и когда доступ
вернут, всё заработает без повторного ввода пароля. Молчит и сторож —
баллы и объявления закрытому не приходят.

Сдача работ (`orioks_homework`) закрыта отдельно и строже: только
владельцу, пока отправка не проверена вживую.
"""
from __future__ import annotations

from . import analytics, appconf

SECTION = "orioks"
FLAG = "orioks_open"


def allowed(me: dict) -> bool:
    """Открыт ли раздел человеку с такими правами (`analytics.identity`)."""
    if me.get("blocked"):
        return False
    return (bool(me.get("root"))
            or SECTION in (me.get("sections") or [])
            or appconf.get(FLAG))


def allowed_id(user_id: int) -> bool:
    """То же по id — для фоновых задач, где прав под рукой нет."""
    # Поздний импорт: api сам импортирует сторожа, а через него и нас.
    from .api import admin_ids
    return allowed(analytics.identity(user_id, admin_ids()))
