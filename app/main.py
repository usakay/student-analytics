from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import json
import bcrypt

from . import models, schemas
from .database import engine, get_db


# Buat tabel di database saat aplikasi pertama kali jalan
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Student Activity API",
    description="API untuk mencatat aktivitas siswa - Capstone Big Data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HELPER ====================

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        password_bytes = plain.encode('utf-8')[:72]
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar")
    
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
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    
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
    db_user = db.query(models.User).filter(models.User.username == activity.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    client_ip = activity.ip_address or (request.client.host if request.client else None)
    device = activity.device or request.headers.get("user-agent", "unknown")[:100]
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


@app.get("/api/activities/recent")
def get_recent_activities(limit: int = 100, db: Session = Depends(get_db)):
    activities = db.query(models.Activity).order_by(
        models.Activity.id.desc()
    ).limit(limit).all()
    
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