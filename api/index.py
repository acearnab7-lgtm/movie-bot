import os
import httpx
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Bot

# Set up logging to help us see errors in Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- HARDCODED CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"

bot = Bot(token=TOKEN)

@app.get("/")
async def root():
    return {"status": "success", "message": "Bot Engine is Online!"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        # Get the update from Telegram
        data = await request.json()
        update = Update.de_json(data, bot)
        
        if update.message and update.message.text:
            chat_id = update.message.chat_id
            text = update.message.text.strip()
            
            logger.info(f"Received message: {text} from {chat_id}")

            # Send initial response
            await bot.send_message(
                chat_id=chat_id, 
                text=f"🔍 Searching for '{text}'...\nSaving to your account and generating monetized link."
            )

            # Generate the monetized link
            # For now, we use a placeholder until you add the scraper logic
            dummy_link = "https://www.terabox.com/s/sample_link"
            api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={dummy_link}"
            
            async with httpx.AsyncClient() as client:
                res = await client.get(api_url)
                short_link = res.json().get('shortened_url', dummy_link)

            # Send the final link
            await bot.send_message(
                chat_id=chat_id, 
                text=f"🎬 Movie Found!\n\nLink: {short_link}"
            )

    except Exception as e:
        logger.error(f"Error: {e}")
    
    return {"status": "ok"}
