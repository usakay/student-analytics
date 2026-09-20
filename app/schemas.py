from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityCreate(BaseModel):
    username: str
    activity_type: str
    session_id: Optional[str] = None
    device: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Optional[dict] = None


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    timestamp: datetime
    session_id: Optional[str] = None
    device: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True