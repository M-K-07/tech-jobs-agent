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
    check_video_exists
)

# ENV SETUP
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_IDS = [cid.strip() for cid in os.getenv("CHANNEL_ID", "").split(",") if cid.strip()]
BOT_TOKEN = os.getenv("BOT_TOKEN")

youtube = build("youtube", "v3", developerKey=API_KEY)


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
    sent = False

    for chat_id in users:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=content,
                disable_web_page_preview=True
            )
            sent = True
        except Exception as e:
            print(f"Failed for {chat_id}: {e}")
    

    return sent


# -------------------------
# MAIN PIPELINE
# -------------------------

async def fetch_job_listings(bot):
    print("Fetching latest videos...")

    videos = fetch_latest_videos()

    for video in videos:
        video_id = video["video_id"]
        title = video["title"].lower()

        print(f"Processing: {title}")

        # skip duplicates
        if check_video_exists(video_id):
            print("Already processed")
            continue

        # better filter
        if "hiring" not in title and "apply" not in title:
            print("Not a job post")
            continue

        description = video["description"]

        transcript = get_transcript(video_id)

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
            print("Stored in DB")
        else:
            print("Not stored (send failed)")


# -------------------------
# TELEGRAM HANDLERS
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    insert_user_if_not_exists(chat_id)

    await context.bot.send_message(
        chat_id=chat_id,
        text="Welcome to Tech Job Bot. You will receive latest job updates here."
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribe_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="Subscribed successfully")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    unsubscribe_user(chat_id)
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
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    application.run_polling()


if __name__ == "__main__":
    print("Bot started...")
    asyncio.run(main())
    # main_local()