from aiogram import Bot, Dispatcher
import asyncio

from config import config
from tg.handlers import routers
from config import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.include_routers(*routers)


async def start_bot():
    await dp.start_polling(bot)