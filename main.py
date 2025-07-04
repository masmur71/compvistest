import os
import cv2
import time
import sys
import logging
import requests
import json
import pandas as pd
from datetime import datetime
from ultralytics import YOLO
import concurrent.futures
from dotenv import load_dotenv
# Import modul notifikasi Telegram
from telegram_handler import TelegramNotifier

load_dotenv()
API_URL =os.getenv("API_URL")
API_KEY = os.getenv("API_TOKEN")
USER_AGENT = os.getenv("DEVICE_ID")
HEADERS = {
        "Content-Type" : "application/json",
        "User-Agent": USER_AGENT,
        "x-access-token" : API_KEY }

# Setup logging
logging.basicConfig(
    filename='dual_yolo.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',  
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Konfigurasi Model dan Parameter
CUSTOM_MODEL_PATH = 'mahasiswaOrDosen(July)HPO1.onnx'
PRETRAINED_MODEL_PATH = 'yolov8n.onnx'
SAVE_INTERVAL = 10        # Interval pengiriman data ke API (detik)
DETECTION_INTERVAL = 1    # Interval deteksi (detik)

# Konfigurasi ByteTrack
TRACKER_CONFIG = {
    'tracker_type': 'bytetrack',
    'track_high_thresh': 0.5,    # Threshold tinggi untuk deteksi yang confident
    'track_low_thresh': 0.1,     # Threshold rendah untuk mempertahankan track
    'new_track_thresh': 0.6,     # Threshold untuk membuat track baru
    'track_buffer': 60,          # Buffer frames untuk mempertahankan track
    'match_thresh': 0.8,         # Threshold untuk matching antara deteksi dan track
    'min_box_area': 10,          # Area minimum bounding box
    'mom': 0.8                   # Momentum untuk update kalman filter
}

# Dictionary untuk menyimpan track terakhir dan data deteksi
last_tracks = {}
track_ages = {}  # Untuk melacak umur setiap track
counted_ids = set()
detection_records = []

# Fungsi untuk mengirim data ke API
def kirim_data_ke_api(detection_records):
    """
    Memproses catatan deteksi dan mengirimkannya ke API
    
    Args:
        detection_records: Daftar deteksi dengan key 'type' dan 'value'
        
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    try:
        # Menyiapkan DataFrame untuk API
        features = pd.DataFrame(columns=['type', 'value'])
        class_counts = {}
        
        # Menghitung jumlah kemunculan setiap kelas
        for record in detection_records:
            cls = record['type']
            class_counts[cls] = class_counts.get(cls, 0) + 1
            
        # Mengisi DataFrame dengan jumlah setiap kelas
        for cls, count in class_counts.items():
            new_row = pd.DataFrame({'type': [cls], 'value': [count]})
            features = pd.concat([features, new_row], ignore_index=True)
        
        # Konversi ke format yang diharapkan oleh API
        x_new = features.values.tolist()
        input_json = json.dumps({"data": x_new})
        
        # Mengirim data ke API
        response = requests.post(API_URL, data=input_json, headers=HEADERS)
        
        if response.ok:
            logging.info("Data berhasil dikirim ke API")
            return True
        else:
            logging.error(f"Kesalahan API {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Kesalahan saat mengirim data ke API: {e}")
        return False

# Fungsi untuk memperbarui umur track
def update_track_ages():
    """Update umur track dan hapus yang terlalu tua"""
    current_time = time.time()
    tracks_to_remove = []
    
    for track_id in track_ages:
        age = current_time - track_ages[track_id]
        if age > TRACKER_CONFIG['track_buffer']:
            tracks_to_remove.append(track_id)
    
    for track_id in tracks_to_remove:
        track_ages.pop(track_id)
        last_tracks.pop(track_id, None)

# Fungsi utama
def main():
    # Inisialisasi model
    try:
        custom_model = YOLO(CUSTOM_MODEL_PATH)
        pretrained_model = YOLO(PRETRAINED_MODEL_PATH)
        logging.info("Model berhasil dimuat.")
    except Exception as e:
        logging.error(f"Kesalahan saat memuat model: {e}")
        sys.exit(1)
        
    # Inisialisasi notifikasi Telegram
    try:
        telegram_notifier = TelegramNotifier()
        logging.info("Notifikasi Telegram berhasil diinisialisasi.")
    except Exception as e:
        logging.error(f"Kesalahan saat menginisialisasi Telegram: {e}")
        telegram_notifier = None

    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Tidak dapat mengakses webcam.")
        sys.exit(1)

    # Inisialisasi ThreadPoolExecutor
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    last_detection_time = time.time()
    last_save_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.error("Tidak dapat membaca frame dari webcam.")
                break

            current_time = time.time()

            if current_time - last_detection_time >= DETECTION_INTERVAL:
                try:
                    # 1. Deteksi dengan model custom (prioritas utama)
                    future_custom = executor.submit(
                        custom_model.track, 
                        frame,
                        tracker="bytetrack.yaml",
                        persist=True,
                        conf=TRACKER_CONFIG['track_high_thresh'],
                        iou=TRACKER_CONFIG['match_thresh']
                    )
                    custom_results = future_custom.result()
                    
                    dosen_count, mahasiswa_count = 0, 0
                    update_track_ages()
                    
                    for r in custom_results:
                        for box in r.boxes:
                            if box.id is None:
                                continue

                            coords = box.xyxy[0].tolist()
                            x1, y1, x2, y2 = map(int, coords)
                            cls = r.names[int(box.cls[0])]
                            conf = float(box.conf[0])
                            try:
                                track_id = int(box.id[0])
                            except TypeError:
                                track_id = int(box.id)
                            
                            # Hitung area bounding box
                            box_area = (x2 - x1) * (y2 - y1)
                            if box_area < TRACKER_CONFIG['min_box_area']:
                                continue

                            # Update atau tambah track baru
                            if conf >= TRACKER_CONFIG['new_track_thresh'] or track_id in last_tracks:
                                last_tracks[track_id] = {
                                    'coords': (x1, y1, x2, y2),
                                    'class': cls,
                                    'conf': conf
                                }
                                track_ages[track_id] = current_time

                            if cls == 'dosen-staff':
                                dosen_count += 1
                                color = (0, 255, 0)  # Hijau untuk dosen
                                
                                # Kirim notifikasi telegram saat dosen terdeteksi
                                unique_key = f"custom_{cls}_{track_id}"
                                if unique_key not in counted_ids and telegram_notifier:
                                    telegram_notifier.notify_detection('dosen-staff')
                                    
                            elif cls == 'mahasiswa':
                                mahasiswa_count += 1
                                color = (255, 0, 0)  # Merah untuk mahasiswa
                                
                                # Kirim notifikasi saat mahasiswa terdeteksi
                                unique_key = f"custom_{cls}_{track_id}"
                                if unique_key not in counted_ids and telegram_notifier:
                                    telegram_notifier.notify_detection('mahasiswa')
                            
                            unique_key = f"custom_{cls}_{track_id}"
                            if unique_key not in counted_ids:
                                counted_ids.add(unique_key)
                                detection_records.append({'type': cls, 'value': 1})
                            
                            # Gambar bounding box dan label dari model custom
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            label = f'{cls} ID:{track_id} Conf:{conf:.2f}'
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    # Gambar tracks yang disimpan tapi tidak terdeteksi di frame ini
                    custom_ids = [int(box.id[0]) for r in custom_results for box in r.boxes if box.id is not None]
                    for track_id, track_info in last_tracks.items():
                        if track_id not in custom_ids:
                            x1, y1, x2, y2 = track_info['coords']
                            cls = track_info['class']
                            color = (0, 255, 0) if cls == 'dosen-staff' else (255, 0, 0)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
                            label = f'{cls} ID:{track_id} (Saved)'
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    

                    # 2. Deteksi dengan model bawaan (pretrained) untuk objek selain "person"
                    try:
                        future_pretrained = executor.submit(
                            pretrained_model.track,
                            frame,
                            tracker="bytetrack.yaml",
                            persist=True,
                            conf=TRACKER_CONFIG['track_high_thresh'],
                            iou=TRACKER_CONFIG['match_thresh']
                            )
                        pretrained_results = future_pretrained.result()
                            
                        for r in pretrained_results:
                            for box in r.boxes:
                                cls_index = int(box.cls[0])
                                cls_name = r.names[cls_index]
                                # Lewati deteksi kelas "person"
                                if cls_name == "person":
                                    continue
                                conf = float(box.conf[0])
                                coords = box.xyxy[0].tolist()
                                x1, y1, x2, y2 = map(int, coords)
                                
                                
                                # Warna kuning untuk deteksi model pretrained
                                color = (0, 255, 255)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                label = f'{cls_name} (pretrained) Conf:{conf:.2f}'
                                cv2.putText(frame, label, (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                                
                                unique_key = f"pretrained_{cls_name}_{x1}_{y1}"
                                if unique_key not in counted_ids:
                                    counted_ids.add(unique_key)
                                    detection_records.append({'type': cls_name, 'value': 1})
                    except Exception as e:
                        logging.error(f"Kesalahan saat deteksi model pretrained: {e}")
                    
                    # Tampilkan informasi deteksi dari model custom
                    y_offset = 80
                    cv2.putText(frame, f'Mahasiswa: {mahasiswa_count}', (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    cv2.putText(frame, f'Dosen/Staff: {dosen_count}', (10, y_offset + 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    fps = int(1 / (time.time() - current_time))
                    cv2.putText(frame, f'FPS: {fps}', (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    
                    cv2.imshow('YOLO Detection', frame)
                    last_detection_time = current_time

                except Exception as e:
                    logging.error(f"Kesalahan saat tracking model: {e}")
                    continue

            # Kirim data ke API setiap SAVE_INTERVAL detik
            if current_time - last_save_time >= SAVE_INTERVAL:
                if detection_records:
                    success = kirim_data_ke_api(detection_records)
                    if success:
                        print("Data berhasil dikirim")
                    else:
                        print("Gagal mengirim data")
                    detection_records.clear()
                    counted_ids.clear()
                    last_save_time = current_time

            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Deteksi dihentikan oleh pengguna.")
                break

    except Exception as e:
        logging.error(f"Kesalahan tak terduga dalam loop utama: {e}")

    finally:
        executor.shutdown(wait=True)
        cap.release()
        cv2.destroyAllWindows()
        logging.info("Deteksi berakhir.")

if __name__ == "__main__":
    main()
