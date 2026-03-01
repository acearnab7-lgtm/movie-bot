import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
import re

app = FastAPI()

# --- YOUR REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

def hybrid_terabox_search(query):
    """Searches public TeraBox indexes when the direct API fails."""
    # Source 1: DuckDuckGo (Better than Google for finding file links)
    search_url = f"https://duckduckgo.com/html/?q=site:terabox.com+OR+site:1024tera.com+{query}+movie"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for links containing the TeraBox share pattern '/s/'
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Match standard TeraBox short links
            match = re.search(r'https?://(?:www\.)?(?:terabox\.com|1024tera\.com|nephobox\.com|teraboxapp\.com)/s/[a-zA-Z0-9_-]+', href)
            if match:
                return match.group(0)
    except Exception as e:
        print(f"Scrape Error: {e}")
    
    return None

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"].get("text", "").strip()
            movie_name = user_text.lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if movie_name == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Welcome! Send me a Movie Name to get your monetized TeraBox link."})
                return {"status": "ok"}

            # 1. Check MongoDB first (Arnab123)
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in library:\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Start Search
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching for '{user_text}' on TeraBox..."})
            
            # 3. Use Hybrid Search (Direct API + Public Scraping)
            found_link = hybrid_terabox_search(movie_name)
            
            if not found_link:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ No direct TeraBox file found. Try a different name or be more specific."})
                return {"status": "ok"}

            # 4. Monetize with ShrinkMe.io
            shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={found_link}"
            res = requests.get(shrink_url).json()
            final_link = res.get('shortened_url', found_link)

            # 5. Save to MongoDB
            await collection.insert_one({"name": movie_name, "short_link": final_link})

            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Found! Added to your collection:\n\n🔗 {final_link}"})
    except: pass
    return {"status": "ok"}
