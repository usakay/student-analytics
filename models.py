"""
models.py - SQLAlchemy models untuk PostgreSQL
"""

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base


class Event(Base):
    """Tabel events - menyimpan log interaksi Moodle."""
    __tablename__ = "events"

    # Primary key auto-increment (untuk polling)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Data event
    sequence = Column(BigInteger, nullable=True)
    user_hash = Column(String(64), nullable=False, index=True)
    courseid = Column(Integer, nullable=False, index=True)
    component = Column(String(100), nullable=True)
    eventname = Column(String(200), nullable=False, index=True)
    action = Column(String(50), nullable=True)
    target = Column(String(50), nullable=True)
    timecreated = Column(BigInteger, nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    bot_name = Column(String(50), nullable=True)
    source = Column(String(50), nullable=True)
    ingested_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp server
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    received_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def to_dict(self):
        """Convert ke dict untuk JSON response."""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "user_hash": self.user_hash,
            "courseid": self.courseid,
            "component": self.component,
            "eventname": self.eventname,
            "action": self.action,
            "target": self.target,
            "timecreated": self.timecreated,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "bot_name": self.bot_name,
            "source": self.source,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }