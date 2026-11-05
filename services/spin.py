# -*- coding: utf-8 -*-
from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

import config
from db.models import User, Spin, Payout
from services.users import calc_chance, build_state, activate_referral, _ensure_aware


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _angle_for_sector(sector: dict) -> float:
    half = sector.get("half", 15.0)
    return sector["a"] + random.uniform(-half * 0.6, half * 0.6)


def _pick_prize(tier: str) -> dict | None:
    pool = [p for p in config.PRIZES if p["tier"] == tier]
    if not pool:
        pool = [p for p in config.PRIZES if p["tier"] in ("bear", "skin")]
    return random.choice(pool) if pool else None


async def do_spin(session: AsyncSession, user: User) -> dict:
    if not (user.captcha_passed and user.sponsors_passed):
        return {"error": "not_onboarded", "state": build_state(user)}

    now = _utcnow()

    last_at = _ensure_aware(user.last_spin_at)
    if last_at and (now - last_at).total_seconds() < getattr(config, "SPIN_RATE_LIMIT_SECONDS", 2):
        return {"error": "rate", "state": build_state(user)}

    next_at = _ensure_aware(user.next_spin_at)
    daily_ready = (next_at is None) or (next_at <= now)

    if (user.spins or 0) <= 0 and daily_ready and not user.streak_frozen:
        user.spins = 1

    total = (user.spins or 0) + (user.extra_spins or 0) + (user.paid_spins or 0)
    if total <= 0:
        wait_sec = int((next_at - now).total_seconds()) if (next_at and next_at > now) else config.COOLDOWN_HOURS * 3600
        return {"error": "cooldown", "next_spin_seconds": max(1, wait_sec), "state": build_state(user)}

    kind = "daily"
    if user.spins and user.spins > 0:
        user.spins -= 1
        kind = "daily"
    elif user.extra_spins and user.extra_spins > 0:
        user.extra_spins -= 1
        kind = "extra"
    elif user.paid_spins and user.paid_spins > 0:
        user.paid_spins -= 1
        kind = "paid"
    else:
        return {"error": "no_spins", "state": build_state(user)}

    chance = calc_chance(user.active_friends or 0)
    current_streak = user.streak or 0
    new_streak = current_streak + 1 if kind == "daily" else current_streak
    pity = (kind == "daily") and (new_streak >= config.PITY_DAY)

    roll = random.uniform(0, 100)
    win = pity or (roll < chance)

    sector = None
    cell_type = "nothing"
    prize = None
    payout = None
    paw = None

    if not win:
        paw_roll = random.uniform(0, 100)
        if config.PAWS_NEED > 0 and paw_roll < config.PAW_CHANCE:
            paw_sectors = [s for s in config.WHEEL_SECTORS if s["type"] == "paw"]
            if paw_sectors:
                sector = random.choice(paw_sectors)
                cell_type = "paw"
                user.paws = (user.paws or 0) + 1
                if user.paws >= config.PAWS_NEED:
                    win = True
                    user.paws = 0
                    paw = {
                        "count": config.PAWS_NEED,
                        "need": config.PAWS_NEED,
                        "completed": True,
                        "left": 0,
                    }
                else:
                    paw = {
                        "count": user.paws,
                        "need": config.PAWS_NEED,
                        "completed": False,
                        "left": config.PAWS_NEED - user.paws,
                    }
        if not win and not paw:
            nothings = [s for s in config.WHEEL_SECTORS if s["type"] == "nothing"]
            sector = random.choice(nothings) if nothings else config.WHEEL_SECTORS[0]
            cell_type = "nothing"

    if win:
        if paw and paw.get("completed"):
            bear_sectors = [s for s in config.WHEEL_SECTORS if s["type"] == "bear"]
            sector = random.choice(bear_sectors) if bear_sectors else config.WHEEL_SECTORS[0]
            cell_type = "bear"
            prize = _pick_prize("bear")
        else:
            win_types = ["bear", "skin", "premium"] if config.PREMIUM_PRIZE else ["bear", "skin"]
            cell_type = random.choice(win_types)
            candidates = [s for s in config.WHEEL_SECTORS if s["type"] == cell_type]
            sector = random.choice(candidates) if candidates else config.WHEEL_SECTORS[0]
            cell_type = sector["type"]

            if cell_type == "premium":
                prize = {"gift_id": "premium", "tier": "premium", "stars": 0, "name": "Telegram Premium"}
            elif cell_type == "nft":
                prize = _pick_prize("nft") or {"gift_id": "nft_vice_cream", "tier": "nft", "stars": 0, "name": "NFT"}
            else:
                prize = _pick_prize(cell_type if cell_type in ("bear", "skin") else "bear")

        if prize:
            payout = Payout(
                user_id=user.id,
                gift_id=prize["gift_id"],
                tier=prize.get("tier"),
                status="pending",
                sender=config.USERBOT_USERNAME,
            )
            session.add(payout)
            await session.flush()

    angle = _angle_for_sector(sector)
    turns = random.randint(5, 8)
    slot_num = sector.get("slot") if isinstance(sector.get("slot"), int) else None

    if kind == "daily":
        user.streak = 0 if (win and pity) else new_streak
        user.last_spin_at = now
        user.next_spin_at = now + timedelta(hours=config.COOLDOWN_HOURS)
    else:
        user.last_spin_at = now

    lose_once = False
    if not win and not paw and not user.onetime_respin_offered and (user.total_friends or 0) == 0:
        lose_once = True
        user.onetime_respin_offered = True

    spin = Spin(
        user_id=user.id,
        kind=kind,
        win=win,
        pity=pity,
        chance=chance,
        prize_gift_id=prize["gift_id"] if prize else None,
        payout_id=payout.id if payout else None,
        wheel_angle=angle,
        wheel_id=config.WHEEL_ID,
        cell_type=cell_type,
    )
    session.add(spin)
    await session.flush()
    if payout:
        payout.spin_id = spin.id

    await session.commit()
    await activate_referral(session, user)
    await session.refresh(spin)
    if payout:
        await session.refresh(payout)

    next_at_updated = _ensure_aware(user.next_spin_at)
    next_sec = int(max(0, (next_at_updated - now).total_seconds())) if next_at_updated else config.COOLDOWN_HOURS * 3600
    can_exchange = bool(win and prize and prize.get("tier") not in ("premium", "nft") and config.EXCHANGE_SPINS > 0)

    return {
        "spin_id": spin.id,
        "kind": kind,
        "first_spin": (user.streak or 0) <= 1 and kind == "daily",
        "win": win,
        "pity": pity,
        "chance": chance,
        "base_chance": config.BASE_CHANCE,
        "chance_steps": config.CHANCE_STEPS,
        "lose_once": lose_once,
        "choice": can_exchange,
        "exchange_spins": config.EXCHANGE_SPINS if can_exchange else 0,
        "cooldown_hours": config.COOLDOWN_HOURS,
        "next_spin_seconds": next_sec,
        "streak": user.streak or 0,
        "milestone": {"day": config.PITY_DAY, "prize": True, "spins": 1} if (pity and win) else None,
        "next_milestone": {"day": config.PITY_DAY, "prize": True, "streak": user.streak or 0},
        "prize": prize,
        "payout_id": payout.id if payout else None,
        "sender": config.GIFT_SENDER if win else None,
        "paw": paw,
        "wheel": {
            "angle": round(angle, 2),
            "cell": slot_num,
            "turns": turns,
            "id": config.WHEEL_ID,
        },
        "burst_seq": 1,
        "_notify_loss": not win and not paw,
        "_user_tg_id": user.telegram_id,
        "_streak": user.streak or 0,
        "_chance": chance,
    }
