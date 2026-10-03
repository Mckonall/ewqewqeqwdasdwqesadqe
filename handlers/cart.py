from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.engine import async_session
from database.models import CartItem, User, Order, OrderItem, Product
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = Router()


async def get_user(session, telegram_id):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one()


@router.callback_query(F.data.startswith("buy_"))
async def add_to_cart(callback: CallbackQuery):

    try:
        product_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("Product not found.", show_alert=True)
        return

    async with async_session() as session:

        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if product is None:
            await callback.answer("Product not found.", show_alert=True)
            return

        if product.stock <= 0:
            await callback.answer("This product is currently unavailable.", show_alert=True)
            return

        user = await get_user(session, callback.from_user.id)

        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product.id
            )
        )
        cart_item = result.scalar_one_or_none()

        if cart_item is None:
            session.add(
                CartItem(user_id=user.id, product_id=product.id, quantity=1)
            )
        else:
            cart_item.quantity += 1

        await session.commit()

    await callback.answer("Added to cart! 🧺", show_alert=False)


async def render_cart(callback: CallbackQuery, session, user):
    """
    Builds the cart text + keyboard for the given user and sends it
    as a new message (used by show_cart and after removing an item).
    Returns True if the cart had items, False if it was empty.
    """

    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.user_id == user.id)
    )
    items = result.scalars().all()

    if not items:
        return False

    text = "🧺 <b>Your Cart:</b>\n\n"
    total = 0

    buttons = []

    for item in items:
        subtotal = item.product.price * item.quantity
        total += subtotal
        text += f"{item.product.name} × {item.quantity} = ${subtotal:.2f}\n"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Remove {item.product.name}",
                    callback_data=f"cart_remove_{item.id}"
                )
            ]
        )

    text += f"\n<b>Total: ${total:.2f}</b>\n💰 <b>Your balance: ${user.balance:.2f}</b>"

    buttons.append(
        [InlineKeyboardButton(text="✅ Checkout (pay from balance)", callback_data="checkout")]
    )
    buttons.append(
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_welcome")]
    )

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

    return True


@router.callback_query(F.data == "menu_cart")
async def show_cart(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_user(session, callback.from_user.id)

        await callback.message.delete()

        has_items = await render_cart(callback, session, user)

        if not has_items:
            await callback.answer("Your cart is empty.", show_alert=True)
            return

    await callback.answer()


@router.callback_query(F.data.startswith("cart_remove_"))
async def remove_from_cart(callback: CallbackQuery):

    try:
        cart_item_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Item not found.", show_alert=True)
        return

    async with async_session() as session:

        result = await session.execute(
            select(CartItem).where(CartItem.id == cart_item_id)
        )
        cart_item = result.scalar_one_or_none()

        user = await get_user(session, callback.from_user.id)

        if cart_item is None or cart_item.user_id != user.id:
            await callback.answer("Item not found.", show_alert=True)
            return

        await session.delete(cart_item)
        await session.commit()

        await callback.message.delete()

        has_items = await render_cart(callback, session, user)

        if not has_items:
            await callback.message.answer("🧺 Your cart is now empty.")

    await callback.answer("Removed from cart.")


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_user(session, callback.from_user.id)

        result = await session.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == user.id)
        )
        items = result.scalars().all()

        if not items:
            await callback.answer("Your cart is empty.", show_alert=True)
            return

        # Re-check stock right before charging, in case it changed
        for item in items:
            if item.product.stock < item.quantity:
                await callback.answer(
                    f"⚠️ Not enough stock for {item.product.name}.",
                    show_alert=True
                )
                return

        total = sum(item.product.price * item.quantity for item in items)

        if user.balance < total:
            missing = total - user.balance
            await callback.answer(
                f"⚠️ Insufficient balance. You need ${missing:.2f} more. "
                f"Top up your balance first.",
                show_alert=True
            )
            return

        user.balance -= total

        order = Order(user_id=user.id, total=total, status="paid")
        session.add(order)
        await session.flush()

        for item in items:
            session.add(OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.product.price
            ))
            item.product.stock -= item.quantity
            await session.delete(item)

        await session.commit()

        order_id = order.id
        new_balance = user.balance

    await callback.message.delete()

    await callback.message.answer(
        f"✅ <b>Order #{order_id} confirmed!</b>\n\n"
        f"💵 Paid: ${total:.2f}\n"
        f"💰 Remaining balance: ${new_balance:.2f}\n\n"
        f"Thank you for your purchase!\n\n"
        f"Our team will process your order shortly and send you information🫶\n\n",
        parse_mode="HTML"
    )

    await callback.answer()