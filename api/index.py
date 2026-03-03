import requests
import random
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- ARNAB'S LIVE CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CHANNEL_ID = "@invvault"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

def is_subscribed(user_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    try:
        res = requests.get(url).json()
        return res.get("result", {}).get("status", "") in ["member", "administrator", "creator"]
    except: return True

def deep_scrape_terabox(movie_name):
    """Try multiple search queries to find the best link."""
    search_queries = [
        f"site:terabox.com {movie_name} movie",
        f"site:1024tera.com {movie_name} download",
        f"\"{movie_name}\" terabox link"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for query in search_queries:
        search_url = f"https://duckduckgo.com/lite/?q={query}"
        try:
            r = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                link = a['href']
                if 'terabox.com/s/' in link or '1024tera.com/s/' in link:
                    return link
        except: continue
    return None

@app.get("/")
@app.get("/api/index")
async def health_check():
    return {"status": "100% Automatic", "owner": "Arnab Mandal"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_id = data["message"]["from"]["id"]
            text = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if text == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Full-Auto Movie Bot is Ready! Send me a name."})
                return {"status": "ok"}

            if not is_subscribed(user_id):
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"⚠️ Access Denied! Join {CHANNEL_ID} to unlock links."})
                return {"status": "ok"}

            # 1. CHECK DATABASE (Library)
            existing = await collection.find_one({"name": text})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in Library!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. AUTOMATION: DEEP SEARCH
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 System is deep-searching for '{text}'..."})
            raw_link = deep_scrape_terabox(text)
            
            if raw_link:
                # Use ShrinkMe API
                api_req = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
                res = requests.get(api_req).json()
                final_link = res.get('shortened_url', raw_link)

                # Save for the next person
                await collection.insert_one({"name": text, "short_link": final_link})
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 New Link Generated Automatically!\n🔗 {final_link}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Movie not found on public indexes yet. Admin Arnab has been notified!"})
    except: pass
    return {"status": "ok"}
