import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- ARNAB'S REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

def find_movie_on_terabox(query):
    """Reliable way to find TeraBox links via specialized file searchers."""
    # Using a specialized indexer that doesn't block bots
    api_url = f"https://terabox-search-api.vercel.app/search?q={query}"
    try:
        results = requests.get(api_url, timeout=10).json()
        if results.get("links"):
            return results["links"][0] # Return the first working link found
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
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Send me any movie name!"})
                return {"status": "ok"}

            # 1. DATABASE CHECK (The most reliable way)
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in Library!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. AUTO-SEARCH
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Deep searching for '{movie_name}'..."})
            raw_link = find_movie_on_terabox(movie_name)
            
            if raw_link:
                # 3. AUTO-MONETIZE
                shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
                res = requests.get(shrink_url).json()
                final_link = res.get('shortened_url', raw_link)

                # 4. AUTO-SAVE
                await collection.insert_one({"name": movie_name, "short_link": final_link})
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Link Generated!\n🔗 {final_link}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Still not found automatically. Please wait for the admin to add it manually!"})
    except: pass
    return {"status": "ok"}
