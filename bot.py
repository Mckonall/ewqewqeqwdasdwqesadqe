import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database.engine import init_db

from handlers import start, catalog, cart, payment


async def main():

    await init_db()

    bot = Bot(
        token=BOT_TOKEN
    )

    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(payment.router)

    print("Bot started!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())