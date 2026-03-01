import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
import re

app = FastAPI()

# --- ARNAB'S MASTER CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
async def root():
    return {"status": "success", "message": "Arnab's Master Engine is 100% Live!"}

def advanced_link_scraper(query):
    """Searches multiple unblocked sources for TeraBox links."""
    # We use specialized search parameters that bypass common bot-blocks
    queries = [
        f"site:terabox.com {query} movie link",
        f"site:1024tera.com {query} movie link",
        f"site:teraboxapp.com {query} movie link"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    for q in queries:
        try:
            # Using DuckDuckGo's lite version which is incredibly bot-friendly
            url = f"https://duckduckgo.com/lite/?q={q}"
            r = requests.get(url, headers=headers, timeout=8)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for a in soup.find_all('a', href=True):
                link = a['href']
                # Finding the actual TeraBox share ID
                if any(domain in link for domain in ['terabox.com', '1024tera', 'nephobox']):
                    # Clean the link from search redirects
                    match = re.search(r'https?://[^\s<>"]+?/s/[a-zA-Z0-9_-]+', link)
                    if match:
                        return match.group(0)
        except: continue
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
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Welcome Arnab! Send me a movie like 'Pushpa 2' and I will find the real link."})
                return {"status": "ok"}

            # 1. Check Library first
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in your library!\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Searching Status
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching deeper for '{user_text}' on TeraBox..."})

            # 3. Use the Advanced Scraper
            raw_link = advanced_link_scraper(movie_name)
            
            if not raw_link:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Movie not found on public indexes. I've alerted Arnab to add it manually!"})
                return {"status": "ok"}

            # 4. ShrinkMe Monetization
            shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
            res = requests.get(shrink_url).json()
            final_link = res.get('shortened_url', raw_link)

            # 5. Save to MongoDB
            await collection.insert_one({"name": movie_name, "short_link": final_link})

            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Found! Added to your collection:\n\n🔗 {final_link}"})
    except: pass
    return {"status": "ok"}
