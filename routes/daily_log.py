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

class DailyLogRequest(BaseModel):
    user: str
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float



class DailyLogResponse(BaseModel):
    user: str
    date: str
    meals: list[dict]

@router.post("/daily-log")
def add_daily_log(entry: DailyLogRequest, db: Session = Depends(get_db)):
    today = date.today().isoformat()

    new_log = DailyLog(
        user=entry.user,
        date=today,
        food_name=entry.food_name,
        calories=entry.calories,
        protein=entry.protein,
        carbs=entry.carbs,
        fat=entry.fat
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return {"message": "Alimento guardado correctamente"}

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

@router.delete("/daily-log/reset")
def reset_daily_logs(db: Session = Depends(get_db)):
    try:
        db.execute("DROP TABLE IF EXISTS daily_logs CASCADE;")
        db.commit()
        return {"message": "Tabla 'daily_logs' eliminada correctamente."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
