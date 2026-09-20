import requests
import random
import time
import uuid
from datetime import datetime

# ============== KONFIGURASI ==============
# GANTI INI setelah deploy: "https://api.domainanda.com"
BASE_URL = "http://127.0.0.1:8000"
JUMLAH_SISWA = 10
DURASI_DETIK = 120           # 2 menit → target ~1000+ events
JEDA_ANTAR_REQUEST = 0.05    # 20 events/detik

AKTIVITAS = [
    "login", "logout",
    "membaca_materi", "mengerjakan_kuis", "mengirim_tugas",
    "download_file", "menonton_video", "diskusi_forum"
]

DEVICES = ["desktop", "mobile", "tablet"]

# Metadata acak per jenis aktivitas
def generate_metadata(activity_type):
    if activity_type == "mengerjakan_kuis":
        return {
            "duration_seconds": random.randint(60, 600),
            "score": random.randint(50, 100),
            "page": "/kuis/matematika"
        }
    elif activity_type == "membaca_materi":
        return {
            "duration_seconds": random.randint(120, 1800),
            "page": f"/materi/bab-{random.randint(1, 10)}"
        }
    elif activity_type == "menonton_video":
        return {
            "duration_seconds": random.randint(60, 900),
            "video_id": f"vid_{random.randint(1, 50)}"
        }
    elif activity_type == "download_file":
        return {
            "file_name": f"materi_{random.randint(1, 20)}.pdf",
            "file_size_kb": random.randint(100, 5000)
        }
    else:
        return {"page": f"/{activity_type}"}


def register_siswa(username, password):
    try:
        r = requests.post(
            f"{BASE_URL}/api/register",
            json={"username": username, "password": password},
            timeout=5
        )
        if r.status_code == 200:
            print(f"[OK] Registrasi: {username}")
            return True
        elif r.status_code == 400:
            print(f"[--] {username} sudah ada")
            return True
        else:
            print(f"[XX] Gagal: {r.text}")
            return False
    except Exception as e:
        print(f"[XX] Error: {e}")
        return False


def kirim_aktivitas(username, activity_type, session_id):
    try:
        payload = {
            "username": username,
            "activity_type": activity_type,
            "session_id": session_id,
            "device": random.choice(DEVICES),
            "metadata": generate_metadata(activity_type)
        }
        r = requests.post(
            f"{BASE_URL}/api/activities",
            json=payload,
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] >> {username:10s} -> {activity_type:20s} (id: {data['id']})")
            return True
        else:
            print(f"[XX] Gagal: {r.text}")
            return False
    except Exception as e:
        print(f"[XX] Error: {e}")
        return False


def main():
    print("=" * 70)
    print("  BOT SIMULASI SISWA - Student Analytics (v2)")
    print("=" * 70)
    print(f"  Target API   : {BASE_URL}")
    print(f"  Jumlah Siswa : {JUMLAH_SISWA}")
    print(f"  Durasi       : {DURASI_DETIK} detik")
    print(f"  Rate Target  : {1/JEDA_ANTAR_REQUEST:.0f} events/detik")
    print("=" * 70)

    # FASE 1: Registrasi
    print("\nFASE 1: Registrasi Siswa")
    print("-" * 70)
    daftar_siswa = []
    for i in range(1, JUMLAH_SISWA + 1):
        username = f"siswa{i}"
        if register_siswa(username, "rahasia"):
            daftar_siswa.append(username)

    if not daftar_siswa:
        print("[XX] Tidak ada siswa. Keluar.")
        return

    # FASE 2: Simulasi
    print("\nFASE 2: Simulasi Aktivitas")
    print("-" * 70)
    print("Tekan Ctrl+C untuk berhenti\n")

    waktu_mulai = time.time()
    total = 0
    gagal = 0
    # Setiap siswa punya 1 session_id
    sesi_per_siswa = {s: f"sess_{str(uuid.uuid4())[:8]}" for s in daftar_siswa}

    try:
        while (time.time() - waktu_mulai) < DURASI_DETIK:
            siswa = random.choice(daftar_siswa)
            aktivitas = random.choice(AKTIVITAS)
            if kirim_aktivitas(siswa, aktivitas, sesi_per_siswa[siswa]):
                total += 1
            else:
                gagal += 1
            time.sleep(JEDA_ANTAR_REQUEST)
    except KeyboardInterrupt:
        print("\n[STOP] Dihentikan manual.")

    # Ringkasan
    durasi = time.time() - waktu_mulai
    print("\n" + "=" * 70)
    print("  RINGKASAN SIMULASI")
    print("=" * 70)
    print(f"  Siswa terdaftar       : {len(daftar_siswa)}")
    print(f"  Total aktivitas sukses: {total}")
    print(f"  Total gagal           : {gagal}")
    print(f"  Durasi aktual         : {durasi:.2f} detik")
    print(f"  Rata-rata             : {total/durasi:.2f} events/detik")
    print("=" * 70)


if __name__ == "__main__":
    main()