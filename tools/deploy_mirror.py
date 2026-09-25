# -*- coding: utf-8 -*-
"""
Выкладка запасного входа (mirror/worker.js) воркером Cloudflare — одной
командой, без веб-редактора.

Редактор на dash.cloudflare.com не пускает к буферу обмена, и вставить
код руками 16 сентября так и не вышло. Через API — десять секунд.

    set CLOUDFLARE_API_TOKEN=<токен с шаблоном «Edit Cloudflare Workers»>
    python tools/deploy_mirror.py

Токен в репозиторий не кладём и в файлах не храним — только переменная
окружения на время выкладки. Адрес воркера после выкладки положить в
MIRROR_URL в панели Amvera (один раз; при обновлении кода он не меняется).
"""
from __future__ import annotations

import json
import os
import sys

import requests

API = "https://api.cloudflare.com/client/v4"
NAME = os.environ.get("MIRROR_NAME", "miet-mirror")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        print("Нужна переменная CLOUDFLARE_API_TOKEN")
        return 1
    h = {"Authorization": f"Bearer {token}"}
    accounts = requests.get(f"{API}/accounts", headers=h, timeout=30).json().get("result") or []
    if not accounts:
        print("Токен не видит ни одного аккаунта")
        return 1
    acc = accounts[0]["id"]
    code = open(os.path.join(HERE, "mirror", "worker.js"), "rb").read()
    meta = {"main_module": "worker.js", "compatibility_date": "2025-09-01"}
    r = requests.put(f"{API}/accounts/{acc}/workers/scripts/{NAME}", headers=h, timeout=60,
                     files={"metadata": (None, json.dumps(meta), "application/json"),
                            "worker.js": ("worker.js", code, "application/javascript+module")})
    if not r.json().get("success"):
        print("Выкладка не прошла:", r.json().get("errors"))
        return 1
    requests.post(f"{API}/accounts/{acc}/workers/scripts/{NAME}/subdomain", headers=h,
                  timeout=60, json={"enabled": True, "previews_enabled": False})
    sub = (requests.get(f"{API}/accounts/{acc}/workers/subdomain", headers=h,
                        timeout=30).json().get("result") or {}).get("subdomain")
    url = f"https://{NAME}.{sub}.workers.dev"
    health = requests.get(url + "/api/health", timeout=30)
    print("Выложено:", url)
    print("Проверка /api/health:", health.status_code, health.text[:120])
    return 0 if health.ok else 1


if __name__ == "__main__":
    sys.exit(main())
