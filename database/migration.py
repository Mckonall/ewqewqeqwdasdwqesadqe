import os
import sqlite3

# На хостинге используем /data, локально - файл рядом с проектом
DB_PATH = os.getenv("DB_PATH", "/data/shop.db" if os.path.isdir("/data") else "shop.db")


def migrate():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]

    if "city" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN city TEXT DEFAULT 'Trójmiasto'")
        print("Added column: city")
    else:
        print("Column city already exists")

    if "image" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN image TEXT")
        print("Added column: image")
    else:
        print("Column image already exists")

    conn.commit()
    conn.close()
    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate()