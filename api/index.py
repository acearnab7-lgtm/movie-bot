import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- ARNAB'S REAL CREDENTIALS ---
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

def auto_scrape(query):
    """Automatic searcher for TeraBox links."""
    search_url = f"https://duckduckgo.com/lite/?q=site:terabox.com+OR+site:1024tera.com+{query}+movie"
    try:
        r = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if 'terabox.com/s/' in a['href'] or '1024tera.com/s/' in a['href']:
                return a['href']
    except: return None

@app.get("/")
@app.get("/api/index")
async def root():
    return {"status": "online", "message": "Automation Engine is Ready!"}

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
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Send any movie name for an instant link!"})
                return {"status": "ok"}

            if not is_subscribed(user_id):
                requests.post(msg_url, json={"chat_id": chat_id, "text": "⚠️ Join @invvault to use this bot!"})
                return {"status": "ok"}

            # 1. Check MongoDB
            existing = await collection.find_one({"name": text})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Automation: Scrape, Shorten, Save
            requests.post(msg_url, json={"chat_id": chat_id, "text": "🔎 Searching..."})
            raw_link = auto_scrape(text)
            if raw_link:
                shrink_res = requests.get(f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}").json()
                final_link = shrink_res.get('shortened_url', raw_link)
                await collection.insert_one({"name": text, "short_link": final_link})
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Link Generated!\n🔗 {final_link}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Not found. Arnab has been alerted!"})
    except: pass
    return {"status": "ok"}
