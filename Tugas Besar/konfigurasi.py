# konfigurasi.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NAMA_DB = 'diagnosis_hardware.db'
DB_PATH = os.path.join(BASE_DIR, NAMA_DB)

KATEGORI_PROBLEM = [
    "Performa (Lambat/Hang)", "Tampilan (Layar/Grafis)", "Jaringan (WiFi/LAN)",
    "Penyimpanan (HDD/SSD)", "Suhu (Overheating)", "Booting (Tidak Nyala/BSOD)",
    "Audio", "Peripheral (USB/Keyboard/Mouse)", "Power (Baterai/Charger)",
    "Lainnya"
]
KATEGORI_DEFAULT = "Lainnya"