import requests
import os
from dotenv import load_dotenv

BOT_TOKEN = os.getenv("BOT_TOKEN")
URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

# Simpan chat_id yang sudah dikumpulkan
collected_ids = set()

response = requests.get(URL)
data = response.json()

for result in data['result']:
    message = result.get('message')
    if message:
        chat_id = message['chat']['id']
        if chat_id not in collected_ids:
            print(f"Chat ID Baru: {chat_id}")
            collected_ids.add(chat_id)
            # Simpan ke file atau database










