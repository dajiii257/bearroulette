# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import SessionLocal
from services.init_data import validate_init_data
from services.users import get_or_create_user
from db.models import User


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    x_init_data: str | None = Header(default=None, alias="X-Init-Data"),
    session: AsyncSession = Depends(get_db),
) -> User:
    if not x_init_data:
        raise HTTPException(status_code=401, detail="missing initData")

    data = validate_init_data(x_init_data)
    if not data or not data.get("user"):
        raise HTTPException(status_code=401, detail="invalid initData")

    tg_user = data["user"]
    user = await get_or_create_user(
        session,
        telegram_id=int(tg_user["id"]),
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        last_name=tg_user.get("last_name"),
    )
    return user
