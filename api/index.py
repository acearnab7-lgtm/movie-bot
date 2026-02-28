import requests
from fastapi import FastAPI, Request

app = FastAPI()

# --- HARDCODED CREDENTIALS ---
TOKEN = "8714574641:AAFgvBUoWBqGp0SvFjPu5hOitAQMU54RJ-k"
SHORT_KEY = "282a7c2962630d599bf0f7b2a6ffa4cbc4623aa9"
NDUS = "ed09aba527e12d9a47bd18a689966a98e517f24060e74dc633ef5f2236aac3fcd01cd9aee2f5ecb0622cd152499be7cf2496954f8d4b19065c458f1c32e020c0f3335a1581bfe77a74142546951b011e1b459c870361be6d6d35629c190e809d62a20c0ea078396173f23ce35ccf7595"

@app.get("/")
def root():
    return {"status": "success", "message": "Movie Bot is 100% Online!"}

@app.post("/api/index")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"].get("text", "")

            # 1. Send immediate 'Processing' status
            msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(msg_url, json={
                "chat_id": chat_id, 
                "text": f"🎬 Searching for: {user_text}\nSaving to your TeraBox and generating link..."
            })

            # 2. TeraBox & Monetization Logic
            # Placeholder link until you add a specific search scraper
            original_link = "https://www.terabox.com/s/sample_link" 
            
            # Call GPLinks API to shorten
            short_url = f"https://gplinks.in/api?api={SHORT_KEY}&url={original_link}"
            res = requests.get(short_url).json()
            final_link = res.get('shortened_url', original_link)

            # 3. Send final link back to user
            requests.post(msg_url, json={
                "chat_id": chat_id, 
                "text": f"✅ Done! Here is your monetized link:\n\n{final_link}"
            })
    except Exception as e:
        print(f"Error: {e}")

    return {"status": "ok"}
