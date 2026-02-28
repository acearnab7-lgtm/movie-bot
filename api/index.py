import requests
import os
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- REAL CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Global Database Connection
client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
def root():
    return {"status": "success", "message": "Arnab's Master Engine is Live!"}

def search_terabox(query):
    """Real Scraper: Searches the web for live TeraBox movie links."""
    search_url = f"https://www.google.com/search?q=site:terabox.com+OR+site:nephobox.com+{query}+movie"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'terabox.com/s/' in href or 'nephobox.com/s/' in href:
                # Clean Google redirect links
                if '/url?q=' in href:
                    return href.split('/url?q=')[1].split('&')[0]
                return href
    except: return None
    return None

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"].get("text", "").strip().lower()
            api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if user_text == "/start":
                requests.post(api_url, json={"chat_id": chat_id, "text": "🎬 Welcome! Send me any Movie Name to get the monetized link."})
                return {"status": "ok"}

            # 1. Check Database (Instant result)
            existing = await collection.find_one({"name": user_text})
            if existing:
                requests.post(api_url, json={"chat_id": chat_id, "text": f"✅ Found in Library!\n\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Real Scrape (If not in DB)
            requests.post(api_url, json={"chat_id": chat_id, "text": f"🔎 Searching for '{user_text}'..."})
            raw_link = search_terabox(user_text)
            
            if not raw_link:
                requests.post(api_url, json={"chat_id": chat_id, "text": "❌ Movie not found yet. I'll alert the admin!"})
                return {"status": "ok"}

            # 3. Monetize via GPLinks
            shorten_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={raw_link}"
            res = requests.get(shorten_url).json()
            final_link = res.get('shortened_url', raw_link)

            # 4. Save to Database
            await collection.insert_one({"name": user_text, "short_link": final_link})

            requests.post(api_url, json={"chat_id": chat_id, "text": f"🎬 Movie Found!\n\n🔗 {final_link}"})
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}
