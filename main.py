import asyncio
import logging

from tg import start_bot


async def main():
    await start_bot()


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as err:
        print(f"Упал: {err}")