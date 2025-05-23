from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.orm import Session
from database import Base, engine
from dependencies import get_db
from models import DailyLog, UserProfile
from routes.daily_log import router as daily_log_router
from routes.profile import router as profile_router
from routes.recommendations import router as recommendations_router
from utils.requirements import calculate_requirements
from schemas.user_profile import (
    UserProfileCreate,
    UserProfileResponse,
    NutritionalRequirements
)

import shutil
import uuid
from pathlib import Path
from ultralytics import YOLO
from food_macros import FOOD_MACROS

# ✅ IMPORTANTE: Añadir ProxyHeadersMiddleware para detectar correctamente HTTPS detrás de proxy (Railway)
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

app = FastAPI()

# ✅ Middleware para respetar X-Forwarded-Proto y evitar redirect http -> https
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# ✅ Servir archivos estáticos
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Inicializar la base de datos
Base.metadata.create_all(bind=engine)

# ✅ Cargar modelo YOLOv8
model_path = "yolo_model/best.pt"
model = YOLO(model_path)
print("✅ Modelo YOLOv8 cargado")

# ✅ Endpoint para detección de alimentos con bounding boxes
@app.post("/detect/")
async def detect_food(file: UploadFile = File(...)):
    try:
        image_id = str(uuid.uuid4())
        input_path = f"static/{image_id}.jpg"
        output_path = f"static/{image_id}_pred.jpg"
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        results = model(input_path)
        results[0].save(filename=output_path)

        names = model.names
        detected = set([names[int(cls)] for cls in results[0].boxes.cls.cpu().numpy()])

        detections = []
        for food in detected:
            macros = FOOD_MACROS.get(food.lower(), {
                "unit": "unidad",
                "proteins": "No disponible",
                "carbs": "No disponible",
                "fats": "No disponible",
                "kcal": "No disponible"
            })
            detections.append({
                "food": food,
                "unit": macros["unit"],
                "macronutrients": {
                    "proteins": macros["proteins"],
                    "carbs": macros["carbs"],
                    "fats": macros["fats"],
                    "kcal": macros["kcal"]
                }
            })

        return JSONResponse(content={
            "image_path": output_path,
            "detections": detections
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ✅ Endpoint para servir imagen procesada
@app.get("/image/{filename}")
async def get_image(filename: str):
    path = Path("static") / filename
    if path.exists():
        return FileResponse(path)
    return JSONResponse(status_code=404, content={"error": "Imagen no encontrada"})

# ✅ Crear o actualizar perfil de usuario
@app.post("/profile/", response_model=UserProfileResponse)
def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    try:
        db_profile = db.query(UserProfile).filter(UserProfile.name == profile.name).first()

        requirements = calculate_requirements(
            age=profile.age,
            gender=profile.gender,
            weight=profile.weight,
            height=profile.height,
            activity_level=profile.activity_level,
            goal=profile.goal
        )

        if db_profile:
            for key, value in profile.dict().items():
                setattr(db_profile, key, value)
            db_profile.required_calories = requirements["calories"]
            db_profile.required_protein = requirements["protein"]
            db_profile.required_fat = requirements["fat"]
            db_profile.required_carbs = requirements["carbs"]
        else:
            db_profile = UserProfile(
                **profile.dict(),
                required_calories=requirements["calories"],
                required_protein=requirements["protein"],
                required_fat=requirements["fat"],
                required_carbs=requirements["carbs"]
            )
            db.add(db_profile)

        db.commit()
        db.refresh(db_profile)

        return UserProfileResponse(
            id=db_profile.id,
            name=db_profile.name,
            age=db_profile.age,
            gender=db_profile.gender,
            weight=db_profile.weight,
            height=db_profile.height,
            activity_level=db_profile.activity_level,
            goal=db_profile.goal,  # ✅ AGREGADO AQUÍ
            requirements=NutritionalRequirements(**requirements)
        )

    except Exception as e:
        print("❌ Error en /profile/:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

# ✅ Rutas adicionales
app.include_router(daily_log_router)
app.include_router(profile_router)
app.include_router(recommendations_router)

@app.get("/")
def root():
    return {"message": "✅ FastAPI + YOLO backend funcionando correctamente"}
