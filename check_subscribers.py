import os
from dotenv import load_dotenv
from database.db import get_db_connection

load_dotenv()


def main():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT chat_id, COALESCE(name, 'N/A') FROM users
        WHERE subscribed = TRUE;
    """)
    subscribed_users = cursor.fetchall()
    cursor.close()
    conn.close()

    print("============================================================")
    print(f"       SUBSCRIBED TELEGRAM USERS FROM DB ({len(subscribed_users)} Total)")
    print("============================================================")

    if not subscribed_users:
        print("No subscribed users found in the database.")
        return

    print(f"{'Chat ID':<15} | {'Name'}")
    print("-" * 50)

    for chat_id, name in subscribed_users:
        print(f"{chat_id:<15} | {name}")

    print("============================================================")


if __name__ == "__main__":
    main()
