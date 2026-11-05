# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

import config
from db.database import SessionLocal
from db.models import CaptchaSession, User, Payment
from services.captcha import get_captcha
from services.users import get_or_create_user, activate_referral, calc_chance, _ensure_aware
from services.subscription import check_channels
from bot.keyboards.inline import sponsors_kb, open_roulette_kb

router = Router()


class CaptchaState(StatesGroup):
    waiting = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject, bot: Bot):
    ref_code = None
    buy_spin_req = False
    if command.args:
        arg = command.args.strip()
        if arg == "buy_spin":
            buy_spin_req = True
        elif arg.startswith("ref_"):
            ref_code = arg[4:]
        else:
            ref_code = arg

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            ref_code=ref_code,
        )

        if buy_spin_req and user.sponsors_passed and config.PAID_SPIN_STARS > 0:
            await message.answer_invoice(
                title="Дополнительный прокрут",
                description="1 прокрут колеса подарков",
                payload=f"spin_{user.telegram_id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="1 прокрут", amount=config.PAID_SPIN_STARS)],
            )
            return

        if user.sponsors_passed:
            chance = calc_chance(user.active_friends or 0)
            await message.answer(
                f"🧸 Доступен прокрут рулетки!\n\n"
                f"• Текущий шанс: {chance}%\n"
                f"• Серия дней: {user.streak or 0}/{config.PITY_DAY}",
                reply_markup=open_roulette_kb(),
            )
            return

        if user.captcha_passed:
            await message.answer(
                "🧸 Чтобы получить подарок, подпишись на каналы ниже и нажми «Готово». "
                "Подарки оплачивают спонсоры: без них раздачи бы не было. Спасибо!",
                reply_markup=sponsors_kb(),
            )
            return

    answer, png = get_captcha()
    async with SessionLocal() as session:
        session.add(CaptchaSession(telegram_id=message.from_user.id, answer=answer.upper()))
        await session.commit()

    await state.set_state(CaptchaState.waiting)
    await message.answer_photo(
        photo=BufferedInputFile(png, filename="captcha.png"),
        caption="🔐 Введи код с картинки, чтобы продолжить:",
    )


@router.message(CaptchaState.waiting)
async def captcha_answer(message: Message, state: FSMContext):
    text = (message.text or "").strip().upper()
    now = datetime.now(timezone.utc)

    async with SessionLocal() as session:
        r = await session.execute(
            select(CaptchaSession)
            .where(CaptchaSession.telegram_id == message.from_user.id)
            .order_by(CaptchaSession.id.desc())
            .limit(1)
        )
        cap = r.scalar_one_or_none()
        created = _ensure_aware(cap.created_at) if cap else None
        expired = bool(created and (now - created).total_seconds() > config.CAPTCHA_TTL_SECONDS)

        if not cap or expired or cap.answer.upper() != text:
            answer, png = get_captcha()
            session.add(CaptchaSession(telegram_id=message.from_user.id, answer=answer.upper()))
            await session.commit()
            msg = "⏳ Время капчи истекло. Введи новый код:" if expired else "❌ Неверно. Попробуй ещё раз — введи код с картинки:"
            await message.answer_photo(
                photo=BufferedInputFile(png, filename="captcha.png"),
                caption=msg,
            )
            return

        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        user.captcha_passed = True
        await session.commit()

    await state.clear()
    await message.answer(
        "🧸 Чтобы получить подарок, подпишись на каналы ниже и нажми «Готово». "
        "Подарки оплачивают спонсоры: без них раздачи бы не было. Спасибо!",
        reply_markup=sponsors_kb(),
    )


@router.callback_query(F.data == "sponsors_done")
async def sponsors_done(cq: CallbackQuery, bot: Bot):
    ok, missing = await check_channels(bot, cq.from_user.id, config.SPONSOR_CHANNELS)
    if not ok:
        titles = ", ".join(ch["title"] for ch in missing)
        await cq.answer(f"Подпишись на: {titles}", show_alert=True)
        return

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=cq.from_user.id,
            username=cq.from_user.username,
            first_name=cq.from_user.first_name,
            last_name=cq.from_user.last_name,
        )
        if not user.sponsors_passed:
            user.sponsors_passed = True
            user.spins = (user.spins or 0) + config.START_SPINS
            if user.ref_parent_id:
                parent = await session.get(User, user.ref_parent_id)
                if parent and parent.onetime_respin_offered and not parent.onetime_respin_used:
                    parent.onetime_respin_used = True
                    parent.extra_spins = (parent.extra_spins or 0) + 1
                if parent and parent.streak_frozen:
                    parent.streak_frozen = False
            await session.commit()
            await activate_referral(session, user)
            await session.refresh(user)

        chance = calc_chance(user.active_friends or 0)
        streak = user.streak or 0

    await cq.message.answer(
        f"🧸 Доступен прокрут рулетки!\n\n"
        f"• Текущий шанс: {chance}%\n"
        f"• Серия дней: {streak}/{config.PITY_DAY}",
        reply_markup=open_roulette_kb(),
    )
    await cq.answer()


@router.callback_query(F.data == "partners_done")
async def partners_done(cq: CallbackQuery, bot: Bot):
    ok, missing = await check_channels(bot, cq.from_user.id, config.PARTNER_CHANNELS)
    if not ok:
        titles = ", ".join(ch["title"] for ch in missing)
        await cq.answer(f"Подпишись на: {titles}", show_alert=True)
        return

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=cq.from_user.id,
            username=cq.from_user.username,
            first_name=cq.from_user.first_name,
            last_name=cq.from_user.last_name,
        )
        if user.partner_bonus_claimed:
            await cq.answer("Бонус уже получен", show_alert=True)
            return
        user.partner_bonus_claimed = True
        user.extra_spins = (user.extra_spins or 0) + config.PARTNER_SPIN_BONUS
        await session.commit()

    await cq.message.answer(
        f"✅ Начислено +{config.PARTNER_SPIN_BONUS} прокрутов!",
        reply_markup=open_roulette_kb(),
    )
    await cq.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    sp = message.successful_payment
    stars = sp.total_amount
    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        user.paid_spins = (user.paid_spins or 0) + 1
        user.stars_spent = (user.stars_spent or 0) + stars
        session.add(
            Payment(
                user_id=user.id,
                charge_id=sp.telegram_payment_charge_id,
                stars_amount=stars,
                spins_granted=1,
                status="paid",
            )
        )
        await session.commit()

    await message.answer(
        "⭐ Оплата прошла успешно! Начислен +1 прокрут.",
        reply_markup=open_roulette_kb(),
    )
