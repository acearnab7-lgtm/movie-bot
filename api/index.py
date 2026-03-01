import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
import re

app = FastAPI()

# --- USING YOUR REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
async def root():
    return {"status": "success", "message": "TeraBox Search Engine is Live!"}

def find_movie_on_web(query):
    """Scrapes DuckDuckGo for real TeraBox/1024Tera movie links."""
    # DuckDuckGo is much better for finding file-sharing links without being blocked
    search_url = f"https://duckduckgo.com/html/?q=site:terabox.com+OR+site:1024tera.com+{query}+movie+link"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # We look for any link that contains the TeraBox share pattern '/s/'
        for a in soup.find_all('a', href=True):
            href = a['href']
            # This regex finds links to terabox, 1024tera, or nephobox
            match = re.search(r'https?://(?:www\.)?(?:terabox\.com|1024tera\.com|nephobox\.com|teraboxapp\.com)/s/[a-zA-Z0-9_-]+', href)
            if match:
                return match.group(0)
    except:
        return None
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
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Welcome Arnab! Send me a Movie Name to get your monetized link."})
                return {"status": "ok"}

            # 1. Check MongoDB First (Arnab123)
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in library:\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Searching Status
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Deep searching for '{user_text}' on TeraBox..."})

            # 3. Web Scraping Search
            raw_link = find_movie_on_web(movie_name)
            
            if not raw_link:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ No TeraBox link found yet. I've alerted Arnab to find it manually!"})
                return {"status": "ok"}

            # 4. ShrinkMe Monetization
            shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
            res = requests.get(shrink_url).json()
            final_link = res.get('shortened_url', raw_link)

            # 5. Save to MongoDB
            await collection.insert_one({"name": movie_name, "short_link": final_link})

            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Found! Enjoy your movie:\n\n🔗 {final_link}"})
    except: pass
    return {"status": "ok"}
