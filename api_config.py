
# File ini hanya berisi konfigurasi yang berhubungan dengan API

# URL untuk endpoint API
API_URL = "https://intsys-research.telkomuniversity.ac.id/enose_api/object_detection"

# ID perangkat yang digunakan untuk identifikasi
DEVICE_ID = 'edge_1'

# Token otentikasi untuk akses API
API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwdWJsaWNfaWQiOiI5OTRlZmIxNi01N2Y3LTQwZmItYTgyZi1kYmFhNGZiYTUwODEiLCJleHAiOjE2NjA5NzIyNjF9.oKQl5BMeQq1RGsHvqG2ROBn0Qb3iYyNpphOGZpG0oKk"

# Header untuk request API
HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': DEVICE_ID,
    'x-access-token': API_TOKEN
}