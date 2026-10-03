from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# ---------- Main menu (all buttons combined into one inline keyboard) ----------

def main_menu_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏙 Available Cities",
                    callback_data="available_cities"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 My Profile",
                    callback_data="menu_profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Top Up Balance",
                    callback_data="menu_topup"
                ),
                InlineKeyboardButton(
                    text="📋 Reviews",
                    callback_data="menu_reviews"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Lottery",
                    callback_data="menu_lottery"
                ),
                InlineKeyboardButton(
                    text="👤 Invite a Friend",
                    callback_data="menu_invite"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎰 Casino",
                    callback_data="menu_casino"
                ),
                InlineKeyboardButton(
                    text="🥬 Operator",
                    callback_data="menu_operator"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔔 News Channel",
                    callback_data="menu_news"
                ),
                InlineKeyboardButton(
                    text="💬 Chat",
                    callback_data="menu_chat"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Useful Info",
                    callback_data="menu_useful"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧺 Cart",
                    callback_data="menu_cart"
                )
            ]
        ]
    )


# ---------- Top Up Balance keyboards ----------

TOPUP_PRESET_AMOUNTS = [10, 25, 50, 100]


def topup_amount_keyboard() -> InlineKeyboardMarkup:

    buttons = []
    row = []

    for amount in TOPUP_PRESET_AMOUNTS:

        row.append(
            InlineKeyboardButton(
                text=f"${amount}",
                callback_data=f"topup_amount_{amount}"
            )
        )

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="✏️ Custom Amount",
                callback_data="topup_amount_custom"
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="back_to_welcome"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def topup_proof_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data="topup_cancel"
                )
            ]
        ]
    )


def admin_topup_keyboard(request_id: int) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve",
                    callback_data=f"topup_approve_{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"topup_reject_{request_id}"
                )
            ]
        ]
    )


# ---------- Countries -> Cities data ----------

COUNTRIES = {
    "France": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Cannes", "Strasbourg"],
    "Italy": ["Rome", "Milan", "Naples", "Turin", "Venice", "Florence", "Pisa"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Granada", "Toledo", "Ibiza"],
    "Germany": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt am Main", "Dresden", "Nuremberg", "Baden-Baden"],
    "United Kingdom": ["London", "Birmingham", "Glasgow", "Manchester", "Edinburgh", "Oxford", "Cambridge"],
    "Greece": ["Athens", "Thessaloniki", "Patras", "Fira (Santorini)", "Chania (Crete)", "Rhodes"],
    "Portugal": ["Lisbon", "Porto", "Sintra", "Funchal (Madeira)", "Faro"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Zaanse Schans", "Giethoorn", "Delft"],
    "Austria": ["Vienna", "Graz", "Linz", "Salzburg", "Hallstatt", "Innsbruck"],
    "Switzerland": ["Zurich", "Geneva", "Basel", "Lucerne", "Zermatt", "Interlaken"],
    "Czech Republic": ["Prague", "Brno", "Ostrava", "Pilsen", "Cesky Krumlov", "Karlovy Vary"],
    "Poland": ["Warsaw", "Krakow", "Lodz", "Wroclaw", "Poznan", "Gdansk", "Zakopane"],
    "Belgium": ["Brussels", "Antwerp", "Ghent", "Charleroi", "Bruges", "Dinant"],
    "Hungary": ["Budapest", "Debrecen", "Szeged", "Szentendre", "Heviz"],
    "Croatia": ["Zagreb", "Split", "Rijeka", "Dubrovnik", "Zadar"]
}

COUNTRY_FLAGS = {
    "France": "🇫🇷",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Germany": "🇩🇪",
    "United Kingdom": "🇬🇧",
    "Greece": "🇬🇷",
    "Portugal": "🇵🇹",
    "Netherlands": "🇳🇱",
    "Austria": "🇦🇹",
    "Switzerland": "🇨🇭",
    "Czech Republic": "🇨🇿",
    "Poland": "🇵🇱",
    "Belgium": "🇧🇪",
    "Hungary": "🇭🇺",
    "Croatia": "🇭🇷"
}

COUNTRY_LIST = list(COUNTRIES.keys())


def countries_keyboard() -> InlineKeyboardMarkup:

    buttons = []
    row = []

    for index, country in enumerate(COUNTRY_LIST):

        flag = COUNTRY_FLAGS.get(country, "🌍")

        row.append(
            InlineKeyboardButton(
                text=f"{flag} {country}",
                callback_data=f"country_{index}"
            )
        )

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="back_to_welcome"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def country_cities_keyboard(country_index: int) -> InlineKeyboardMarkup:

    country = COUNTRY_LIST[country_index]
    cities = COUNTRIES[country]
    flag = COUNTRY_FLAGS.get(country, "🏙")

    buttons = []
    row = []

    for city_index, city in enumerate(cities):

        row.append(
            InlineKeyboardButton(
                text=f"{flag} {city}",
                callback_data=f"ccity_{country_index}_{city_index}"
            )
        )

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back to Countries",
                callback_data="available_cities"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------- Casino (guess the number) ----------

CASINO_COST = 2.5
CASINO_PRIZE = 50.0
CASINO_MAX_NUMBER = 30


def casino_numbers_keyboard() -> InlineKeyboardMarkup:

    buttons = []
    row = []

    for number in range(1, CASINO_MAX_NUMBER + 1):

        row.append(
            InlineKeyboardButton(
                text=str(number),
                callback_data=f"casino_guess_{number}"
            )
        )

        if len(row) == 5:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="back_to_welcome"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def casino_result_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎰 Play Again",
                    callback_data="menu_casino"
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


# ---------- Reviews (placeholder data) ----------

REVIEWS = [
    "⭐⭐⭐⭐⭐\n\"Fast delivery, exactly as described. Will order again!\"\n— Customer #1, Paris",
    "⭐⭐⭐⭐⭐\n\"Great quality, packaging was discreet and neat.\"\n— Customer #2, Berlin",
    "⭐⭐⭐⭐\n\"Good product overall, delivery took a bit longer than expected.\"\n— Customer #3, Amsterdam",
    "⭐⭐⭐⭐⭐\n\"Best shop I've used so far, very responsive operator.\"\n— Customer #4, Rome",
    "⭐⭐⭐⭐⭐\n\"Smooth process from order to delivery. Highly recommend.\"\n— Customer #5, Vienna",
    "⭐⭐⭐⭐\n\"Solid experience, prices are fair for the quality.\"\n— Customer #6, Prague",
    "⭐⭐⭐⭐⭐\n\"Second time ordering, consistent quality both times.\"\n— Customer #7, Warsaw",
    "⭐⭐⭐⭐⭐\n\"Everything arrived quickly and as ordered. Thanks!\"\n— Customer #8, Zurich",
    "⭐⭐⭐⭐\n\"Good communication, minor delay but worth the wait.\"\n— Customer #9, Brussels",
    "⭐⭐⭐⭐⭐\n\"Very satisfied, will recommend to friends.\"\n— Customer #10, Athens"
]


def reviews_keyboard() -> InlineKeyboardMarkup:

    buttons = []
    row = []

    for index in range(len(REVIEWS)):

        row.append(
            InlineKeyboardButton(
                text=str(index + 1),
                callback_data=f"review_{index}"
            )
        )

        if len(row) == 5:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="back_to_welcome"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def review_detail_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back to Reviews",
                    callback_data="menu_reviews"
                )
            ]
        ]
    )


# ---------- Useful Info ----------

USEFUL_INFO_TEXT = (
    "ℹ️ <b>Useful Information</b>\n\n"
    "• Delivery usually takes 1 day depending on the city.\n"
    "• All orders are packed discreetly.\n"
    "• 🚚 Delivery to your address(treasure)📍\n"
    "• If you have any issue with your order, contact the Operator.\n"
    "• Top up your balance before placing an order — see 💰 Top Up Balance.\n"
    "• Check 📋 Reviews to see feedback from other customers.\n\n"
    "If you have questions not covered here, use 🥬 Operator to reach support."
)


def useful_info_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back_to_welcome"
                )
            ]
        ]
    )


# ---------- Products inline keyboard (for a chosen city) ----------

def products_keyboard(products, country_index: int, city_index: int, back_callback: str = "available_cities") -> InlineKeyboardMarkup:

    buttons = []

    for product in products:

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📦 {product.name} — ${product.price:.2f}",
                    callback_data=f"product_{product.id}_{country_index}_{city_index}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data=back_callback
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------- Single product card keyboard ----------

def product_keyboard(product_id: int, country_index: int, city_index: int) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Buy",
                    callback_data=f"buy_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data=f"ccity_{country_index}_{city_index}"
                )
            ]
        ]
    )