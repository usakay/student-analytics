import requests
import random
import time
import uuid
import string
from datetime import datetime

# ============== KONFIGURASI ==============
BASE_URL = "https://api.nelson.csexadit24.academy"
JUMLAH_SISWA = 1000           # 1000 siswa
DURASI_DETIK = 3600           # 1 jam
JEDA_ANTAR_REQUEST = 0.01     # ~100 events/detik

AKTIVITAS = [
    "login", "logout",
    "membaca_materi", "mengerjakan_kuis", "mengirim_tugas",
    "download_file", "menonton_video", "diskusi_forum"
]

DEVICES = ["desktop", "mobile", "tablet"]


# ============== GENERATE NAMA ==============
FIRST_NAMES = [
    'Juvenal', 'Nelson', 'Raimunda', 'Rosalina', 'José', 'Teresa', 'António', 'Isabel',
    'Manuel', 'Francisca', 'Pedro', 'Cecília', 'Fernando', 'Rosa', 'Domingos', 'Olivia',
    'Luís', 'Marta', 'Hélio', 'Gracinda', 'Agostinho', 'Alexandre', 'Alfredo', 'Amélia',
    'Anacleto', 'André', 'Ângela', 'Antonieta', 'Armando', 'Augusto', 'Benedito', 'Bernardino',
    'Brigida', 'Caetano', 'Cândido', 'Carlos', 'Catarina', 'Celestino', 'Clemente', 'Cristina',
    'Damião', 'Daniel', 'Delfim', 'Diógenes', 'Domingas', 'Edgar', 'Edmundo', 'Elisabete',
    'Emanuel', 'Emília', 'Ermelinda', 'Euclides', 'Eugénio', 'Eusébio', 'Eva', 'Faustino',
    'Felícia', 'Feliciano', 'Fernanda', 'Fidélis', 'Filipe', 'Florindo', 'Francisco', 'Gabriel',
    'Georgina', 'Geraldo', 'Gertrudes', 'Gilberto', 'Gisela', 'Graciano', 'Guilherme', 'Helena',
    'Hermínio', 'Hilário', 'Ilda', 'Inácio', 'Irene', 'Isidoro', 'Iva', 'Jacinto', 'Januário',
    'Jerónimo', 'Joãozinho', 'Joaquina', 'Jonas', 'Jorge', 'Joselina', 'Júlio', 'Juvinal',
    'Laurinda', 'Leandro', 'Leonel', 'Liberdade', 'Lúcia', 'Ludovino', 'Luísa', 'Marcelino',
    'Margarida', 'Mário', 'Mariana', 'Mateus', 'Matilde', 'Maurício', 'Maximiano', 'Miguel',
    'Moisés', 'Natalino', 'Natércia', 'Nicolau', 'Norberto', 'Octávio', 'Odete', 'Olívia',
    'Osvaldo', 'Otília', 'Paulo', 'Paulina', 'Rafael', 'Raúl', 'Regina', 'Ricardo', 'Roberto',
    'Rodolfo', 'Romeu', 'Rui', 'Sabina', 'Salvador', 'Samuel', 'Sandra', 'Sebastião', 'Sérgio',
    'Silvano', 'Simão', 'Sofia', 'Suzana', 'Tarcísio', 'Telmo', 'Tomás', 'Valentim', 'Vasco',
    'Vera', 'Vicente', 'Vítor', 'Xavier', 'Zacarias', 'Zulmira'
]

LAST_NAMES = [
    'da Costa', 'Martins', 'Guterres', 'Belo', 'Ximenes', 'Alves', 'Babo', 'dos Reis',
    'Monteiro', 'de Jesus', 'Fernandes', 'Amaral', 'de Araújo', 'dos Santos', 'Soares',
    'Gama', 'da Silva', 'Pereira', 'do Rosário', 'Ribeiro', 'Barreto', 'Cardoso',
    'Carvalho', 'Correia', 'Dias', 'Duarte', 'Esteves', 'Faria', 'Figueiredo', 'Freitas',
    'Gomes', 'Gonçalves', 'Henriques', 'Leal', 'Lima', 'Lopes', 'Lourenço', 'Machado',
    'Magalhães', 'Marques', 'Matos', 'Mendes', 'Miranda', 'Moreira', 'Nascimento',
    'Neves', 'Nogueira', 'Nunes', 'Oliveira', 'Paiva', 'Pinto', 'Pires', 'Ramos',
    'Reis', 'Rocha', 'Rodrigues', 'Sampaio', 'Saraiva', 'Silveira', 'Simões', 'Teixeira',
    'Tavares', 'Vaz', 'Vieira'
]


def generate_students():
    """Generate 1000 siswa dengan nama unik"""
    students = []
    used_names = set()
    
    for i in range(1, JUMLAH_SISWA + 1):
        # Coba beberapa kali untuk dapat nama unik
        for attempt in range(10):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            
            if name not in used_names:
                used_names.add(name)
                break
        else:
            # Kalau gagal 10x, tambahkan angka di belakang
            name = f"{first} {last} {i}"
            used_names.add(name)
        
        students.append({
            "username": f"siswa{i}",
            "display_name": name,
            "password": "rahasia"
        })
    
    return students


# Generate daftar siswa
STUDENTS = generate_students()


# ============== METADATA GENERATOR ==============
def generate_metadata(activity_type):
    """Generate metadata acak per jenis aktivitas"""
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


# ============== REGISTRASI ==============
def register_siswa(username, display_name, password):
    """Daftarkan siswa baru ke aplikasi"""
    try:
        r = requests.post(
            f"{BASE_URL}/api/register",
            json={"username": username, "password": password},
            timeout=10
        )
        if r.status_code == 200:
            return True
        elif r.status_code == 400:
            # Sudah terdaftar
            return True
        else:
            return False
    except Exception as e:
        print(f"[XX] Register error {username}: {e}")
        return False


# ============== KIRIM AKTIVITAS ==============
def kirim_aktivitas(username, activity_type, session_id):
    """Kirim satu aktivitas ke API"""
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
            timeout=10
        )
        if r.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        return False


# ============== MAIN ==============
def main():
    print("=" * 70)
    print("  BOT SIMULASI SISWA - Student Analytics (v3 - 1000 Siswa)")
    print("=" * 70)
    print(f"  Target API   : {BASE_URL}")
    print(f"  Jumlah Siswa : {JUMLAH_SISWA}")
    print(f"  Durasi       : {DURASI_DETIK} detik ({DURASI_DETIK/60:.0f} menit)")
    print(f"  Rate Target  : {1/JEDA_ANTAR_REQUEST:.0f} events/detik")
    print("=" * 70)
    
    # FASE 1: Registrasi 1000 siswa
    print("\nFASE 1: Registrasi 1000 Siswa")
    print("-" * 70)
    print("Tunggu ya, ini butuh beberapa menit...\n")
    
    waktu_registrasi_mulai = time.time()
    berhasil_registrasi = 0
    gagal_registrasi = 0
    
    for i, siswa in enumerate(STUDENTS, 1):
        if register_siswa(siswa["username"], siswa["display_name"], siswa["password"]):
            berhasil_registrasi += 1
        else:
            gagal_registrasi += 1
        
        # Print progress setiap 100 siswa
        if i % 100 == 0:
            elapsed = time.time() - waktu_registrasi_mulai
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  [{i}/{JUMLAH_SISWA}] Registrasi... "
                  f"(berhasil: {berhasil_registrasi}, gagal: {gagal_registrasi}, "
                  f"rate: {rate:.1f}/detik)")
    
    durasi_registrasi = time.time() - waktu_registrasi_mulai
    print(f"\nRegistrasi selesai dalam {durasi_registrasi:.1f} detik")
    print(f"  Berhasil: {berhasil_registrasi}")
    print(f"  Gagal   : {gagal_registrasi}")
    
    # FASE 2: Simulasi aktivitas
    print("\nFASE 2: Simulasi Aktivitas")
    print("-" * 70)
    print("Tekan Ctrl+C untuk berhenti\n")
    
    waktu_mulai = time.time()
    total = 0
    gagal = 0
    counter_print = 0
    
    # Setiap siswa punya 1 session_id
    sesi_per_siswa = {s["username"]: f"sess_{str(uuid.uuid4())[:8]}" for s in STUDENTS}
    
    try:
        while (time.time() - waktu_mulai) < DURASI_DETIK:
            siswa = random.choice(STUDENTS)
            aktivitas = random.choice(AKTIVITAS)
            
            if kirim_aktivitas(siswa["username"], aktivitas, sesi_per_siswa[siswa["username"]]):
                total += 1
            else:
                gagal += 1
            
            counter_print += 1
            # Print progress setiap 1000 request
            if counter_print % 1000 == 0:
                elapsed = time.time() - waktu_mulai
                rate = total / elapsed if elapsed > 0 else 0
                print(f"  Total: {total} sukses, {gagal} gagal, "
                      f"rate: {rate:.1f}/detik, "
                      f"elapsed: {elapsed:.0f}s")
            
            time.sleep(JEDA_ANTAR_REQUEST)
    except KeyboardInterrupt:
        print("\n[STOP] Dihentikan manual.")
    
    # Ringkasan
    durasi = time.time() - waktu_mulai
    print("\n" + "=" * 70)
    print("  RINGKASAN SIMULASI")
    print("=" * 70)
    print(f"  Siswa terdaftar       : {berhasil_registrasi}")
    print(f"  Total aktivitas sukses: {total}")
    print(f"  Total gagal           : {gagal}")
    print(f"  Durasi aktual         : {durasi:.2f} detik")
    if durasi > 0:
        print(f"  Rata-rata             : {total/durasi:.2f} events/detik")
    print("=" * 70)


if __name__ == "__main__":
    main()