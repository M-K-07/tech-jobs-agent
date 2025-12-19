from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
from services.yt_transcript_fetcher import get_transcript
from services.llm_helper import get_job_link, get_job_details
from database.db import insert_job_if_not_exists, insert_user_if_not_exists, unsubscribe_user, subscribe_user, get_subscribed_users, check_video_exists
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

CHANNEL_ID = os.getenv("CHANNEL_ID")

BOT_TOKEN = os.getenv("BOT_TOKEN")

youtube = build("youtube", "v3", developerKey=API_KEY)

application = Application.builder().token(BOT_TOKEN).build()
bot = application.bot

async def fetch_job_listings():
    # STEP 1: Get latest video IDs
    search_req = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        maxResults=2,
        order="date",
        type="video",
    )
    search_res = search_req.execute()

    for item in search_res["items"]:
        video_id = item["id"]["videoId"]

        # STEP 2: Get full video details
        video_req = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        video_res = video_req.execute()

        video = video_res["items"][0]["snippet"]
        
        if "hiring" not in video["title"].lower():
            continue

        title = video["title"]
        description = video["description"]  
        print("\n====================\n")
    
        print("Title:\n", title)
        print("\nFull Description:\n", description)
        
        video_exists = check_video_exists(video_id)
        if video_exists:
            print(f"Video {video_id} already processed. Skipping.")
            continue
        
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
        content=format_content(job_listing)
        print("=====================\n")
        print("Job Listing Content:\n",content)
        print("\n=====================\n")
        
        job_id=insert_job_if_not_exists(job_listing)
        
        if job_id:
            await notify_users(job_id, content)

def format_content(job):
    return f"""
🏢 Company: {job['company_name']}

💼 Role: {job['role']}

📍 Location: {job['location']}

💰 Package: {job['package_range'] or 'Not specified'}

🔗 Apply Here:  
{job['job_url']}

📋 Job Requirements:
{job['job_requirements']}
"""


async def notify_users(job_id: int, content: str):
        user_chat_ids = get_subscribed_users()
        for chat_id in user_chat_ids:
            # map_user_to_job(chat_id, job_id)
            await bot.send_message(chat_id=chat_id, text=content)
      
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    insert_user_if_not_exists(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="👋 Welcome to Tech Job Bot! You will receive daily tech job listings here. To unsubscribe, use /unsubscribe.")
    

async def subscribe(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribe_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="✅ You have subscribed to Tech Job Bot!")

async def unsubscribe(update:Update,context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    unsubscribe_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="❌ You have unsubscribed from Tech Job Bot.")
    
if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    # print("Bot started...")
    # application.run_polling()
    asyncio.run(fetch_job_listings())
