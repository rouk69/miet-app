# -*- coding: utf-8 -*-
"""
Читаемость палитры: считает контраст текста к подложкам по WCAG.

Цвет — единственная часть внешнего вида, которую в этой среде можно
проверить честно: браузера здесь нет, а формула контраста есть. И
проверять её нужно, потому что «бледно-серая подпись» выглядит на
макете изящно, а на телефоне под солнцем исчезает совсем.

Пороги WCAG AA: 4.5 для обычного текста, 3.0 для крупного и значков.
Третичному тексту дозволено 3.5 — им набраны подписи под подписями,
которые и должны отступать на второй план, но всё-таки читаться.

    python tools/check_contrast.py
"""
from __future__ import annotations

import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Роль → минимальный контраст к каждой подложке своей темы.
WANT = {
    "text": 4.5,
    "text-secondary": 4.5,
    "text-tertiary": 3.5,
    "primary": 4.5,
    "danger-text": 4.5,
    "warning-text": 4.5,
    "success-text": 4.5,
}

GROUNDS = ("bg", "surface")


def _lum(hexcolor: str) -> float:
    c = hexcolor.lstrip("#")
    channels = []
    for i in (0, 2, 4):
        v = int(c[i:i + 2], 16) / 255
        channels.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a: str, b: str) -> float:
    hi, lo = max(_lum(a), _lum(b)), min(_lum(a), _lum(b))
    return (hi + 0.05) / (lo + 0.05)


def palette(block: str) -> dict:
    """Токены-цвета одного блока: имя без «--» → #RRGGBB."""
    out = {}
    for name, value in re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", block):
        out[name] = value
    return out


def blocks(css: str) -> dict:
    """Светлая тема лежит в :root, тёмная — в :root[data-theme=dark]."""
    out = {}
    for m in re.finditer(r"(:root(?:\[data-theme=\"dark\"\])?)\s*\{([^}]*)\}", css):
        out["тёмная" if "dark" in m.group(1) else "светлая"] = m.group(2)
    return out


def main() -> int:
    css = io.open(os.path.join(ROOT, "css", "tokens.css"), encoding="utf-8").read()
    problems = []
    checked = 0

    for theme, block in blocks(css).items():
        colors = palette(block)
        # Тёмная тема ссылается на свои же токены (--danger-text:
        # var(--danger)) — недостающее берём оттуда же по имени.
        for role, want in WANT.items():
            color = colors.get(role) or colors.get(role.replace("-text", ""))
            if not color:
                problems.append(f"{theme}: нет цвета «{role}»")
                continue
            for ground in GROUNDS:
                under = colors.get(ground)
                if not under:
                    continue
                got = contrast(color, under)
                checked += 1
                if got < want:
                    problems.append(
                        f"{theme}: {role} ({color}) на {ground} ({under}) — "
                        f"{got:.2f} при нужных {want}")

    if problems:
        print("НАЙДЕНО:")
        for p in problems:
            print("  ! " + p)
        return 1
    print(f"палитра читается ({checked} сочетаний проверено)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
