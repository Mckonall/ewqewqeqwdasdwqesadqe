from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile
)
from aiogram.filters import CommandStart

from sqlalchemy import select, func

from database.engine import async_session
from database.models import User, Order
from keyboards.menus import (
    main_menu_keyboard,
    USEFUL_INFO_TEXT,
    useful_info_keyboard
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):

    async with async_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=message.from_user.id,
                age_verified=False,
                balance=0.0
            )

            session.add(user)

            await session.commit()
            await session.refresh(user)

        if not user.age_verified:

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="I'm 18+",
                            callback_data="confirm_age"
                        ),
                        InlineKeyboardButton(
                            text="I'm under 18",
                            callback_data="deny_age"
                        )
                    ]
                ]
            )

            await message.answer(
                "This store is available only to users "
                "aged 18 and over.\n\n"
                "Please confirm your age:",
                reply_markup=keyboard
            )

            return

        await send_welcome(
            message,
            user,
            message.from_user
        )


async def send_welcome(
    message: Message,
    user: User,
    telegram_user
):

    async with async_session() as session:

        result = await session.execute(
            select(func.count(Order.id)).where(
                Order.user_id == user.id
            )
        )

        purchased = result.scalar() or 0

    photo = FSInputFile("229.jpg")

    if telegram_user.username:
        name = f"@{telegram_user.username}"
    else:
        name = telegram_user.first_name

    text = (
        f"👋 <b>Welcome, {name}!</b>\n\n"
        f"🆔 <b>Your ID:</b> "
        f"<code>{telegram_user.id}</code>\n"
        f"💰 <b>Balance:</b> "
        f"${user.balance:.2f}\n"
        f"🛍 <b>Purchased:</b> "
        f"{purchased}\n\n"
        f"⚠️ <b>Balance deposits made using "
        f"the payment methods listed above are processed "
        f"AUTOMATICALLY within 30 minutes.</b>\n\n"
        f"👇 <b>Choose an option below:</b>"
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "confirm_age")
async def confirm_age(callback: CallbackQuery):

    async with async_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=callback.from_user.id,
                age_verified=True,
                balance=0.0
            )

            session.add(user)

        else:

            user.age_verified = True

        await session.commit()
        await session.refresh(user)

    await callback.message.delete()

    await send_welcome(
        callback.message,
        user,
        callback.from_user
    )

    await callback.answer()


@router.callback_query(F.data == "deny_age")
async def deny_age(callback: CallbackQuery):

    await callback.message.edit_text(
        "Sorry, access is restricted to users "
        "aged 18 and over."
    )

    await callback.answer()


@router.callback_query(F.data == "menu_useful")
async def menu_useful(callback: CallbackQuery):

    await callback.message.edit_caption(
        caption=USEFUL_INFO_TEXT,
        parse_mode="HTML",
        reply_markup=useful_info_keyboard()
    )

    await callback.answer()