from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
import random

from database import SessionLocal
from models import UserProfile, DailyLog
from utils.requirements import calculate_requirements

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

BOLIVIAN_FOODS = [
    {
        "name": "Quinoa", "calories": 120, "protein": 4.4, "carbs": 21.3, "fat": 1.9,
        "description": "Cereal andino rico en proteínas y fibra"
    },
    {
        "name": "Charque", "calories": 150, "protein": 30, "carbs": 0, "fat": 3.5,
        "description": "Carne deshidratada alta en proteínas"
    },
    {
        "name": "Chuño", "calories": 160, "protein": 1.9, "carbs": 38, "fat": 0.2,
        "description": "Papa deshidratada tradicional, rica en carbohidratos"
    },
    {
        "name": "Camote", "calories": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1,
        "description": "Tubérculo dulce con alto contenido de vitamina A"
    },
    {
        "name": "Tarwi", "calories": 150, "protein": 15.5, "carbs": 9.6, "fat": 7.2,
        "description": "Legumbre andina de alto valor proteico"
    },
    {
        "name": "Arroz con Queso", "calories": 190, "protein": 6, "carbs": 25, "fat": 7,
        "description": "Plato equilibrado con buen aporte de macronutrientes"
    },
    {
        "name": "Locro", "calories": 250, "protein": 12, "carbs": 28, "fat": 10,
        "description": "Sopa espesa tradicional con carne y maíz"
    },
    {
        "name": "Falso Conejo", "calories": 300, "protein": 18, "carbs": 30, "fat": 12,
        "description": "Plato típico con carne apanada y arroz"
    },
    {
        "name": "Majadito", "calories": 220, "protein": 10, "carbs": 35, "fat": 6,
        "description": "Arroz con charque típico del oriente boliviano"
    },
    {
        "name": "Sopa de Maní", "calories": 280, "protein": 9, "carbs": 15, "fat": 20,
        "description": "Sopa tradicional hecha con maní y carne"
    }
]

@router.get("/recommendations")
def get_recommendations(user: str = Query(...), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.name == user).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    requirements = calculate_requirements(
        age=profile.age,
        gender=profile.gender,
        weight=profile.weight,
        height=profile.height,
        activity_level=profile.activity_level
    )

    today = date.today()
    logs = db.query(DailyLog).filter(DailyLog.user == user, DailyLog.date == today).all()

    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for log in logs:
        total["calories"] += log.calories
        total["protein"] += log.protein
        total["carbs"] += log.carbs
        total["fat"] += log.fat

    deficit = {
        key: max(requirements[key] - total[key], 0)
        for key in total
    }

    scored = []
    for food in BOLIVIAN_FOODS:
        score = 0
        reason = []
        for key in ["protein", "carbs", "fat", "calories"]:
            if deficit[key] > 0:
                score += food[key] / (requirements[key] or 1)
                reason.append(key)
        if score > 0:
            scored.append({
                "name": food["name"],
                "description": food["description"],
                "macros": {
                    "calories": food["calories"],
                    "protein": food["protein"],
                    "carbs": food["carbs"],
                    "fat": food["fat"]
                },
                "reason": f"Buena fuente de {', '.join(reason)}",
                "score": score
            })

    top_six = sorted(scored, key=lambda x: x["score"], reverse=True)[:6]
    top = random.sample(top_six, min(3, len(top_six)))

    return {"user": user, "recommendations": top}
