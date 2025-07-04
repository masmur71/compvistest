# Konfigurasi Bot Telegram untuk sistem deteksi objek YOLO
# File ini berisi konfigurasi yang berhubungan dengan Bot Telegram

# Token Bot Telegram (dapatkan dari BotFather)
BOT_TOKEN = '7564699981:AAHU_jMSzUHF8VFcU2aWo40QJFWgvKZU2sI'

# ID Chat atau User yang akan menerima notifikasi
# Bisa berupa ID chat grup, channel, atau user individu
# Gunakan list jika ingin mengirim ke beberapa penerima
CHAT_IDS = ['1260785711']  # Ganti dengan ID chat yang sebenarnya

# Interval minimal antara notifikasi untuk mencegah spam (dalam detik)
# Jika ada deteksi berturut-turut dalam interval ini, hanya 1 notifikasi yang dikirim
NOTIFICATION_COOLDOWN = 10

# Template pesan notifikasi
DOSEN_MESSAGE = "🚨 PEMBERITAHUAN: Terdeteksi dosen/staff di area pemantauan! ({time})"
MAHASISWA_MESSAGE = "🚨 PEMBERITAHUAN: Terdeteksi mahasiswa di area pemantauan! ({time})"
