"""
schemas.py - Pydantic schemas untuk validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EventCreate(BaseModel):
    """Schema untuk POST /api/activities."""
    sequence: Optional[int] = None
    bot_name: Optional[str] = None
    user_hash: str = Field(..., min_length=10)
    courseid: int
    component: Optional[str] = None
    eventname: str = Field(..., min_length=5)
    action: Optional[str] = None
    target: Optional[str] = None
    timecreated: int
    event_time: Optional[str] = None
    ingested_at: Optional[str] = None
    source: Optional[str] = "moodle-bot-replay"


class EventResponse(BaseModel):
    """Schema untuk response event."""
    id: int
    user_hash: str
    courseid: int
    eventname: str
    action: Optional[str] = None
    timecreated: int
    received_at: Optional[str] = None

    class Config:
        from_attributes = True


class EventBatch(BaseModel):
    """Schema untuk batch POST."""
    events: List[EventCreate]


class StatsResponse(BaseModel):
    """Schema untuk GET /api/stats."""
    total_events: int
    unique_users: int
    unique_courses: int
    top_events: List[List]
    top_courses: List[List]