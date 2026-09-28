"""
bot_replay.py - Bot replay dataset Moodle ke FastAPI
Simulasi aktivitas mahasiswa dengan mengirim event dari dataset asli.
"""

import pandas as pd
import requests
import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import config
sys.path.append(str(Path(__file__).parent))
from config import CONFIG, validate_config, print_config


# ============================================================
# HELPER
# ============================================================
def check_api_health() -> bool:
    """Cek FastAPI online."""
    url = f"{CONFIG['api_base_url']}{CONFIG['endpoint_health']}"
    try:
        r = requests.get(url, timeout=CONFIG["request_timeout"])
        if r.status_code == 200:
            data = r.json()
            if CONFIG["verbose"]:
                print(f"[INFO] Health check OK: {data}")
            return True
        return False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Tidak dapat connect ke {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout saat health check")
        return False
    except Exception as e:
        print(f"[ERROR] Health check gagal: {e}")
        return False


def parse_event(row, sequence: int) -> dict:
    """Ubah baris CSV jadi payload JSON."""
    return {
        "sequence": sequence,
        "bot_name": CONFIG["bot_name"],
        "user_hash": row["user_hash"],
        "courseid": int(row["courseid"]),
        "component": row["component"],
        "eventname": row["eventname"],
        "action": row["action"],
        "target": row["target"],
        "timecreated": int(row["timecreated"]),
        "event_time": datetime.fromtimestamp(
            int(row["timecreated"]), tz=timezone.utc
        ).isoformat(),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source": "moodle-bot-replay",
    }


def send_event(payload: dict, retries: int = None) -> tuple:
    """
    Kirim 1 event ke FastAPI dengan retry.
    Return: (success: bool, status_code: int)
    """
    if retries is None:
        retries = CONFIG["max_retries"]
    
    url = f"{CONFIG['api_base_url']}{CONFIG['endpoint_post']}"
    
    for attempt in range(retries):
        try:
            r = requests.post(
                url,
                json=payload,
                timeout=CONFIG["request_timeout"],
                headers={
                    "Content-Type": "application/json",
                    "X-Bot-Name": CONFIG["bot_name"],
                },
            )
            if r.status_code in [200, 201]:
                return True, r.status_code
            else:
                if CONFIG["verbose"]:
                    print(f"[WARN] HTTP {r.status_code}: {r.text[:100]}")
                return False, r.status_code
        
        except requests.exceptions.ConnectionError:
            if attempt < retries - 1:
                if CONFIG["verbose"]:
                    print(f"[RETRY] Attempt {attempt+1}/{retries}...")
                time.sleep(CONFIG["retry_delay"])
            else:
                return False, 0
        
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(CONFIG["retry_delay"])
            else:
                return False, 0
        
        except Exception as e:
            print(f"[ERROR] {e}")
            return False, 0
    
    return False, 0


def send_batch(payloads: list, retries: int = None) -> tuple:
    """Kirim batch event."""
    if retries is None:
        retries = CONFIG["max_retries"]
    
    url = f"{CONFIG['api_base_url']}{CONFIG['endpoint_post']}/batch"
    
    for attempt in range(retries):
        try:
            r = requests.post(
                url,
                json={"events": payloads},
                timeout=CONFIG["request_timeout"],
                headers={"Content-Type": "application/json"},
            )
            if r.status_code in [200, 201]:
                return True, len(payloads)
        except Exception:
            if attempt < retries - 1:
                time.sleep(CONFIG["retry_delay"])
    
    return False, 0


# ============================================================
# MAIN
# ============================================================
def run():
    # Print config
    print_config()
    
    # Validasi
    errors = validate_config()
    if errors:
        print("[ERROR] Konfigurasi tidak valid:")
        for e in errors:
            print(f"  - {e}")
        return
    
    # Cek API
    print("[INFO] Cek FastAPI health...")
    if not check_api_health():
        print(f"\n[ERROR] FastAPI tidak dapat dihubungi di {CONFIG['api_base_url']}")
        print(f"[HINT] Pastikan:")
        print(f"  1. mock_api.py sudah jalan (untuk dev), atau")
        print(f"  2. FastAPI Railway sudah deploy")
        print(f"  3. API_BASE_URL di config.py sudah benar\n")
        return
    
    print("[INFO] FastAPI online ✓\n")
    
    # Load dataset
    csv_path = Path(CONFIG["csv_path"])
    print(f"[INFO] Membaca {csv_path.name}...")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Gagal baca CSV: {e}")
        return
    
    # Batasi record
    if CONFIG["max_records"]:
        df = df.head(CONFIG["max_records"])
    
    # Sort by timecreated
    df = df.sort_values("timecreated").reset_index(drop=True)
    total = len(df)
    
    # Info dataset
    t_min = datetime.fromtimestamp(df["timecreated"].min(), tz=timezone.utc)
    t_max = datetime.fromtimestamp(df["timecreated"].max(), tz=timezone.utc)
    
    print(f"[INFO] Total      : {total:,}")
    print(f"[INFO] Rentang    : {t_min} → {t_max}")
    print(f"[INFO] Mulai replay...\n")
    
    # Replay
    interval = 1.0 / CONFIG["events_per_second"]
    sent = 0
    failed = 0
    start_real = time.time()
    
    try:
        for idx, row in df.iterrows():
            payload = parse_event(row, sequence=idx + 1)
            
            if CONFIG["dry_run"]:
                ok, status = True, 200
            else:
                ok, status = send_event(payload)
            
            if ok:
                sent += 1
            else:
                failed += 1
            
            # Log progress
            if (idx + 1) % CONFIG["log_every"] == 0:
                elapsed = time.time() - start_real
                rate = sent / elapsed if elapsed > 0 else 0
                print(f"[{idx+1:>7,}/{total:,}] "
                      f"sent={sent:,} failed={failed} "
                      f"| {rate:5.1f} ev/s "
                      f"| {payload['eventname'][:40]}")
            
            # Rate limiting
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\n[STOP] Dihentikan user (Ctrl+C)")
    
    # Summary
    elapsed = time.time() - start_real
    print(f"\n{'='*70}")
    print(f"  REPLAY SELESAI")
    print(f"{'='*70}")
    print(f"  Total sent   : {sent:,}")
    print(f"  Total failed : {failed:,}")
    print(f"  Durasi       : {elapsed:.1f}s")
    print(f"  Rate         : {sent/elapsed:.1f} ev/s")
    print(f"  Success rate : {sent/(sent+failed)*100:.1f}%")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run()