import requests
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# --- YOUR REAL CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHRINKME_API = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9" 
MONGO_URL = "mongodb+srv://Arnab:Arnab123@cluster0.ya468bd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CHANNEL_ID = "@invvault"

client = AsyncIOMotorClient(MONGO_URL)
collection = client['movie_bot_db']['links']

def is_subscribed(user_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    try:
        res = requests.get(url).json()
        return res.get("result", {}).get("status", "") in ["member", "administrator", "creator"]
    except: return True

@app.get("/api/index")
async def root():
    return {"status": "success", "message": "Bot is Live!"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_id = data["message"]["from"]["id"]
            movie_name = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            if not is_subscribed(user_id):
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"⚠️ Join https://t.me/invvault to use this bot!"})
                return {"status": "ok"}

            # Search MongoDB
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ Found!\n🔗 {existing['short_link']}"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ Not in library. I've alerted Arnab!"})
    except: pass
    return {"status": "ok"}
