import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, WEBAPP_URL


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN не задан. Укажи BOT_TOKEN в .env или положи токен в token_bot.txt / bot_token.txt."
    )


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть мини‑приложение",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    await message.answer(
        "Привет! Нажми кнопку ниже, чтобы открыть мини‑приложение.",
        reply_markup=kb,
    )


@dp.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(f"Ты написал: {message.text}")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

