# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

import config
from db.models import User, Referral


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _make_ref_code() -> str:
    return secrets.token_urlsafe(8)[:12]


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    ref_code: str | None = None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if changed:
            await session.commit()
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        ref_code=_make_ref_code(),
        spins=0,
    )
    session.add(user)
    await session.flush()

    if ref_code:
        ref_clean = ref_code.strip()
        conds = [User.ref_code == ref_clean]
        if ref_clean.startswith("r") and ref_clean[1:].isdigit():
            conds.append(User.telegram_id == int(ref_clean[1:]))
        elif ref_clean.isdigit():
            conds.append(User.telegram_id == int(ref_clean))

        parent = await session.execute(select(User).where(or_(*conds)))
        parent_user = parent.scalar_one_or_none()
        if parent_user and parent_user.id != user.id:
            user.ref_parent_id = parent_user.id
            parent_user.total_friends = (parent_user.total_friends or 0) + 1
            session.add(
                Referral(inviter_id=parent_user.id, invitee_id=user.id, is_active=False)
            )

    await session.commit()
    await session.refresh(user)
    return user


async def activate_referral(session: AsyncSession, user: User) -> None:
    """Сделать реферала активным после прохождения спонсоров / первого спина."""
    if not user.ref_parent_id:
        return
    result = await session.execute(
        select(Referral).where(Referral.invitee_id == user.id, Referral.is_active == False)  # noqa: E712
    )
    ref = result.scalar_one_or_none()
    if not ref:
        return

    ref.is_active = True
    ref.activated_at = _utcnow()

    parent = await session.get(User, user.ref_parent_id)
    if parent:
        parent.active_friends = (parent.active_friends or 0) + 1
        if parent.active_friends % config.REF_BONUS_EVERY == 0:
            parent.extra_spins = (parent.extra_spins or 0) + config.REF_BONUS_SPINS

    await session.commit()


def calc_chance(active_friends: int) -> int:
    chance = config.BASE_CHANCE
    for step in sorted(config.CHANCE_STEPS, key=lambda s: s["friends"]):
        if active_friends >= step["friends"]:
            chance = step["chance"]
    return min(chance, config.CHANCE_CAP)


def build_state(user: User) -> dict:
    now = _utcnow()
    next_spin_seconds = 0
    daily_ready = False

    next_at = _ensure_aware(user.next_spin_at)
    if next_at:
        delta = (next_at - now).total_seconds()
        if delta > 0:
            next_spin_seconds = int(delta)
        else:
            daily_ready = True
    else:
        daily_ready = True

    stored_spins = (user.spins or 0) + (user.extra_spins or 0) + (user.paid_spins or 0)
    free_daily = 1 if (daily_ready and (user.spins or 0) == 0 and user.sponsors_passed and not user.streak_frozen) else 0
    total_spins = stored_spins + free_daily
    chance = calc_chance(user.active_friends or 0)

    return {
        "onboarded": bool(user.captcha_passed and user.sponsors_passed),
        "chance": chance,
        "base_chance": config.BASE_CHANCE,
        "chance_per_friend": config.CHANCE_PER_FRIEND,
        "chance_cap": config.CHANCE_CAP,
        "chance_steps": config.CHANCE_STEPS,
        "rare_gap_days": config.RARE_GAP_DAYS,
        "ref_active_days": config.REF_ACTIVE_DAYS,
        "active_friends": user.active_friends or 0,
        "total_friends": user.total_friends or 0,
        "streak": user.streak or 0,
        "pity_day": config.PITY_DAY,
        "next_prize_day": config.PITY_DAY,
        "streak_frozen": bool(user.streak_frozen),
        "spins": total_spins,
        "daily_available": bool(daily_ready and ((user.spins or 0) > 0 or free_daily > 0)),
        "extra_spins": user.extra_spins or 0,
        "paid_spins": user.paid_spins or 0,
        "paid_spin_stars": config.PAID_SPIN_STARS,
        "cooldown_hours": config.COOLDOWN_HOURS,
        "wall_pending": bool(user.wall_pending),
        "wall_active": bool(user.wall_active),
        "exchange_spins": config.EXCHANGE_SPINS,
        "gift_sender": config.GIFT_SENDER,
        "ref_bonus_every": config.REF_BONUS_EVERY,
        "ref_bonus_spins": config.REF_BONUS_SPINS,
        "next_spin_seconds": 0 if total_spins > 0 else next_spin_seconds,
        "onetime_respin_used": bool(user.onetime_respin_used),
        "onetime_respin_offered": bool(user.onetime_respin_offered),
        "next_milestone": {"day": config.PITY_DAY, "prize": True, "streak": user.streak or 0},
        "milestones": {},
        "paws": user.paws or 0,
        "paws_need": config.PAWS_NEED,
        "paw_chance": config.PAW_CHANCE,
        "friend_partner": config.FRIEND_PARTNER,
        "wheel_paws": config.WHEEL_PAWS,
        "wheel_layout": config.WHEEL_LAYOUT,
        "wheel_id": config.WHEEL_ID,
        "wheel_sectors": config.WHEEL_SECTORS,
        "prizes": config.PRIZES,
        "premium_prize": config.PREMIUM_PRIZE,
        "userbot": config.USERBOT_USERNAME,
        "bot_username": config.BOT_USERNAME,
        "share_text": config.SHARE_TEXT,
    }


async def get_user_by_tg(session: AsyncSession, telegram_id: int) -> User | None:
    r = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return r.scalar_one_or_none()
