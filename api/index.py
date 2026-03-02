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
    """Checks if the user is a member of @invvault."""
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    try:
        response = requests.get(url).json()
        status = response.get("result", {}).get("status", "")
        return status in ["member", "administrator", "creator"]
    except:
        return True 

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_id = data["message"]["from"]["id"]
            movie_name = data["message"].get("text", "").strip().lower()
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            # 1. THE GATEKEEPER: FORCE JOIN CHANNEL
            if not is_subscribed(user_id):
                join_msg = f"⚠️ **Access Denied!**\n\nTo get movies, you must join our official channel:\n👉 https://t.me/invvault\n\nAfter joining, come back and type the movie name!"
                requests.post(msg_url, json={"chat_id": chat_id, "text": join_msg, "parse_mode": "Markdown"})
                return {"status": "ok"}

            if movie_name == "/start":
                requests.post(msg_url, json={"chat_id": chat_id, "text": "🎬 Welcome! Send me a movie name (like 'KGF 2') to get your link."})
                return {"status": "ok"}

            # 2. THE LIBRARY: SEARCH MONGODB
            existing = await collection.find_one({"name": movie_name})
            if existing:
                requests.post(msg_url, json={"chat_id": chat_id, "text": f"✅ **Movie Found!**\n\n🔗 {existing['short_link']}", "parse_mode": "Markdown"})
            else:
                requests.post(msg_url, json={"chat_id": chat_id, "text": "❌ This movie isn't in my library yet. I've alerted Arnab to add it!"})
    except: pass
    return {"status": "ok"}
