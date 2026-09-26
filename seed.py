import asyncio
import sys

import openpyxl
from sqlalchemy import delete

from database.engine import async_session, init_db
from database.models import Product


EXCEL_PATH = "products_template.xlsx"  # put the file next to this script, or change the path here


def load_products_from_excel(path: str) -> list[dict]:

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Products"]

    products = []
    errors = []

    # Row 1 = headers. Row 2+ = data.
    # Columns: product_no, name, description, price, stock, category, city, image
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):

        _product_no, name, description, price, stock, category, city, image = (
            cell.value for cell in row[:8]
        )

        # Skip fully empty rows
        if not any([name, description, price, stock, category, city, image]):
            continue

        if not name or not city or price is None or stock is None:
            errors.append(
                f"Row {row_idx}: missing a required field "
                f"(name/city/price/stock). Skipping this row."
            )
            continue

        try:
            price = float(price)
            stock = int(stock)
        except (TypeError, ValueError):
            errors.append(
                f"Row {row_idx}: price or stock is not a valid number. Skipping this row."
            )
            continue

        products.append({
            "name": str(name).strip(),
            "description": str(description).strip() if description else "",
            "price": price,
            "stock": stock,
            "category": str(category).strip() if category else "",
            "city": str(city).strip(),
            "image": str(image).strip() if image else ""
        })

    if errors:
        print("⚠️ Found problematic rows (skipped):")
        for e in errors:
            print("  -", e)
        print()

    return products


async def seed_from_excel(path: str):

    products = load_products_from_excel(path)

    if not products:
        print("❌ No valid products found in the spreadsheet. Nothing was done.")
        return

    await init_db()

    async with async_session() as session:

        # Clear out every existing product first — this only touches
        # the products table, users/balances/orders are untouched.
        await session.execute(delete(Product))

        for item in products:
            session.add(Product(**item))

        await session.commit()

    print(f"✅ Loaded {len(products)} products from {path} (old products cleared first).")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else EXCEL_PATH
    asyncio.run(seed_from_excel(path))