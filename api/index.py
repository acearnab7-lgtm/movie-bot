import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- USING YOUR REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
async def root():
    return {"status": "success", "message": "Direct TeraBox Engine is Online!"}

def get_direct_terabox_link(query):
    """Searches for TeraBox files directly using an internal API call."""
    # We use a direct file-sharing search API that bypasses Google
    api_url = f"https://www.terabox.com/api/search?key={query}"
    headers = {"Cookie": f"ndus={NDUS}"}
    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        data = r.json()
        if data.get('list'):
            # Grabs the first direct link found in the search results
            shareid = data['list'][0]['shareid']
            uk = data['list'][0]['uk']
            return f"https://www.terabox.com/s/{shareid}"
    except:
        return None
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
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Welcome! Send a Movie Name to get a direct TeraBox link."})
                return {"status": "ok"}

            # 1. Check MongoDB First
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Direct Link Found:\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Direct TeraBox API Search
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching TeraBox for '{movie_name}'..."})
            raw_link = get_direct_terabox_link(movie_name)
            
            if not raw_link:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ No direct TeraBox file found for this name. Please check spelling."})
                return {"status": "ok"}

            # 3. ShrinkMe Monetization
            shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
            res = requests.get(shrink_url).json()
            final_link = res.get('shortened_url', raw_link)

            # 4. Save to MongoDB
            await collection.insert_one({"name": movie_name, "short_link": final_link})

            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Found! Added to your library:\n\n🔗 {final_link}"})
    except: pass
    return {"status": "ok"}
