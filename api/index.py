import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup

app = FastAPI()

# --- USING YOUR REAL TOKENS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize Database
client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
def root():
    return {"status": "success", "message": "Arnab's Master Engine is Live!"}

def find_movie_on_web(query):
    """Scrapes Google for actual TeraBox links."""
    search_url = f"https://www.google.com/search?q=site:terabox.com+OR+site:nephobox.com+{query}+movie+link"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            link = a['href']
            if 'terabox.com/s/' in link or 'nephobox.com/s/' in link:
                return link.split('?q=')[1].split('&')[0] if '?q=' in link else link
    except: return None
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
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Send me a Movie Name to get your link!"})
                return {"status": "ok"}

            # 1. Check MongoDB (Instant Response)
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found in Library!\n\n🔗 {existing['short_link']}"})
                return {"status": "ok"}

            # 2. Status Update
            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🔎 Searching for '{user_text}'..."})

            # 3. Real Web Search
            raw_link = find_movie_on_web(movie_name)
            
            if not raw_link:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Movie not found yet. Try another name!"})
                return {"status": "ok"}

            # 4. Monetize with ShrinkMe.io
            shrink_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={raw_link}"
            res = requests.get(shrink_url).json()
            final_link = res.get('shortened_url', raw_link)

            # 5. Save to MongoDB
            await collection.insert_one({"name": movie_name, "short_link": final_link})

            requests.post(msg_url, json={"chat_id": chat_id, "text": f"🎬 Found!\n\n🔗 {final_link}"})
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}
