# -*- coding: utf-8 -*-
"""Проверка подписки на каналы/чаты."""
from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

import config


MEMBER_OK = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
    ChatMemberStatus.RESTRICTED,  # всё ещё в чате
}


async def is_subscribed(bot: Bot, user_id: int, chat_id) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in MEMBER_OK
    except Exception:
        return False


async def check_channels(bot: Bot, user_id: int, channels: list[dict]) -> tuple[bool, list[dict]]:
    """
    Возвращает (all_ok, missing_list).
    missing_list — каналы, на которые не подписан.
    """
    missing = []
    for ch in channels:
        ok = await is_subscribed(bot, user_id, ch["chat_id"])
        if not ok:
            missing.append(ch)
    return (len(missing) == 0, missing)
