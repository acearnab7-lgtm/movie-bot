import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- ARNAB'S REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
async def root():
    return {"status": "success", "message": "Arnab's Fully Automatic Engine is Live!"}

def auto_scrape_terabox(query):
    """Automatically finds TeraBox links on the web."""
    search_url = f"https://duckduckgo.com/lite/?q=site:terabox.com+OR+site:1024tera.com+{query}+movie"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            link = a['href']
            if 'terabox.com/s/' in link or '1024tera.com/s/' in link:
                return link
    except: return None
    return None

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            movie_name = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if movie_name == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Send me any movie name to get your link!"})
                return {"status": "ok"}

            # 1. CHECK DATABASE FIRST
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in Library!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. AUTO-SEARCH IF NOT FOUND
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching for '{movie_name}'..."})
            raw_link = auto_scrape_terabox(movie_name)
            
            if raw_link:
                # 3. AUTO-MONETIZE (ShrinkMe API)
                shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
                res = requests.get(shrink_url).json()
                final_link = res.get('shortened_url', raw_link)

                # 4. AUTO-SAVE TO MONGODB
                await collection.insert_one({"name": movie_name, "short_link": final_link})
                
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Done! Monetized link generated:\n🔗 {final_link}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Movie not found yet. Try another name!"})
    except: pass
    return {"status": "ok"}
