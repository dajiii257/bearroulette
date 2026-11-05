# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func

import config
from db.database import SessionLocal
from db.models import User, Spin, Payout
from bot.keyboards.inline import admin_menu_kb

router = Router()


class BroadcastState(StatesGroup):
    waiting_text = State()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Админ-панель", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "adm_stats")
async def adm_stats(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    async with SessionLocal() as session:
        users = await session.scalar(select(func.count()).select_from(User))
        spins = await session.scalar(select(func.count()).select_from(Spin))
        wins = await session.scalar(select(func.count()).select_from(Spin).where(Spin.win == True))  # noqa
        pending = await session.scalar(
            select(func.count()).select_from(Payout).where(Payout.status == "pending")
        )
        stars = await session.scalar(select(func.coalesce(func.sum(User.stars_spent), 0)))
        captcha_ok = await session.scalar(
            select(func.count()).select_from(User).where(User.captcha_passed == True)  # noqa
        )
        sponsors_ok = await session.scalar(
            select(func.count()).select_from(User).where(User.sponsors_passed == True)  # noqa
        )

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"🔐 Прошли капчу: <b>{captcha_ok}</b>\n"
        f"📢 Прошли спонсоров: <b>{sponsors_ok}</b>\n"
        f"🎰 Всего спинов: <b>{spins}</b>\n"
        f"🎁 Выигрышей: <b>{wins}</b>\n"
        f"⏳ Pending выплат: <b>{pending}</b>\n"
        f"⭐ Stars потрачено: <b>{stars}</b>"
    )
    await cq.message.answer(text)
    await cq.answer()


@router.callback_query(F.data == "adm_top_stars")
async def adm_top_stars(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    async with SessionLocal() as session:
        r = await session.execute(
            select(User).where(User.stars_spent > 0).order_by(User.stars_spent.desc()).limit(15)
        )
        rows = r.scalars().all()

    if not rows:
        await cq.message.answer("Пока никто не тратил Stars.")
        await cq.answer()
        return

    lines = ["⭐ <b>Топ по Stars</b>\n"]
    for i, u in enumerate(rows, 1):
        name = u.username and f"@{u.username}" or u.first_name or str(u.telegram_id)
        lines.append(f"{i}. {name} — <b>{u.stars_spent}</b> ⭐")
    await cq.message.answer("\n".join(lines))
    await cq.answer()


@router.callback_query(F.data == "adm_users")
async def adm_users(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    async with SessionLocal() as session:
        total = await session.scalar(select(func.count()).select_from(User))
        active = await session.scalar(
            select(func.count()).select_from(User).where(User.sponsors_passed == True)  # noqa
        )
        r = await session.execute(select(User).order_by(User.id.desc()).limit(10))
        last = r.scalars().all()

    lines = [
        f"👥 Всего: <b>{total}</b> | Активных: <b>{active}</b>\n",
        "<b>Последние 10:</b>",
    ]
    for u in last:
        name = u.username and f"@{u.username}" or u.first_name or str(u.telegram_id)
        tot_sp = (u.spins or 0) + (u.extra_spins or 0) + (u.paid_spins or 0)
        lines.append(f"• {name} (id={u.telegram_id}) spins={tot_sp}")
    await cq.message.answer("\n".join(lines))
    await cq.answer()


@router.callback_query(F.data == "adm_payouts")
async def adm_payouts(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    async with SessionLocal() as session:
        r = await session.execute(
            select(Payout).where(Payout.status == "pending").order_by(Payout.id.desc()).limit(20)
        )
        rows = r.scalars().all()

    if not rows:
        await cq.message.answer("Нет pending-выплат.")
        await cq.answer()
        return

    lines = ["🎁 <b>Pending выплаты</b>\n"]
    for p in rows:
        lines.append(f"#{p.id} user={p.user_id} gift={p.gift_id} tier={p.tier}")
    await cq.message.answer("\n".join(lines))
    await cq.answer()


@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_start(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_text)
    await cq.message.answer("📣 Пришли текст рассылки (HTML можно). /cancel — отмена.")
    await cq.answer()


@router.message(BroadcastState.waiting_text)
async def adm_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip() == "/cancel":
        await state.clear()
        await message.answer("Отменено.")
        return

    text = message.text or message.caption or ""
    async with SessionLocal() as session:
        r = await session.execute(select(User.telegram_id))
        ids = [row[0] for row in r.all()]

    ok = fail = 0
    for tid in ids:
        try:
            await bot.send_message(tid, text)
            ok += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await state.clear()
    await message.answer(f"Рассылка завершена.\n✅ {ok}\n❌ {fail}")
