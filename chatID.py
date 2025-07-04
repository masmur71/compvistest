import requests

BOT_TOKEN = '7564699981:AAHU_jMSzUHF8VFcU2aWo40QJFWgvKZU2sI'
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










