"""
config.py - Konfigurasi bot replay
"""

import os
from pathlib import Path

# ============================================================
# BASE PATH
# ============================================================
BASE_DIR = Path(__file__).parent.resolve()

# ============================================================
# KONFIGURASI BOT
# ============================================================
CONFIG = {
    # --------------------------------------------------------
    # TARGET API
    # --------------------------------------------------------
    # Development (lokal):
    #   "http://localhost:8000"          (mock_api.py)
    #   "http://127.0.0.1:8000"
    #
    # Production (Railway):
    #   "https://xxx.railway.app"        (FastAPI Railway)
    #
    # Bisa di-override via environment variable:
    #   set API_BASE_URL=https://xxx.railway.app
    # --------------------------------------------------------
    "api_base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
    
    # --------------------------------------------------------
    # ENDPOINT
    # --------------------------------------------------------
    "endpoint_post": "/api/activities",
    "endpoint_health": "/api/health",
    "endpoint_stats": "/api/stats",
    
    # --------------------------------------------------------
    # DATASET
    # --------------------------------------------------------
    "csv_path": str(BASE_DIR / "logs_interacoes_anon.csv"),
    
    # --------------------------------------------------------
    # RATE LIMITING
    # --------------------------------------------------------
    "events_per_second": 5,          # intensitas (5 event/detik)
    "max_records": 10000,            # None = semua (1 juta)
    
    # --------------------------------------------------------
    # BATCH
    # --------------------------------------------------------
    "batch_size": 1,                 # 1 = kirim per event
                                     # 100 = kirim per batch
    
    # --------------------------------------------------------
    # RETRY
    # --------------------------------------------------------
    "max_retries": 3,
    "retry_delay": 2,                # detik
    
    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------
    "request_timeout": 10,           # detik
    
    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------
    "log_every": 100,                # print tiap N event
    
    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------
    "dry_run": False,                # True = tidak kirim, hanya print
    "verbose": True,                 # print detail
    
    # --------------------------------------------------------
    # IDENTITAS BOT
    # --------------------------------------------------------
    "bot_name": "moodle-bot-replay",
    "bot_version": "1.0.0",
}


# ============================================================
# VALIDASI
# ============================================================
def validate_config():
    """Validasi konfigurasi sebelum dijalankan."""
    errors = []
    
    # Cek CSV ada
    csv_path = Path(CONFIG["csv_path"])
    if not csv_path.exists():
        errors.append(f"CSV tidak ditemukan: {csv_path}")
    
    # Cek rate
    if CONFIG["events_per_second"] <= 0:
        errors.append("events_per_second harus > 0")
    
    # Cek URL
    if not CONFIG["api_base_url"].startswith("http"):
        errors.append("api_base_url harus dimulai dengan http:// atau https://")
    
    return errors


# ============================================================
# PRINT CONFIG
# ============================================================
def print_config():
    """Print konfigurasi ke console."""
    print(f"\n{'='*70}")
    print(f"  BOT CONFIGURATION")
    print(f"{'='*70}")
    print(f"  Bot Name      : {CONFIG['bot_name']} v{CONFIG['bot_version']}")
    print(f"  Target API    : {CONFIG['api_base_url']}")
    print(f"  Endpoint      : {CONFIG['endpoint_post']}")
    print(f"  Dataset       : {CONFIG['csv_path']}")
    print(f"  Rate          : {CONFIG['events_per_second']} event/detik")
    print(f"  Max Records   : {CONFIG['max_records'] or 'ALL'}")
    print(f"  Batch Size    : {CONFIG['batch_size']}")
    print(f"  Dry Run       : {CONFIG['dry_run']}")
    print(f"  Timeout       : {CONFIG['request_timeout']}s")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    print_config()
    errors = validate_config()
    if errors:
        print("[ERROR] Konfigurasi tidak valid:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("[OK] Konfigurasi valid")