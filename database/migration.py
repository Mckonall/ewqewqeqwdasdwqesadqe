import sqlite3


DB_PATH = "shop.db"


def migrate():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(products)")

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "city" not in columns:

        cursor.execute(
            """
            ALTER TABLE products
            ADD COLUMN city TEXT DEFAULT 'Trójmiasto'
            """
        )

        print("Added column: city")

    else:

        print("Column city already exists")

    if "image" not in columns:

        cursor.execute(
            """
            ALTER TABLE products
            ADD COLUMN image TEXT
            """
        )

        print("Added column: image")

    else:

        print("Column image already exists")

    conn.commit()

    conn.close()

    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate()