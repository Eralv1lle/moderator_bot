from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
import asyncio

from config import config
from tg.handlers import routers
from config import config

proxy = "socks5://216.128.138.177:1080"
session = AiohttpSession(proxy=proxy)

bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher()
dp.include_routers(*routers)


async def start_bot():
    await dp.start_polling(bot)