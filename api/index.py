import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- ARNAB'S REAL CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CHANNEL_ID = "@invvault"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

def find_terabox_automatic(movie_name):
    """Deep-search for TeraBox links using dedicated file indexes."""
    # Using a specialized search query for better results
    search_url = f"https://duckduckgo.com/lite/?q=site:terabox.com+OR+site:1024tera.com+\"{movie_name}\"+movie"
    try:
        r = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if 'terabox.com/s/' in a['href'] or '1024tera.com/s/' in a['href']:
                return a['href']
    except: return None
    return None

@app.get("/")
@app.get("/api/index")
async def root():
    return {"status": "Automatic Engine Online", "owner": "Arnab Mandal"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if text == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Full-Auto Engine Ready! Send me a movie name."})
                return {"status": "ok"}

            # 1. Check MongoDB (Instant Response)
            existing = await collection.find_one({"name": text})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Automation: Find, Monetize, and Save
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching for '{text}'..."})
            raw_link = find_terabox_automatic(text)
            
            if raw_link:
                shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
                res = requests.get(shrink_url).json()
                final_link = res.get('shortened_url', raw_link)

                await collection.insert_one({"name": text, "short_link": final_link})
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 New Link Generated!\n🔗 {final_link}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Not found automatically yet. Try a different name!"})
    except: pass
    return {"status": "ok"}
