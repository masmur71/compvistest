import requests
import logging
import time
import os
from dotenv import load_dotenv

# Load variabel dari file .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")
NOTIFICATION_COOLDOWN = int(os.getenv("NOTIFICATION_COOLDOWN", 10))
DOSEN_MESSAGE = os.getenv("DOSEN_MESSAGE", "🔔 Dosen/staff terdeteksi.")
MAHASISWA_MESSAGE = os.getenv("MAHASISWA_MESSAGE", "📚 Mahasiswa terdeteksi.")

class TelegramNotifier:
    """
    Kelas untuk menangani notifikasi Telegram
    """
    
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_ids = CHAT_IDS
        self.cooldown = NOTIFICATION_COOLDOWN
        
        # Menyimpan waktu terakhir notifikasi dikirim untuk tiap jenis
        self.last_notification_time = {
            'dosen-staff': 0,
            'mahasiswa': 0
        }
        
        logging.info("TelegramNotifier diinisialisasi")
    
    def send_message(self, chat_id, message):
        """
        Mengirim pesan ke chat ID tertentu
        
        Args:
            chat_id (str): ID chat tujuan
            message (str): Pesan yang akan dikirim
        
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=payload)
            if response.ok:
                return True
            else:
                logging.error(f"Telegram API error: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Error mengirim pesan Telegram: {e}")
            return False
    
    def notify_detection(self, object_type, count=1, additional_info=''):
        """
        Mengirim notifikasi deteksi objek ke semua chat ID
        
        Args:
            object_type (str): Tipe objek yang terdeteksi ('dosen-staff' atau 'mahasiswa')
            count (int): Jumlah objek yang terdeteksi
            additional_info (str): Informasi tambahan untuk disertakan dalam pesan
        
        Returns:
            bool: True jika notifikasi berhasil dikirim, False jika cooldown aktif atau gagal
        """
        current_time = time.time()
        
        # Periksa cooldown untuk tipe objek ini
        if current_time - self.last_notification_time.get(object_type, 0) < self.cooldown:
            # Masih dalam masa cooldown, jangan kirim notifikasi
            return False
        
        # Pilih pesan berdasarkan tipe objek
        if object_type == 'dosen-staff':
            message = DOSEN_MESSAGE
        elif object_type == 'mahasiswa':
            message = MAHASISWA_MESSAGE
        else:
            message = f"🔔 PEMBERITAHUAN: {object_type} terdeteksi oleh sistem!"
        
        # Tambahkan jumlah jika lebih dari 1
        if count > 1:
            message += f"\nJumlah: {count}"
        
        # Tambahkan informasi tambahan jika ada
        if additional_info:
            message += f"\n{additional_info}"
        
        # Tambahkan waktu deteksi
        message += f"\nWaktu: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Kirim ke semua chat ID
        success = True
        for chat_id in self.chat_ids:
            if not self.send_message(chat_id, message):
                success = False
        
        # Update waktu notifikasi terakhir jika berhasil mengirim ke minimal satu chat
        if success:
            self.last_notification_time[object_type] = current_time
            logging.info(f"Notifikasi {object_type} berhasil dikirim")
        
        return success
