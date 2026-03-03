import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- YOUR REAL CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CHANNEL_ID = "@invvault"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

def auto_search_terabox(movie_name):
    """Deep-Scraper: Tries multiple queries to bypass blocks."""
    queries = [
        f"site:terabox.com {movie_name} movie",
        f"site:1024tera.com {movie_name} download",
        f"\"{movie_name}\" terabox share link"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for q in queries:
        try:
            url = f"https://duckduckgo.com/lite/?q={q}"
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if 'terabox.com/s/' in a['href'] or '1024tera.com/s/' in a['href']:
                    return a['href']
        except: continue
    return None

@app.get("/")
@app.get("/api/index")
async def health_check():
    return {"status": "100% Automatic", "owner": "Arnab"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if text == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Automation Online! Send any movie name."})
                return {"status": "ok"}

            # 1. Check Database (Instant Library)
            existing = await collection.find_one({"name": text})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Automation: Scrape, Monetize, and Save
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching and monetizing '{text}'..."})
            raw_link = auto_search_terabox(text)
            
            if raw_link:
                shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
                res = requests.get(shrink_url).json()
                final_link = res.get('shortened_url', raw_link)

                # Save for the next person
                await collection.insert_one({"name": text, "short_link": final_link})
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Done! Link Generated:\n🔗 {final_link}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Not found automatically yet. Admin Arnab alerted!"})
    except: pass
    return {"status": "ok"}
