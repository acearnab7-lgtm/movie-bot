import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# --- HARDCODED CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"

@app.get("/")
def root():
    return {"status": "success", "message": "Bot is active!"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    data = await request.json()
    
    # Check if this is a message
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # 1. Send the "Searching" status immediately
        search_text = f"🔍 Searching for '{text}'..."
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": chat_id, "text": search_text})

        # 2. Get the Shortener link
        # Placeholder link for now
        dummy_link = "https://www.terabox.com/s/sample_link"
        api_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={dummy_link}"
        
        try:
            res = requests.get(api_url).json()
            short_link = res.get('shortened_url', dummy_link)
        except:
            short_link = dummy_link

        # 3. Send the final movie link
        final_text = f"🎬 Movie Found!\n\nLink: {short_link}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": chat_id, "text": final_text})

    return {"status": "ok"}
