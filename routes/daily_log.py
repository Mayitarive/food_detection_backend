from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import DailyLog
from schemas.daily_log import DailyLogResponse, DailyFoodItem

router = APIRouter()

@router.get("/daily-log", response_model=DailyLogResponse)
def get_daily_log(user: str = Query(...), db: Session = Depends(get_db)):
    today = datetime.utcnow().date()

    logs = db.query(DailyLog).filter(
        DailyLog.user == user,
        DailyLog.timestamp >= datetime.combine(today, datetime.min.time()),
        DailyLog.timestamp <= datetime.combine(today, datetime.max.time())
    ).all()

    meals = [
        DailyFoodItem(
            name=log.food_name,
            calories=log.calories,
            protein=log.protein,
            carbs=log.carbs,
            fat=log.fat,
            timestamp=str(log.timestamp)
        )
        for log in logs
    ]

    return DailyLogResponse(user=user, date=today, meals=meals)
