from pydantic import BaseModel
from typing import List
from datetime import date

class DailyFoodItem(BaseModel):
    name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    timestamp: str

class DailyLogResponse(BaseModel):
    user: str
    date: date
    meals: List[DailyFoodItem]
