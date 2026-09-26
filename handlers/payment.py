from datetime import datetime

import stripe

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select

from database.engine import async_session
from database.models import User, TopUpRequest
from keyboards.menus import (
    topup_amount_keyboard,
    topup_proof_keyboard,
    admin_topup_keyboard,
    main_menu_keyboard
)
from config import ADMIN_ID, STRIPE_SECRET_KEY


router = Router()

stripe.api_key = STRIPE_SECRET_KEY

# Wallet address shown to users for manual USDT (TON network) top-ups
TOPUP_USDT_TON_WALLET = "UQB4U-idTCAA0_qf1PWzeIP96wRd19Yjjouve_HvnCc06_NJ"


# ---------- Stripe checkout link, used by cart.py at checkout ----------

def create_payment_link(order_id: int, amount: float, description: str) -> str:
    """
    Creates a Stripe Checkout session for a cart order and returns
    the URL the user should be sent to in order to pay.

    `amount` is expected in USD.
    """

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": description},
                "unit_amount": int(round(amount * 100)),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="https://t.me/vapecity_bot?start=success",
        cancel_url="https://t.me/vapecity_bot?start=cancel",
        metadata={"order_id": str(order_id)},
    )

    return session.url


class TopUpStates(StatesGroup):
    waiting_amount = State()
    waiting_proof = State()


# ---------- Step 1: open the Top Up menu ----------

@router.callback_query(F.data == "menu_topup")
async def topup_menu(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await callback.message.answer(
        "💰 <b>Top Up Balance</b>\n\n"
        "Choose an amount below, or tap "
        "\"✏️ Custom Amount\" to enter your own:",
        parse_mode="HTML",
        reply_markup=topup_amount_keyboard()
    )

    await callback.answer()


# ---------- Step 2: user picks a preset amount or asks for a custom one ----------

@router.callback_query(F.data.startswith("topup_amount_"))
async def topup_amount_chosen(callback: CallbackQuery, state: FSMContext):

    value = callback.data.removeprefix("topup_amount_")

    if value == "custom":

        await state.set_state(TopUpStates.waiting_amount)

        await callback.message.answer(
            "✏️ Enter the amount in USD you'd like to top up "
            "(e.g. <code>37.5</code>):",
            parse_mode="HTML"
        )

        await callback.answer()
        return

    amount = float(value)

    await ask_for_proof(callback.message, state, amount)

    await callback.answer()


# ---------- Step 2b: user typed a custom amount ----------

@router.message(TopUpStates.waiting_amount)
async def topup_custom_amount(message: Message, state: FSMContext):

    text = message.text.strip().replace(",", ".")

    try:
        amount = float(text)

        if amount <= 0:
            raise ValueError

    except ValueError:

        await message.answer(
            "⚠️ Please enter a valid positive number, e.g. "
            "<code>25</code> or <code>37.5</code>",
            parse_mode="HTML"
        )
        return

    await ask_for_proof(message, state, amount)


async def ask_for_proof(message: Message, state: FSMContext, amount: float):

    await state.update_data(amount=amount)
    await state.set_state(TopUpStates.waiting_proof)

    await message.answer(
        f"💵 <b>Amount: ${amount:.2f}</b>\n\n"
        f"💠 <b>Pay with USDT (TON network)</b>\n"
        f"Send exactly <b>${amount:.2f}</b> worth of USDT to this wallet:\n"
        f"<code>{TOPUP_USDT_TON_WALLET}</code>\n"
        f"<i>(tap the address to copy it)</i>\n\n"
        f"⚠️ Make sure to send on the <b>TON network</b> only — "
        f"other networks will not arrive.\n\n"
        f"After paying, send a screenshot of the transaction, or a "
        f"text message with your transaction ID / hash.\n\n"
        f"An admin will review it and confirm your top-up manually "
        f"— usually within 30 minutes.",
        parse_mode="HTML",
        reply_markup=topup_proof_keyboard()
    )


# ---------- Step 3: user cancels ----------

@router.callback_query(F.data == "topup_cancel")
async def topup_cancel(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    await callback.message.answer(
        "❌ Top up cancelled.",
        reply_markup=main_menu_keyboard()
    )

    await callback.answer()


# ---------- Step 3b: user sends proof (photo or text) ----------

@router.message(TopUpStates.waiting_proof, F.photo | F.text)
async def topup_proof_received(message: Message, state: FSMContext, bot: Bot):

    data = await state.get_data()
    amount = data.get("amount")

    if amount is None:
        await state.clear()
        await message.answer(
            "⚠️ Something went wrong, please start over via "
            "💰 Top Up Balance."
        )
        return

    proof_file_id = None
    proof_text = None

    if message.photo:
        proof_file_id = message.photo[-1].file_id
        proof_text = message.caption
    else:
        proof_text = message.text

    async with async_session() as session:

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )

        user = result.scalar_one_or_none()

        if user is None:
            await state.clear()
            await message.answer("⚠️ User not found, please /start again.")
            return

        request = TopUpRequest(
            user_id=user.id,
            amount=amount,
            status="pending",
            proof_file_id=proof_file_id,
            proof_text=proof_text
        )

        session.add(request)
        await session.commit()
        await session.refresh(request)

        request_id = request.id

    await state.clear()

    await message.answer(
        "✅ Your top-up request has been sent to the admin.\n"
        "You'll be notified as soon as it's confirmed.",
        reply_markup=main_menu_keyboard()
    )

    telegram_user = message.from_user
    username = f"@{telegram_user.username}" if telegram_user.username else telegram_user.first_name

    admin_text = (
        f"🆕 <b>New Top-Up Request</b>\n\n"
        f"👤 User: {username} (ID: <code>{telegram_user.id}</code>)\n"
        f"💵 Amount: <b>${amount:.2f}</b>\n"
        f"🆔 Request ID: <code>{request_id}</code>"
    )

    if proof_file_id:

        if proof_text:
            admin_text += f"\n📝 Note: {proof_text}"

        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=proof_file_id,
            caption=admin_text,
            parse_mode="HTML",
            reply_markup=admin_topup_keyboard(request_id)
        )

    else:

        admin_text += f"\n📝 Confirmation: {proof_text}"

        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="HTML",
            reply_markup=admin_topup_keyboard(request_id)
        )


# ---------- Step 4: admin approves / rejects ----------

@router.callback_query(F.data.startswith("topup_approve_"))
async def topup_approve(callback: CallbackQuery, bot: Bot):

    request_id = int(callback.data.removeprefix("topup_approve_"))
    await process_topup_decision(callback, bot, request_id, approve=True)


@router.callback_query(F.data.startswith("topup_reject_"))
async def topup_reject(callback: CallbackQuery, bot: Bot):

    request_id = int(callback.data.removeprefix("topup_reject_"))
    await process_topup_decision(callback, bot, request_id, approve=False)


async def process_topup_decision(
    callback: CallbackQuery,
    bot: Bot,
    request_id: int,
    approve: bool
):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Admins only.", show_alert=True)
        return

    async with async_session() as session:

        result = await session.execute(
            select(TopUpRequest).where(TopUpRequest.id == request_id)
        )

        request = result.scalar_one_or_none()

        if request is None:
            await callback.answer("⚠️ Request not found.", show_alert=True)
            return

        if request.status != "pending":
            await callback.answer(f"Already {request.status}.", show_alert=True)
            return

        result = await session.execute(
            select(User).where(User.id == request.user_id)
        )

        user = result.scalar_one_or_none()

        request.processed_at = datetime.utcnow()

        if approve:
            request.status = "approved"
            user.balance += request.amount
        else:
            request.status = "rejected"

        await session.commit()

        telegram_id = user.telegram_id
        new_balance = user.balance
        amount = request.amount

    # Notify the user
    if approve:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"✅ Your top-up of <b>${amount:.2f}</b> has been approved!\n"
                f"💰 New balance: <b>${new_balance:.2f}</b>"
            ),
            parse_mode="HTML"
        )
        status_note = "\n\n✅ <b>APPROVED</b>"
    else:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"❌ Your top-up request of <b>${amount:.2f}</b> was "
                f"rejected. Please contact support if this is a mistake."
            ),
            parse_mode="HTML"
        )
        status_note = "\n\n❌ <b>REJECTED</b>"

    # Update the admin's message so it's clear this request is handled
    try:
        if callback.message.caption is not None:
            await callback.message.edit_caption(
                caption=callback.message.caption + status_note,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                callback.message.text + status_note,
                parse_mode="HTML"
            )
    except Exception:
        pass

    await callback.answer("Done ✅" if approve else "Rejected ❌")