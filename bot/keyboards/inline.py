# -*- coding: utf-8 -*-
from urllib.parse import quote

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import config


def sponsors_kb(channels: list[dict] | None = None) -> InlineKeyboardMarkup:
    channels = channels or config.SPONSOR_CHANNELS
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch["url"])])
    rows.append([InlineKeyboardButton(text="✅ Готово", callback_data="sponsors_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def partners_kb(channels: list[dict] | None = None) -> InlineKeyboardMarkup:
    channels = channels or config.PARTNER_CHANNELS
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(text=f"💝 {ch['title']}", url=ch["url"])])
    rows.append([
        InlineKeyboardButton(text="✅ Проверить и получить +5", callback_data="partners_done")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def open_roulette_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎰 Открыть рулетку",
                    web_app=WebAppInfo(url=config.WEBAPP_URL),
                )
            ]
        ]
    )


def invite_and_home_kb(telegram_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с кнопками 'Пригласить друга' и 'На главную'."""
    invite_link = f"https://t.me/{config.BOT_USERNAME}?start=r{telegram_id}"
    invite_url = f"https://t.me/share/url?url={quote(invite_link)}&text={quote(config.SHARE_TEXT)}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Пригласить друга",
                    url=invite_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎰 На главную",
                    web_app=WebAppInfo(url=config.WEBAPP_URL),
                )
            ]
        ]
    )


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
            [InlineKeyboardButton(text="⭐ Топ по Stars", callback_data="adm_top_stars")],
            [InlineKeyboardButton(text="📣 Рассылка", callback_data="adm_broadcast")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="adm_users")],
            [InlineKeyboardButton(text="🎁 Выдачи (pending)", callback_data="adm_payouts")],
        ]
    )
