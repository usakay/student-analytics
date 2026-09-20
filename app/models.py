from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Ganti dari 'password'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    activities = relationship("Activity", back_populates="owner")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Field tambahan untuk enrichment (untuk tim lain)
    session_id = Column(String, nullable=True)
    device = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)  # Simpan sebagai JSON string

    owner = relationship("User", back_populates="activities")