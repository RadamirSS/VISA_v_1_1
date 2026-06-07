from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import get_settings
from bot.database import init_db
from bot.handlers import admin, order, start


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required to run the Telegram bot.")

    init_db(settings.database_url)

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(start.router)
    dispatcher.include_router(order.router)
    dispatcher.include_router(admin.router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
