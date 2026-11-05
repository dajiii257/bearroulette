# -*- coding: utf-8 -*-
"""
Точка входа: FastAPI (Mini App + API) + aiogram polling в фоне.
Запуск:  python main.py
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from db.database import init_db
from api.routes import game as game_routes
from bot.handlers import start as start_handlers
from bot.handlers import admin as admin_handlers
from bot.handlers.notify import send_loss_messages

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, "INFO"))
logger = logging.getLogger("bearbot")

WEBAPP_DIR = Path(__file__).parent / "webapp"

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(start_handlers.router)
dp.include_router(admin_handlers.router)


async def loss_notifier(telegram_id: int, streak: int, chance: int):
    await send_loss_messages(bot, telegram_id, streak, chance)


game_routes.loss_notifier = loss_notifier
game_routes.bot_instance = bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("DB ready")

    # polling в фоне
    poll_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Bot polling started")
    yield
    poll_task.cancel()
    try:
        await poll_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()


app = FastAPI(title="Bear Bot API", lifespan=lifespan)

# API
app.include_router(game_routes.router, prefix="/api")

# статика Mini App
if WEBAPP_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEBAPP_DIR / "assets"), name="assets")
    app.mount("/fonts", StaticFiles(directory=WEBAPP_DIR / "fonts"), name="fonts")
    app.mount("/vendor", StaticFiles(directory=WEBAPP_DIR / "vendor"), name="vendor")

    @app.get("/")
    async def index():
        return FileResponse(WEBAPP_DIR / "index.html")

    @app.get("/app.js")
    async def app_js():
        return FileResponse(WEBAPP_DIR / "app.js", media_type="application/javascript")

    @app.get("/app.css")
    async def app_css():
        return FileResponse(WEBAPP_DIR / "app.css", media_type="text/css")


def main():
    if config.BOT_TOKEN.startswith("PUT_"):
        logger.error("Укажи BOT_TOKEN в config.py")
        return
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
