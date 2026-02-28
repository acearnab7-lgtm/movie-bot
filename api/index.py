import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- USING YOUR REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize Database
client = AsyncIOMotorClient(MONGO_URL)
db = client['movie_bot_db']
collection = db['links']

@app.get("/")
def root():
    return {"status": "success", "message": "Arnab's Real Token Engine is Live!"}

def find_real_movie(query):
    """Scrapes the web for actual TeraBox links based on user request."""
    search_url = f"https://www.google.com/search?q=site:terabox.com+{query}+movie+link"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(search_url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            link = a['href']
            if 'terabox.com/s/' in link:
                # Cleaning the link from Google's redirect format
                return link.split('?q=')[1].split('&')[0] if '?q=' in link else link
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

            # 1. Check MongoDB (Don't waste API calls if we already have it)
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in Library:\n{existing['short_link']}"})
                return {"status": "ok"}

            # 2. Real Web Search
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching the web for '{movie_name}'..."})
            raw_link = find_real_movie(movie_name)
            
            if not raw_link:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Sorry, I couldn't find a direct link for that movie yet."})
                return {"status": "ok"}

            # 3. Shorten with your Real GPLinks Key
            api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={raw_link}"
            res = requests.get(api_url).json()
            short_link = res.get('shortened_url', raw_link)

            # 4. Save to your Real MongoDB
            await collection.insert_one({"name": movie_name, "short_link": short_link})

            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Movie Found & Monetized!\n\nLink: {short_link}"})
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}
