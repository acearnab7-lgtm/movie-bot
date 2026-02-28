import os
import httpx
from fastapi import FastAPI, Request
from telegram import Update, Bot
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- HARDCODED CREDENTIALS (NO SPACES IN NDUS) ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"
JS_TOKEN = "4389D58831B381B436E1D5A6846BD9ED3D399B8066AA3284A6286CDEF51B56265FB87A12E27186A82ED2CF1E28F3DBDE76DEA1F7E18D95365B72F74BD9D227B0"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"
MONGO_URL = "mongodb+srv://Arnab:Arnab@123@cluster0.ya468bd.mongodb.net/?appName=Cluster0"

bot = Bot(token=TOKEN)
client = AsyncIOMotorClient(MONGO_URL)
db = client['movie_bot_db']
collection = db['links']

# UPGRADE: This GET route prevents the 500 Server Error in your browser
@app.get("/")
async def root():
    return {"status": "success", "message": "Bot is online and waiting for Telegram data!"}

async def get_short_link(url):
    """Converts your TeraBox link to a monetized short link."""
    api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={url}"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(api_url)
            return r.json().get('shortened_url', url)
        except:
            return url

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        
        if update.message and update.message.text:
            chat_id = update.message.chat_id
            movie_name = update.message.text.strip().lower()

            # 1. Search Database first
            stored = await collection.find_one({"name": movie_name})
            if stored:
                await bot.send_message(chat_id=chat_id, text=f"✅ Found in my Database!\n{stored['short_link']}")
                return {"status": "ok"}

            # 2. Status message
            status = await bot.send_message(chat_id=chat_id, text=f"🔍 Searching for '{movie_name}' and saving to my account...")

            # 3. TeraBox Logic (Simplified for finished structure)
            # You can replace this with your scraper logic to find specific links
            found_terabox_link = "https://www.terabox.com/s/example_movie_link" 
            
            # 4. Shorten & Save to DB
            final_link = await get_short_link(found_terabox_link)
            await collection.insert_one({"name": movie_name, "short_link": final_link})

            await bot.edit_message_text(chat_id=chat_id, message_id=status.message_id, 
                                        text=f"🎬 Movie Ready!\n\nLink: {final_link}")
    except Exception as e:
        print(f"Error: {e}")

    return {"status": "ok"}
