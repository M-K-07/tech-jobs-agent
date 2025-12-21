import os
import asyncio
from dotenv import load_dotenv
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from services.yt_transcript_fetcher import get_transcript
from services.llm_helper import get_job_link, get_job_details
from database.db import (
    insert_job_if_not_exists,
    insert_user_if_not_exists,
    unsubscribe_user,
    subscribe_user,
    get_subscribed_users,
    check_video_exists,
)


# ENV SETUP

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

youtube = build("youtube", "v3", developerKey=API_KEY)


# MESSAGE FORMATTER

def format_content(job):
    return f"""
🏢 Company: {job['company_name']}

💼 Role: {job['role']}

📍 Location: {job['location']}

💰 Package: {job['package_range'] or 'Not specified'}

🔗 Apply Here:  
{job['job_url']}

📋 Requirements:  
{job['job_requirements']}
"""


# NOTIFY USERS (SEND FIRST)

async def notify_users(bot, content):
    users = get_subscribed_users()
    sent_to_anyone = False

    for chat_id in users:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=content,
                disable_web_page_preview=True
            )
            sent_to_anyone = True
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

    return sent_to_anyone

# FETCH + PROCESS JOBS

async def fetch_job_listings(bot):
    search_req = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        maxResults=4,
        order="date",
        type="video",
    )
    search_res = search_req.execute()

    for item in search_res["items"]:
        video_id = item["id"]["videoId"]

        # Skip already processed videos
        if check_video_exists(video_id):
            print(f"⏭ Skipping existing video {video_id}")
            continue

        video_req = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        video_res = video_req.execute()
        video = video_res["items"][0]["snippet"]

        if "hiring" not in video["title"].lower():
            continue

        title = video["title"]
        description = video["description"]

        print("\n==============================")
        print("Processing:", title)

        transcript = get_transcript(video_id)
        job_link = get_job_link(title, description)
        job_details = get_job_details(title, transcript)

        job_listing = {
            "video_id": video_id,
            "title": title,
            "description": description,
            "company_name": job_details.get("company_name"),
            "role": job_details.get("role"),
            "location": job_details.get("location"),
            "job_url": job_link,
            "package_range": job_details.get("package_range"),
            "job_requirements": job_details.get("job_requirements"),
        }

        content = format_content(job_listing)

        # 1️⃣ SEND MESSAGE
        success = await notify_users(bot, content)

        # 2️⃣ STORE ONLY IF SENT
        if success:
            insert_job_if_not_exists(job_listing)
            print("✅ Job stored in DB")
        else:
            print("⚠ Job NOT stored (message failed)")


# TELEGRAM COMMANDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    insert_user_if_not_exists(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="👋 Welcome to Tech Job Bot!\nYou will receive hiring updates here.\n\nUse /unsubscribe to stop."
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribe_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="✅ Subscribed successfully!")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    unsubscribe_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="❌ You have unsubscribed.")


# ENTRY POINT (LOCAL + GITHUB ACTIONS SAFE)

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    bot = application.bot

    # Run only job fetcher (no polling in GitHub Actions)
    await fetch_job_listings(bot)

if __name__ == "__main__":
    # print("Bot started...")
    # application.run_polling()
    asyncio.run(main())
