import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# --- YOUR CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"

@app.get("/")
def root():
    return {"status": "success", "message": "Bot is active!"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            # 1. Send "Searching" message immediately
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": f"🔍 Searching for '{text}'..."})

            # 2. Get Short Link
            dummy_link = "https://www.terabox.com/s/sample_link"
            api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={dummy_link}"
            
            res = requests.get(api_url).json()
            short_link = res.get('shortened_url', dummy_link)

            # 3. Send final link
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          json={"chat_id": chat_id, "text": f"🎬 Movie Found!\n\nLink: {short_link}"})
    except Exception as e:
        print(f"Error: {e}")

    return {"status": "ok"}
