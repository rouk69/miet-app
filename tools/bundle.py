# -*- coding: utf-8 -*-
"""
Сборка модулей приложения в один файл.

Мини-приложение написано ES-модулями без сборщика — так его удобно
править и читать. Но браузер за это платит: тридцать с лишним файлов,
и каждый — отдельный поход по сети. Приложение открывают в метро, на
мобильном интернете, и там это секунды ожидания на ровном месте.

Поэтому исходники остаются модулями, а на Pages уезжает ещё и сборка:
те же модули, сложенные в порядке зависимостей и обёрнутые каждый в
свою функцию, чтобы имена не сталкивались. Таблица `__mod` заменяет
импорты.

Этим же сборщиком пользуется `check_app.py`: он выполняет собранный
код в движке JS. Значит сборка проверяется каждым прогоном проверок —
не «наверное, соберётся», а «выполнилось целиком».
"""
from __future__ import annotations

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IMPORT = re.compile(
    r"^import\s+([\s\S]*?)\s+from\s*['\"](\.[^'\"]+)['\"]\s*;?", re.M)


def modules() -> list:
    """Все файлы модулей — в устойчивом порядке имён."""
    out = []
    for base, _, names in os.walk(os.path.join(ROOT, "js")):
        for n in sorted(names):
            if n.endswith(".js") and n != "bundle.js":
                out.append(os.path.join(base, n))
    return out


def order(files):
    """Модули в порядке зависимостей: сначала те, кого импортируют."""
    deps = {}
    for path in files:
        src = io.open(path, encoding="utf-8").read()
        here = os.path.dirname(path)
        deps[path] = {os.path.normpath(os.path.join(here, m[1]))
                      for m in IMPORT.findall(src)}
    done, out = set(), []
    while len(out) < len(files):
        moved = False
        for path in files:
            if path in done:
                continue
            if deps[path] <= done:
                out.append(path)
                done.add(path)
                moved = True
        if not moved:                       # цикл импортов
            rest = [os.path.relpath(p, ROOT) for p in files if p not in done]
            print("ЦИКЛ ИМПОРТОВ между:", ", ".join(rest))
            out.extend(p for p in files if p not in done)
            break
    return out


def translate(path: str, src: str) -> str:
    """ES-модуль → кусок общего скрипта с ручной таблицей экспортов."""
    key = os.path.relpath(path, ROOT).replace("\\", "/")
    here = os.path.dirname(path)
    body = src
    for clause, rel in IMPORT.findall(src):
        target = os.path.relpath(os.path.normpath(os.path.join(here, rel)),
                                 ROOT).replace("\\", "/")
        names = re.search(r"\{([^}]*)\}", clause)
        lines = []
        if names:
            for part in names.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                src_name, _, alias = part.partition(" as ")
                alias = (alias or src_name).strip()
                lines.append(f"var {alias} = __mod['{target}']"
                             f"['{src_name.strip()}'];")
        head = clause.strip().split(",")[0].strip()
        if head and not head.startswith("{"):
            lines.append(f"var {head} = __mod['{target}']['default'];")
        body = re.sub(r"^import\s+" + re.escape(clause) + r"\s+from\s*['\"]"
                      + re.escape(rel) + r"['\"]\s*;?",
                      "\n".join(lines), body, count=1, flags=re.M)

    exports = []
    for m in re.finditer(r"^export\s+default\s+(?:async\s+)?function\s+"
                         r"([A-Za-z_$][\w$]*)", body, re.M):
        exports.append(("default", m.group(1)))
    body = re.sub(r"^export\s+default\s+", "", body, flags=re.M)

    for m in re.finditer(r"^export\s+(?:async\s+)?(?:const|let|var|function"
                         r"|class)\s+([A-Za-z_$][\w$]*)", body, re.M):
        exports.append((m.group(1), m.group(1)))
    for m in re.finditer(r"^export\s*\{([^}]*)\}", body, re.M):
        for part in m.group(1).split(","):
            part = part.strip()
            if part:
                a, _, b = part.partition(" as ")
                exports.append(((b or a).strip(), a.strip()))
    body = re.sub(r"^export\s*\{[^}]*\}\s*;?", "", body, flags=re.M)
    body = re.sub(r"^export\s+", "", body, flags=re.M)

    table = ", ".join(f"'{name}': {local}" for name, local in exports)
    return (f"__mod['{key}'] = (function () {{\n{body}\n"
            f"return {{{table}}};\n}})();\n")


def build(head: str = "") -> str:
    """Собранное приложение одним куском. `head` — что дописать сверху."""
    parts = [head] if head else []
    parts.append("var __mod = {};")
    for path in order(modules()):
        parts.append(f"/* ==== {os.path.relpath(path, ROOT)} ==== */")
        parts.append(translate(path, io.open(path, encoding="utf-8").read()))
    return "\n".join(parts)
