import os
import asyncio
from datetime import datetime
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
    check_video_exists
)

# ENV SETUP
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_IDS = [cid.strip() for cid in os.getenv("CHANNEL_ID", "").split(",") if cid.strip()]
BOT_TOKEN = os.getenv("BOT_TOKEN")

youtube = build("youtube", "v3", developerKey=API_KEY)


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# -------------------------
# YOUTUBE FETCH (FIXED)
# -------------------------

def get_uploads_playlist_id(channel_id):
    channel_req = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    channel_res = channel_req.execute()

    if not channel_res.get("items"):
        return None

    return channel_res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_latest_videos(limit=3):
    videos = []

    for channel_id in CHANNEL_IDS:
        uploads_id = get_uploads_playlist_id(channel_id)
        if not uploads_id:
            continue

        playlist_req = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_id,
            maxResults=limit
        )
        playlist_res = playlist_req.execute()

        for item in playlist_res["items"]:
            snippet = item["snippet"]

            videos.append({
                "video_id": snippet["resourceId"]["videoId"],
                "title": snippet["title"],
                "description": snippet["description"]
            })

    return videos


# -------------------------
# FORMATTER
# -------------------------

def format_content(job):
    return f"""

Company: {job['company_name']}

Role: {job['role']}

Location: {job['location']}

Package: {job['package_range'] or 'Not specified'}

Apply Here:
{job['job_url']}

Requirements:
{job['job_requirements']}

==========================
"""


# -------------------------
# NOTIFY USERS
# -------------------------

async def notify_users(bot, content):
    users = get_subscribed_users()
    log(f"📢 Sending job notification to {len(users)} subscribed user(s)...")
    sent = False

    for chat_id in users:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=content,
                disable_web_page_preview=True
            )
            sent = True
            log(f"  ✓ Notification successfully delivered to Chat ID: {chat_id}")
        except Exception as e:
            log(f"  ✗ Failed to deliver notification to Chat ID {chat_id}: {e}")
    

    return sent


# -------------------------
# MAIN PIPELINE
# -------------------------

async def fetch_job_listings(bot):
    log("🔍 Fetching latest videos from YouTube...")

    videos = fetch_latest_videos()
    log(f"📹 Found {len(videos)} video(s) from target channels.")

    for video in videos:
        video_id = video["video_id"]
        title = video["title"]

        log(f"➡️ Processing video: '{title}' ({video_id})")

        # skip duplicates
        if check_video_exists(video_id):
            log("  ⏭️ Already processed in DB, skipping.")
            continue

        # better filter
        if "hiring" not in title.lower() and "apply" not in title.lower():
            log("  ⏭️ Title does not match job post criteria ('hiring'/'apply'), skipping.")
            continue

        description = video["description"]

        log("  📥 Fetching transcript...")
        transcript = get_transcript(video_id)

        log("  🤖 Extracting job details via LLM...")
        job_link = get_job_link(video["title"], description)
        job_details = get_job_details(video["title"], transcript)

        job_listing = {
            "video_id": video_id,
            "title": video["title"],
            "description": description,
            "company_name": job_details.get("company_name"),
            "role": job_details.get("role"),
            "location": job_details.get("location"),
            "job_url": job_link,
            "package_range": job_details.get("package_range"),
            "job_requirements": job_details.get("job_requirements"),
        }

        content = format_content(job_listing)

        success = await notify_users(bot, content)

        if success:
            insert_job_if_not_exists(job_listing)
            log("  ✅ Stored job listing in database.")
        else:
            log("  ⚠️ Job listing not stored in database (send failed).")


# -------------------------
# TELEGRAM HANDLERS
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_info = f"@{user.username}" if user and user.username else (user.full_name if user and user.full_name else str(chat_id))
    
    insert_user_if_not_exists(chat_id, name=user_info)
    log(f"👤 User started bot: {user_info} (Chat ID: {chat_id})")

    await context.bot.send_message(
        chat_id=chat_id,
        text="Welcome to Tech Job Bot. You will receive latest job updates here."
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_info = f"@{user.username}" if user and user.username else (user.full_name if user and user.full_name else str(chat_id))

    subscribe_user(chat_id, name=user_info)
    log(f"🔔 User SUBSCRIBED: {user_info} (Chat ID: {chat_id})")

    await context.bot.send_message(chat_id=chat_id, text="Subscribed successfully")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_info = f"@{user.username}" if user and user.username else (user.full_name if user and user.full_name else str(chat_id))

    unsubscribe_user(chat_id)
    log(f"🔕 User UNSUBSCRIBED: {user_info} (Chat ID: {chat_id})")

    await context.bot.send_message(chat_id=chat_id, text="Unsubscribed successfully")


# -------------------------
# ENTRY POINT
# -------------------------

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    bot = application.bot

    await fetch_job_listings(bot)


def main_local():
    log("🤖 Tech Job Bot starting in polling mode...")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    log("✅ Bot is online and listening for user commands (/start, /subscribe, /unsubscribe)...")
    application.run_polling()


if __name__ == "__main__":
    log("🚀 Script initiated.")
    # asyncio.run(main())
    main_local()
