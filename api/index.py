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

def is_subscribed(user_id):
    """Checks if the user joined @invvault."""
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    try:
        res = requests.get(url).json()
        status = res.get("result", {}).get("status", "")
        return status in ["member", "administrator", "creator"]
    except: return True

@app.get("/api/index")
async def root():
    return {"status": "success", "message": "Arnab's Bot is Live!"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_id = data["message"]["from"]["id"]
            text = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            # 1. Start Command
            if text == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Send me a movie name like 'KGF 2'!"})
                return {"status": "ok"}

            # 2. Check Channel Membership
            if not is_subscribed(user_id):
                requests.post(msg_url, json={
                    "chat_id": chat_id, 
                    "text": "⚠️ Access Denied! Join our channel first:\nhttps://t.me/invvault"
                })
                return {"status": "ok"}

            # 3. Search MongoDB Library
            existing = await collection.find_one({"name": text})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found!\n🔗 {existing['short_link']}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Movie not in library yet. Arnab will add it soon!"})
                
    except Exception as e: print(f"Error: {e}")
    return {"status": "ok"}
