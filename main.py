"""
main.py - FastAPI application untuk Moodle Activity API
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone
from typing import Optional

from config import APP_NAME, APP_VERSION, CORS_ORIGINS
from database import engine, get_db, Base
from models import Event
from schemas import EventCreate, EventResponse, EventBatch, StatsResponse

# ============================================================
# CREATE TABLES
# ============================================================
Base.metadata.create_all(bind=engine)

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API gateway untuk Moodle activity data",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "endpoints": [
            "GET  /health",
            "POST /api/activities",
            "POST /api/activities/batch",
            "GET  /api/activities/kafka-format/since/{last_id}",
            "GET  /api/stats",
            "GET  /api/events",
        ]
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Health check dengan verifikasi database."""
    try:
        count = db.query(func.count(Event.id)).scalar()
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected",
            "total_events": count,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "error",
            "error": str(e),
        }


@app.post("/api/activities", response_model=dict, status_code=201)
def post_activity(event: EventCreate, db: Session = Depends(get_db)):
    """Terima 1 event dari bot."""
    try:
        db_event = Event(
            sequence=event.sequence,
            user_hash=event.user_hash,
            courseid=event.courseid,
            component=event.component,
            eventname=event.eventname,
            action=event.action,
            target=event.target,
            timecreated=event.timecreated,
            event_time=event.event_time,
            bot_name=event.bot_name,
            source=event.source,
            ingested_at=event.ingested_at,
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        return {
            "status": "ok",
            "id": db_event.id,
            "total": db.query(func.count(Event.id)).scalar(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/activities/batch", status_code=201)
def post_activity_batch(batch: EventBatch, db: Session = Depends(get_db)):
    """Terima batch event."""
    try:
        db_events = []
        for event in batch.events:
            db_events.append(Event(
                sequence=event.sequence,
                user_hash=event.user_hash,
                courseid=event.courseid,
                component=event.component,
                eventname=event.eventname,
                action=event.action,
                target=event.target,
                timecreated=event.timecreated,
                event_time=event.event_time,
                bot_name=event.bot_name,
                source=event.source,
                ingested_at=event.ingested_at,
            ))
        db.add_all(db_events)
        db.commit()

        return {
            "status": "ok",
            "inserted": len(db_events),
            "total": db.query(func.count(Event.id)).scalar(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activities/kafka-format/since/{last_id}")
def get_kafka_format(
    last_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Ambil event dengan ID > last_id (untuk polling producer)."""
    events = (
        db.query(Event)
        .filter(Event.id > last_id)
        .order_by(Event.id.asc())
        .limit(limit)
        .all()
    )

    next_last_id = events[-1].id if events else last_id

    return {
        "last_id": last_id,
        "count": len(events),
        "next_last_id": next_last_id,
        "events": [e.to_dict() for e in events],
    }


@app.get("/api/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    """Statistik keseluruhan."""
    total = db.query(func.count(Event.id)).scalar()
    unique_users = db.query(func.count(func.distinct(Event.user_hash))).scalar()
    unique_courses = db.query(func.count(func.distinct(Event.courseid))).scalar()

    top_events = (
        db.query(Event.eventname, func.count(Event.id).label("count"))
        .group_by(Event.eventname)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    top_courses = (
        db.query(Event.courseid, func.count(Event.id).label("count"))
        .group_by(Event.courseid)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    return StatsResponse(
        total_events=total,
        unique_users=unique_users,
        unique_courses=unique_courses,
        top_events=[[e[0], e[1]] for e in top_events],
        top_courses=[[c[0], c[1]] for c in top_courses],
    )


@app.get("/api/events")
def list_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List event dengan paginasi."""
    events = (
        db.query(Event)
        .order_by(Event.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": db.query(func.count(Event.id)).scalar(),
        "offset": offset,
        "limit": limit,
        "count": len(events),
        "events": [e.to_dict() for e in events],
    }


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)