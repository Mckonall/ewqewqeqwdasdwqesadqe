import random

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import os

from sqlalchemy import select, func

from database.engine import async_session
from database.models import Product, User, Order

from keyboards.menus import (
    countries_keyboard,
    country_cities_keyboard,
    products_keyboard,
    product_keyboard,
    reviews_keyboard,
    review_detail_keyboard,
    casino_numbers_keyboard,
    casino_result_keyboard,
    CASINO_COST,
    CASINO_PRIZE,
    CASINO_MAX_NUMBER,
    COUNTRY_LIST,
    COUNTRIES,
    REVIEWS
)


router = Router()

# ---------- EDIT ME: put your real invite link / operator contact here ----------

# Your bot's referral/invite link template. Replace YOUR_BOT_USERNAME with your
# actual bot username (without @). {user_id} is filled in automatically per user.
INVITE_LINK_TEMPLATE = "https://t.me/ZzZazzaPluG_bot"

# Your operator's contact — a @username or a t.me link. Shown as-is to users.
OPERATOR_CONTACT = "@zaza41124"

# Your news channel link — a t.me link. Shown as-is to users.
NEWS_CHANNEL_LINK = "https://t.me/+X5OnMWK939M4MDJi"


@router.callback_query(F.data == "available_cities")
async def available_cities(callback: CallbackQuery):

    await callback.message.edit_caption(
        caption=(
            "🌍 <b>Available Countries</b>\n\n"
            "Choose your country:"
        ),
        parse_mode="HTML",
        reply_markup=countries_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data.startswith("country_"))
async def country_selected(callback: CallbackQuery):

    try:
        country_index = int(callback.data.split("_")[1])
        country = COUNTRY_LIST[country_index]

    except (IndexError, ValueError):

        await callback.answer(
            "Country not found.",
            show_alert=True
        )

        return

    await callback.message.edit_caption(
        caption=(
            f"🌍 <b>{country}</b>\n\n"
            "Choose a city:"
        ),
        parse_mode="HTML",
        reply_markup=country_cities_keyboard(country_index)
    )

    await callback.answer()


@router.callback_query(F.data.startswith("ccity_"))
async def city_selected(callback: CallbackQuery):

    try:
        _, country_index_str, city_index_str = callback.data.split("_")
        country_index = int(country_index_str)
        city_index = int(city_index_str)

        country = COUNTRY_LIST[country_index]
        city = COUNTRIES[country][city_index]

    except (IndexError, ValueError):

        await callback.answer(
            "City not found.",
            show_alert=True
        )

        return

    async with async_session() as session:

        result = await session.execute(
            select(Product).where(
                Product.city == city,
                Product.stock > 0
            )
        )

        products = result.scalars().all()

    back_callback = f"country_{country_index}"

    if not products:

        await callback.message.edit_caption(
            caption=(
                f"🏙 <b>{city}</b>\n\n"
                "There are currently no "
                "available products in this city."
            ),
            parse_mode="HTML",
            reply_markup=country_cities_keyboard(country_index)
        )

        await callback.answer()
        return

    await callback.message.edit_caption(
        caption=(
            f"🏙 <b>{city}</b>\n\n"
            "🛍 <b>Available Products</b>\n\n"
            "Choose a product:"
        ),
        parse_mode="HTML",
        reply_markup=products_keyboard(
            products,
            country_index=country_index,
            city_index=city_index,
            back_callback=back_callback
        )
    )

    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def product_selected(callback: CallbackQuery):

    try:
        parts = callback.data.split("_")
        product_id = int(parts[1])
        country_index = int(parts[2])
        city_index = int(parts[3])

    except (IndexError, ValueError):

        await callback.answer(
            "Product not found.",
            show_alert=True
        )

        return

    async with async_session() as session:

        result = await session.execute(
            select(Product).where(
                Product.id == product_id
            )
        )

        product = result.scalar_one_or_none()

    if product is None:

        await callback.answer(
            "Product not found.",
            show_alert=True
        )

        return

    if product.stock <= 0:

        await callback.answer(
            "This product is currently unavailable.",
            show_alert=True
        )

        return

    text = (
        f"📦 <b>{product.name}</b>\n\n"
        f"🏙 <b>City:</b> {product.city}\n"
        f"💰 <b>Price:</b> "
        f"${product.price:.2f}\n"
        f"📦 <b>Available:</b> "
        f"{product.stock}\n\n"
    )

    if product.description:
        text += (
            f"📝 <b>Description:</b>\n"
            f"{product.description}\n\n"
        )

    keyboard = product_keyboard(product.id, country_index, city_index)

    if product.image and os.path.isfile(product.image):

        try:

            photo = FSInputFile(
                product.image
            )

            await callback.message.answer_photo(
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )

            await callback.message.delete()

        except Exception:

            await callback.message.edit_caption(
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )

    else:

        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    await callback.answer()


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):

    async with async_session() as session:

        result = await session.execute(
            select(Product).where(
                Product.stock > 0
            )
        )

        products = result.scalars().all()

    if not products:

        await callback.message.delete()

        await callback.message.answer(
            "🛍 <b>Available Products</b>\n\n"
            "There are currently no products.",
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await callback.message.delete()

    await callback.message.answer(
        "🛍 <b>Available Products</b>\n\n"
        "Choose a product:",
        parse_mode="HTML",
        reply_markup=products_keyboard(products)
    )

    await callback.answer()


@router.callback_query(F.data == "back_to_welcome")
async def back_to_welcome(callback: CallbackQuery):

    from handlers.start import send_welcome

    async with async_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

    if user is None:
        await callback.answer(
            "Please send /start again.",
            show_alert=True
        )
        return

    await callback.message.delete()

    await send_welcome(
        callback.message,
        user,
        callback.from_user
    )

    await callback.answer()


@router.callback_query(F.data == "menu_profile")
async def my_profile(callback: CallbackQuery):

    async with async_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "Please send /start again.",
                show_alert=True
            )
            return

        result = await session.execute(
            select(func.count(Order.id)).where(
                Order.user_id == user.id
            )
        )

        orders_count = result.scalar() or 0

        result = await session.execute(
            select(func.coalesce(func.sum(Order.total), 0.0)).where(
                Order.user_id == user.id
            )
        )

        total_spent = result.scalar() or 0.0

    telegram_user = callback.from_user

    if telegram_user.username:
        name = f"@{telegram_user.username}"
    else:
        name = telegram_user.first_name

    member_since = user.created_at.strftime("%d.%m.%Y")

    text = (
        f"👤 <b>My Profile</b>\n\n"
        f"📛 <b>Name:</b> {name}\n"
        f"🆔 <b>ID:</b> <code>{telegram_user.id}</code>\n"
        f"💰 <b>Balance:</b> ${user.balance:.2f}\n"
        f"🛍 <b>Total Orders:</b> {orders_count}\n"
        f"💸 <b>Total Spent:</b> ${total_spent:.2f}\n"
        f"📅 <b>Member Since:</b> {member_since}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_welcome"
                )
            ]
        ]
    )

    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "menu_reviews")
async def reviews_list(callback: CallbackQuery):

    await callback.message.edit_caption(
        caption=(
            "📋 <b>Reviews</b>\n\n"
            "Choose a review to read:"
        ),
        parse_mode="HTML",
        reply_markup=reviews_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data.startswith("review_"))
async def review_detail(callback: CallbackQuery):

    try:
        review_index = int(callback.data.split("_")[1])
        review_text = REVIEWS[review_index]

    except (IndexError, ValueError):

        await callback.answer(
            "Review not found.",
            show_alert=True
        )

        return

    await callback.message.edit_caption(
        caption=(
            f"📋 <b>Review #{review_index + 1}</b>\n\n"
            f"{review_text}"
        ),
        parse_mode="HTML",
        reply_markup=review_detail_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "menu_casino")
async def casino_menu(callback: CallbackQuery):

    await callback.message.edit_caption(
        caption=(
            f"🎰 <b>Casino — Guess the Number</b>\n\n"
            f"💵 <b>Cost:</b> ${CASINO_COST:.2f} per attempt\n"
            f"🎯 <b>Prize:</b> ${CASINO_PRIZE:.2f} if you guess right\n"
            f"🔢 Pick a number from 1 to {CASINO_MAX_NUMBER}.\n"
            f"You get <b>one guess</b> per attempt — good luck!"
        ),
        parse_mode="HTML",
        reply_markup=casino_numbers_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data.startswith("casino_guess_"))
async def casino_guess(callback: CallbackQuery):

    try:
        guess = int(callback.data.split("_")[2])

    except (IndexError, ValueError):

        await callback.answer(
            "Invalid number.",
            show_alert=True
        )

        return

    async with async_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "Please send /start again.",
                show_alert=True
            )
            return

        if user.balance < CASINO_COST:
            await callback.answer(
                f"⚠️ Insufficient balance. You need ${CASINO_COST:.2f} "
                f"to play. Top up your balance first.",
                show_alert=True
            )
            return

        user.balance -= CASINO_COST

        winning_number = random.randint(1, CASINO_MAX_NUMBER)
        won = guess == winning_number

        if won:
            user.balance += CASINO_PRIZE

        await session.commit()

        new_balance = user.balance

    if won:
        text = (
            f"🎉 <b>Jackpot!</b>\n\n"
            f"You guessed <b>{guess}</b> and the number was "
            f"<b>{winning_number}</b> — correct!\n\n"
            f"💰 You won <b>${CASINO_PRIZE:.2f}</b>\n"
            f"💳 New balance: <b>${new_balance:.2f}</b>"
        )
    else:
        text = (
            f"😔 <b>Not this time.</b>\n\n"
            f"You guessed <b>{guess}</b>, the number was "
            f"<b>{winning_number}</b>.\n\n"
            f"💵 ${CASINO_COST:.2f} was deducted.\n"
            f"💳 Balance: <b>${new_balance:.2f}</b>"
        )

    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML",
        reply_markup=casino_result_keyboard()
    )

    await callback.answer()


# ---------- Placeholder handlers for menu buttons not yet built ----------
# NOTE: "menu_topup" and "menu_casino" were removed from this set —
# they're now handled by their own dedicated flows above / in payment.py.
# "menu_chat" also has its own dedicated handler below (static message).

@router.callback_query(F.data.in_({
    "menu_lottery"
}))
async def menu_placeholder(callback: CallbackQuery):

    await callback.answer(
        "🚧 This section is coming soon.",
        show_alert=True
    )


@router.callback_query(F.data == "menu_chat")
async def menu_chat(callback: CallbackQuery):

    await callback.answer(
        "🔒 Chat is available from 3 purchases.",
        show_alert=True
    )


@router.callback_query(F.data == "menu_invite")
async def menu_invite(callback: CallbackQuery):

    link = INVITE_LINK_TEMPLATE.format(user_id=callback.from_user.id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_welcome"
                )
            ]
        ]
    )

    await callback.message.answer(
        "👤 <b>Invite a Friend</b>\n\n"
        "Share your personal invite link:\n"
        f"<code>{link}</code>\n"
        "<i>(tap the link to copy it)</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "menu_operator")
async def menu_operator(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_welcome"
                )
            ]
        ]
    )

    await callback.message.answer(
        "🥬 <b>Operator</b>\n\n"
        f"Contact our operator: {OPERATOR_CONTACT}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()


@router.callback_query(F.data == "menu_news")
async def menu_news(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Open Channel",
                    url=NEWS_CHANNEL_LINK
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_welcome"
                )
            ]
        ]
    )

    await callback.message.answer(
        "🔔 <b>News Channel</b>\n\n"
        "Stay updated — join our news channel:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await callback.answer()