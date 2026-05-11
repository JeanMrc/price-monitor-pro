import os
from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN   = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": "Price Monitor Bot is online!"}

r = requests.post(url, data=payload)
print(r.json())