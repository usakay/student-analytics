from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime
import json

from . import models, schemas
from .database import engine, get_db


# Buat tabel di database saat aplikasi pertama kali jalan
models.Base.metadata.create_all(bind=engine)

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


app = FastAPI(
    title="Student Activity API",
    description="API untuk mencatat aktivitas siswa - Capstone Big Data",
    version="1.0.0"
)

# CORS: izinkan akses dari mana saja (nanti bisa dipersempit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti dengan domain spesifik untuk production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HELPER ====================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "Student Activity API - Capstone Big Data",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Endpoint untuk cek status server"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registrasi siswa baru"""
    # Cek apakah username sudah ada
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar")
    
    # Hash password sebelum disimpan
    new_user = models.User(
        username=user.username,
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Registrasi berhasil",
        "user_id": new_user.id,
        "username": new_user.username
    }


@app.post("/api/login")
def login(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    """Login siswa dan catat aktivitas login"""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    
    # Catat aktivitas login
    client_ip = request.client.host if request.client else None
    new_activity = models.Activity(
        user_id=db_user.id,
        activity_type="login",
        ip_address=client_ip,
        device=request.headers.get("user-agent", "unknown")[:100]
    )
    db.add(new_activity)
    db.commit()
    
    return {
        "message": "Login berhasil",
        "user_id": db_user.id,
        "username": db_user.username
    }


@app.post("/api/activities", response_model=schemas.ActivityResponse)
def create_activity(
    activity: schemas.ActivityCreate, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Catat aktivitas siswa (dipanggil oleh bot atau siswa asli)"""
    # Cari user
    db_user = db.query(models.User).filter(models.User.username == activity.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    # Auto-fill IP dan device kalau tidak ada
    client_ip = activity.ip_address or (request.client.host if request.client else None)
    device = activity.device or request.headers.get("user-agent", "unknown")[:100]
    
    # Simpan metadata sebagai JSON string
    metadata_str = json.dumps(activity.metadata) if activity.metadata else None
    
    new_activity = models.Activity(
        user_id=db_user.id,
        activity_type=activity.activity_type,
        session_id=activity.session_id,
        device=device,
        ip_address=client_ip,
        metadata_json=metadata_str
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    
    return new_activity


# ==================== ENDPOINTS UNTUK TIM LAIN ====================

@app.get("/api/activities/recent")
def get_recent_activities(limit: int = 100, db: Session = Depends(get_db)):
    """
    Ambil aktivitas terbaru (untuk tim lain / dashboard)
    Ini yang akan dipolling oleh Producer Kafka tim lain.
    """
    activities = db.query(models.Activity).order_by(
        models.Activity.id.desc()
    ).limit(limit).all()
    
    # Join dengan user untuk dapat username
    result = []
    for act in activities:
        result.append({
            "id": act.id,
            "user_id": act.user_id,
            "username": act.owner.username,
            "activity_type": act.activity_type,
            "timestamp": act.timestamp.isoformat(),
            "session_id": act.session_id,
            "device": act.device,
            "ip_address": act.ip_address,
            "metadata": json.loads(act.metadata_json) if act.metadata_json else None
        })
    
    return result


@app.get("/api/activities/since/{last_id}")
def get_activities_since(last_id: int, db: Session = Depends(get_db)):
    """
    Ambil aktivitas baru setelah ID tertentu.
    Ini yang akan dipolling terus-menerus oleh Producer Kafka tim lain.
    
    Contoh: GET /api/activities/since/50 → ambil semua aktivitas dengan id > 50
    """
    activities = db.query(models.Activity).filter(
        models.Activity.id > last_id
    ).order_by(models.Activity.id.asc()).limit(1000).all()
    
    result = []
    for act in activities:
        result.append({
            "id": act.id,
            "user_id": act.user_id,
            "username": act.owner.username,
            "activity_type": act.activity_type,
            "timestamp": act.timestamp.isoformat(),
            "session_id": act.session_id,
            "device": act.device,
            "ip_address": act.ip_address,
            "metadata": json.loads(act.metadata_json) if act.metadata_json else None
        })
    
    return result


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Statistik umum untuk dashboard"""
    total_users = db.query(models.User).count()
    total_activities = db.query(models.Activity).count()
    last_activity = db.query(models.Activity).order_by(
        models.Activity.id.desc()
    ).first()
    
    return {
        "total_users": total_users,
        "total_activities": total_activities,
        "last_activity_id": last_activity.id if last_activity else 0,
        "last_activity_time": last_activity.timestamp.isoformat() if last_activity else None
    }