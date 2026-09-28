"""
database.py - Koneksi SQLAlchemy ke PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# ============================================================
# ENGINE
# ============================================================
# Railway PostgreSQL butuh SSL, tapi SQLAlchemy handle otomatis
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # cek koneksi sebelum dipakai
    pool_recycle=300,        # recycle tiap 5 menit
    pool_size=5,
    max_overflow=10,
)

# ============================================================
# SESSION
# ============================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ============================================================
# BASE
# ============================================================
Base = declarative_base()


# ============================================================
# DEPENDENCY
# ============================================================
def get_db():
    """Dependency injection untuk database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()