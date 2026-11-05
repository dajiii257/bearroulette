# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, get_current_user
from db.models import User, Payout
from services.users import build_state
from services.spin import do_spin
from services.subscription import check_channels
import config

router = APIRouter()

loss_notifier = None
bot_instance = None


@router.post("/state")
async def api_state(user: User = Depends(get_current_user)):
    return build_state(user)


@router.post("/spin")
async def api_spin(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        await request.json()
    except Exception:
        pass

    db_user = await session.get(User, user.id)
    if not db_user:
        return {"error": "user_not_found"}

    result = await do_spin(session, db_user)

    if result.get("error"):
        return result

    if result.pop("_notify_loss", False) and loss_notifier:
        try:
            await loss_notifier(
                telegram_id=result.pop("_user_tg_id"),
                streak=result.pop("_streak", 0),
                chance=result.pop("_chance", 1),
            )
        except Exception:
            pass
    else:
        result.pop("_user_tg_id", None)
        result.pop("_streak", None)
        result.pop("_chance", None)

    return result


@router.post("/offer")
async def api_offer(user: User = Depends(get_current_user)):
    if user.partner_bonus_claimed or not config.PARTNER_CHANNELS:
        return {"offer": None}

    first_ch = config.PARTNER_CHANNELS[0]
    return {
        "offer": {
            "id": "partners_pack",
            "title": first_ch.get("title", "Партнёр"),
            "url": first_ch.get("url", "https://t.me/telegram"),
            "spins": config.PARTNER_SPIN_BONUS,
            "action": "subscribe",
            "hold": 0,
            "hold_days": 0,
        }
    }


@router.post("/offer_claim")
async def api_offer_claim(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    db_user = await session.get(User, user.id)
    if not db_user or db_user.partner_bonus_claimed:
        return {"status": "done"}

    if bot_instance and config.PARTNER_CHANNELS:
        ok, _ = await check_channels(bot_instance, db_user.telegram_id, config.PARTNER_CHANNELS)
        if not ok:
            return {"status": "need"}

    db_user.partner_bonus_claimed = True
    db_user.extra_spins = (db_user.extra_spins or 0) + config.PARTNER_SPIN_BONUS
    await session.commit()
    await session.refresh(db_user)
    return {
        "status": "granted",
        "spins": config.PARTNER_SPIN_BONUS,
        "state": build_state(db_user),
    }


@router.post("/prize")
async def api_prize(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    payout_id = body.get("payout_id")
    action = body.get("action", "keep")

    if not payout_id:
        return {"error": "no_payout"}

    try:
        pid = int(payout_id)
    except (ValueError, TypeError):
        return {"error": "invalid_payout"}

    payout = await session.get(Payout, pid)
    db_user = await session.get(User, user.id)
    if not payout or not db_user or payout.user_id != db_user.id:
        return {"error": "not_found"}

    if payout.status != "pending":
        return {"error": "already_processed", "state": build_state(db_user)}

    if action == "exchange":
        if config.EXCHANGE_SPINS <= 0:
            return {"error": "disabled"}
        payout.status = "exchanged"
        db_user.extra_spins = (db_user.extra_spins or 0) + config.EXCHANGE_SPINS
        await session.commit()
        await session.refresh(db_user)
        return {"status": "exchanged", "state": build_state(db_user)}

    payout.status = "kept"
    await session.commit()
    await session.refresh(db_user)
    return {"status": "kept", "state": build_state(db_user)}


@router.post("/share")
async def api_share(user: User = Depends(get_current_user)):
    return {"id": ""}


@router.post("/invoice")
async def api_invoice(user: User = Depends(get_current_user)):
    if config.PAID_SPIN_STARS <= 0 or not bot_instance:
        return {"error": "disabled"}
    try:
        invoice_url = await bot_instance.create_invoice_link(
            title="Дополнительный прокрут",
            description="1 прокрут колеса подарков",
            payload=f"spin_{user.telegram_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="1 прокрут", amount=config.PAID_SPIN_STARS)],
        )
        return {
            "url": invoice_url,
            "stars": config.PAID_SPIN_STARS,
        }
    except Exception:
        return {"error": "invoice_failed"}


@router.post("/wall_seen")
async def api_wall_seen(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    db_user = await session.get(User, user.id)
    if db_user:
        db_user.wall_pending = False
        await session.commit()
        await session.refresh(db_user)
        return {"state": build_state(db_user)}
    return {"state": build_state(user)}
