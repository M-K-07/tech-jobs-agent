from telegram.ext import Application
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def send_invitation(bot):

    invitation_message= '''
    
HI, I am a bot that scrapes job application links from YouTube video descriptions and sends them to you.

'''
    # USER_ID=5712432664
    USER_ID=946451791
    await bot.send_message(chat_id=USER_ID, text=invitation_message) 

async def for_her():
    application = Application.builder().token(BOT_TOKEN).build()

    bot = application.bot

    await send_invitation(bot)

if __name__ == "__main__":
    asyncio.run(for_her())