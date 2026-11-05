# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    spins: Mapped[int] = mapped_column(Integer, default=0)
    extra_spins: Mapped[int] = mapped_column(Integer, default=0)
    paid_spins: Mapped[int] = mapped_column(Integer, default=0)

    streak: Mapped[int] = mapped_column(Integer, default=0)
    streak_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    paws: Mapped[int] = mapped_column(Integer, default=0)

    active_friends: Mapped[int] = mapped_column(Integer, default=0)
    total_friends: Mapped[int] = mapped_column(Integer, default=0)
    ref_parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    last_spin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_spin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    onetime_respin_used: Mapped[bool] = mapped_column(Boolean, default=False)
    onetime_respin_offered: Mapped[bool] = mapped_column(Boolean, default=False)
    wall_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    wall_active: Mapped[bool] = mapped_column(Boolean, default=False)

    captcha_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    sponsors_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    partner_bonus_claimed: Mapped[bool] = mapped_column(Boolean, default=False)

    stars_spent: Mapped[int] = mapped_column(Integer, default=0)
    ref_code: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    spins_log: Mapped[list["Spin"]] = relationship(back_populates="user")
    payouts: Mapped[list["Payout"]] = relationship(back_populates="user")


class Spin(Base):
    __tablename__ = "spins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # daily|paid|extra|bonus
    win: Mapped[bool] = mapped_column(Boolean, default=False)
    pity: Mapped[bool] = mapped_column(Boolean, default=False)
    chance: Mapped[int] = mapped_column(Integer, default=1)
    prize_gift_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payout_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wheel_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    wheel_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cell_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="spins_log")


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    invitee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    spin_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("spins.id"), nullable=True)
    gift_id: Mapped[str] = mapped_column(String(64))
    tier: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|sending|sent|failed|kept|exchanged
    sender: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="payouts")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    charge_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    stars_amount: Mapped[int] = mapped_column(Integer, default=0)
    spins_granted: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaptchaSession(Base):
    __tablename__ = "captcha_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    answer: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
