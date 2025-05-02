from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from database import SessionLocal
from models import DailyLog
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DailyLogResponse(BaseModel):
    user: str
    date: str
    meals: list[dict]

@router.get("/daily-log", response_model=DailyLogResponse)
def get_daily_log(user: str = Query(...), db: Session = Depends(get_db)):
    today = date.today().isoformat()

    logs = db.query(DailyLog).filter(DailyLog.user == user, DailyLog.date == today).all()
    meals = [
        {
            "name": log.food_name,
            "calories": log.calories,
            "protein": log.protein,
            "carbs": log.carbs,
            "fat": log.fat,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in logs
    ]

    return {
        "user": user,
        "date": today,
        "meals": meals
    }
