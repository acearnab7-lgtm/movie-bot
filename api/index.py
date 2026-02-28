import requests
import os
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- HARDCODED CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize DB
client = AsyncIOMotorClient(MONGO_URL)
db = client['movie_bot_db']
collection = db['links']

@app.get("/")
def root():
    return {"status": "success", "message": "Master Engine Live!"}

def search_scraper(query):
    """Searches a public TeraBox index for the movie."""
    # Using a common search parameter for shared terabox links
    search_url = f"https://www.google.com/search?q=site:terabox.com+OR+site:nephobox.com+{query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Simple logic to find the first terabox link in Google results
        for link in soup.find_all('a'):
            href = link.get('href')
            if 'terabox.com/s/' in href:
                # Clean the Google redirect link
                return href.split('?q=')[1].split('&')[0]
    except:
        return None
    return None

@app.post("/api/index")
async def handle_webhook(request: Request):
    data = await request.json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        movie_name = data["message"].get("text", "").strip().lower()

        # 1. Database Check
        existing = await collection.find_one({"name": movie_name})
        if existing:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": f"✅ Already in library:\n{existing['short_link']}"})
            return {"status": "ok"}

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": chat_id, "text": f"🔎 Searching for '{movie_name}'..."})

        # 2. Real Scraper Search
        real_link = search_scraper(movie_name)
        
        if not real_link:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": "❌ Sorry, I couldn't find that movie yet."})
            return {"status": "ok"}

        # 3. Monetize with GPLinks
        api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={real_link}"
        short_link = requests.get(api_url).json().get('shortened_url', real_link)

        # 4. Save to MongoDB
        await collection.insert_one({"name": movie_name, "short_link": short_link})

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": chat_id, "text": f"🎬 Found! Enjoy your movie:\n\n{short_link}"})

    return {"status": "ok"}
