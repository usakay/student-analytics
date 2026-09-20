import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Kalau ada env var DATABASE_URL (production/Railway), pakai itu
# Kalau tidak, fallback ke SQLite (development lokal)
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./student_app.db"
)

# Railway/Heroku kasih URL dengan prefix "postgres://"
# SQLAlchemy butuh "postgresql://"
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

# SQLite butuh connect_args khusus
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()