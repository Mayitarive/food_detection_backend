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
    },
    {
        "name": "Huevo", "calories": 155, "protein": 13, "carbs": 1.1, "fat": 11,
        "description": "Fuente excelente de proteína de alta calidad y grasas saludables"
    },
    {
        "name": "Palta", "calories": 160, "protein": 2, "carbs": 8.5, "fat": 14.7,
        "description": "Fruta rica en grasas saludables y fibra"
    },
    {
        "name": "Tunta", "calories": 140, "protein": 2.0, "carbs": 32, "fat": 0.2,
        "description": "Papa blanca deshidratada típica de los Andes, rica en carbohidratos"
    },
    {
        "name": "Pepino", "calories": 15, "protein": 0.7, "carbs": 3.6, "fat": 0.1,
        "description": "Vegetal fresco, bajo en calorías, rico en agua y fibra"
    },
    {
        "name": "Plátano", "calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3,
        "description": "Fruta rica en carbohidratos y potasio, ideal para energía rápida"
    },
    {
        "name": "Manzana", "calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2,
        "description": "Fruta refrescante, rica en fibra y baja en calorías"
    },
    {
        "name": "Frutillas", "calories": 32, "protein": 0.7, "carbs": 7.7, "fat": 0.3,
        "description": "Fruta rica en antioxidantes, vitamina C y fibra"
    },
    {
        "name": "Naranja", "calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1,
        "description": "Fruta cítrica rica en vitamina C y carbohidratos simples"
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

    # 🔥 Cambio aquí para que las recomendaciones sean más variadas
    if len(scored) <= 3:
        top = scored
    else:
        top = random.sample(scored, 3)

    return {"user": user, "recommendations": top}
