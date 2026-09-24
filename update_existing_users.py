import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from database.db import initialize_db, get_all_users, update_user_name

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing from .env file.")
        return

    print("Step 1: Ensuring database schema has 'name' column...")
    initialize_db()

    print("Step 2: Fetching all users from database...")
    users = get_all_users()
    print(f"Found {len(users)} users in database.\n")

    bot = Bot(token=BOT_TOKEN)
    updated_count = 0

    for chat_id, current_name, subscribed in users:
        try:
            chat = await bot.get_chat(chat_id)
            user_info = f"@{chat.username}" if chat.username else (f"{chat.first_name or ''} {chat.last_name or ''}".strip() or str(chat_id))
            update_user_name(chat_id, user_info)
            print(f"✓ Chat ID {chat_id:12} | Name updated to: {user_info}")
            updated_count += 1
        except Exception as e:
            print(f"✗ Chat ID {chat_id:12} | Error fetching info: {e}")

    print(f"\nDone! Successfully updated names for {updated_count}/{len(users)} users in PostgreSQL database.")


if __name__ == "__main__":
    asyncio.run(main())
