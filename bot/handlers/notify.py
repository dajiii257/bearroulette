# -*- coding: utf-8 -*-
"""Уведомления в чат бота после спина."""
from __future__ import annotations

from aiogram import Bot

import config
from bot.keyboards.inline import partners_kb, open_roulette_kb, invite_and_home_kb


async def send_loss_messages(bot: Bot, telegram_id: int, streak: int, chance: int) -> None:
    left = max(config.PITY_DAY - streak, 0)
    text = (
        "☹️ Сегодня не повезло\n\n"
        f"Следующий прокрут будет доступен ровно через {config.COOLDOWN_HOURS} часа. "
        "Пригласи друга — и шанс на подарок станет вдвое выше!\n\n"
        f"• Серия дней: {streak}/{config.PITY_DAY}\n"
        f"• Ещё {left} дней подряд — и гарантированный подарок"
    )
    try:
        await bot.send_message(telegram_id, text, reply_markup=invite_and_home_kb(telegram_id))
    except Exception:
        pass

    try:
        await bot.send_message(
            telegram_id,
            f"💝 Получи дополнительные +{config.PARTNER_SPIN_BONUS} прокрутов за подписку на наших партнеров.",
            reply_markup=partners_kb(),
        )
    except Exception:
        pass


async def send_win_message(bot: Bot, telegram_id: int, prize_name: str) -> None:
    try:
        await bot.send_message(
            telegram_id,
            f"🎉 Поздравляем! Ты выиграл: <b>{prize_name}</b>\n"
            "Подарок скоро придёт на аккаунт.",
            reply_markup=open_roulette_kb(),
        )
    except Exception:
        pass
