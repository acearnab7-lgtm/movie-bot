import os
import httpx
from fastapi import FastAPI, Request
from telegram import Update, Bot
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- HARDCODED CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"

# CORRECTED PASSWORD: Using Arnab123
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

bot = Bot(token=TOKEN)
client = AsyncIOMotorClient(MONGO_URL)
db = client['movie_bot_db']
collection = db['links']

# Fix for 500 Error: Browser-friendly route
@app.get("/")
async def root():
    return {"status": "success", "message": "Bot is online! Use /api/index for webhooks."}

async def shorten_url(url):
    """Converts your TeraBox link to a monetized short link."""
    api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={url}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(api_url)
            return res.json().get('shortened_url', url)
        except:
            return url

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        
        if update.message and update.message.text:
            chat_id = update.message.chat_id
            movie_query = update.message.text.strip().lower()

            # 1. Search Database first
            stored = await collection.find_one({"name": movie_query})
            if stored:
                await bot.send_message(chat_id=chat_id, text=f"✅ Found in Database!\n{stored['short_link']}")
                return {"status": "ok"}

            # 2. Status message
            status = await bot.send_message(chat_id=chat_id, text=f"🔍 Searching for '{movie_query}' and saving to your account...")

            # 3. TeraBox Placeholder (Replace with your actual scraping logic)
            found_terabox_link = "https://www.terabox.com/s/sample_link" 
            
            # 4. Shorten & Save to DB
            final_link = await shorten_url(found_terabox_link)
            await collection.insert_one({"name": movie_query, "short_link": final_link})

            await bot.edit_message_text(chat_id=chat_id, message_id=status.message_id, 
                                        text=f"🎬 Movie Ready!\n\nLink: {final_link}")
    except Exception as e:
        print(f"Error occurred: {e}")

    return {"status": "ok"}
