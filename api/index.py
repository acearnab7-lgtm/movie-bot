import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- ARNAB'S REAL CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CHANNEL_ID = "@invvault"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

@app.get("/")
@app.get("/api/index")
async def root():
    return {"status": "Stable", "owner": "Arnab Mandal"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if text == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Send a movie name! If I don't have it, I'll add it in 5 mins."})
                return {"status": "ok"}

            # Search your private MongoDB Library
            existing = await collection.find_one({"name": text})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found!\n🔗 {existing['short_link']}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Movie not in library yet. Arnab is fetching it from the main server now!"})
    except: pass
    return {"status": "ok"}
