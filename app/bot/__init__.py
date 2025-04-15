from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from fastapi import Request

from app.bot.dialogs import setup_dialogs
from app.bot.dialogs.all_booking import router_all_booking
from app.bot.dialogs.faq import router_faq
from app.bot.dialogs.get_user_jwt import router_get_jwt
from app.bot.dialogs.profile import router_profile
from app.bot.dialogs.send_notification import router_notification
from app.bot.router import router
from app.bot.utils import Bot
from app.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL


async def run_bot_webhook():
    me = await bot.get_me()

    await bot.set_webhook(
        WEBHOOK_URL,
        drop_pending_updates=True,
        allowed_updates=["message", "edited_channel_post", "callback_query"],
    )


storage = MemoryStorage()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=storage)

dp.include_router(router_profile)
dp.include_router(router)
dp.include_router(router_notification)
dp.include_router(router_faq)
dp.include_router(router_get_jwt)
dp.include_router(router_all_booking)

setup_dialogs(dp)


async def process_update(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)


def get_bot():
    return bot
