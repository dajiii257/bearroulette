# -*- coding: utf-8 -*-
"""Валидация Telegram WebApp initData."""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

import config


def validate_init_data(init_data: str) -> dict | None:
    """
    Проверяет подпись initData.
    Возвращает dict с полями (user, auth_date, ...) или None.
    """
    if not init_data:
        return None

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        return None

    user_raw = parsed.get("user")
    user = None
    if user_raw:
        try:
            user = json.loads(user_raw)
        except Exception:
            return None

    return {
        "user": user,
        "auth_date": parsed.get("auth_date"),
        "query_id": parsed.get("query_id"),
        "raw": parsed,
    }


def extract_user_id(init_data: str) -> int | None:
    data = validate_init_data(init_data)
    if not data or not data.get("user"):
        return None
    return int(data["user"]["id"])
