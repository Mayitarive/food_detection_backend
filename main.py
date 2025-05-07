from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from food_macros import FOOD_MACROS

app = FastAPI()

# ✅ Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# ✅ Cargar modelo de detección
try:
    model_path = "ssd_mobilenet_v2_saved_model"
    model = tf.saved_model.load(model_path)
    print("✅ Modelo local cargado correctamente")
except Exception as e:
    print("❌ Error cargando modelo:", e)

# ✅ Mapeo de clases detectables
classes = {
    53: "apple",
    59: "pizza",
    61: "cake",
    58: "hot dog",
    60: "donut",
    54: "sandwich",
    56: "broccoli",
    52: "banana",
}

# ✅ Funciones auxiliares
def read_imagefile(file) -> np.ndarray:
    image = Image.open(io.BytesIO(file)).convert("RGB")
    return np.array(image)

def detect_objects(image, model):
    input_tensor = tf.convert_to_tensor(image)[tf.newaxis, ...]
    detections = model(input_tensor)
    class_ids = detections['detection_classes'][0].numpy().astype(int)
    scores = detections['detection_scores'][0].numpy()
    boxes = detections['detection_boxes'][0].numpy()
    return class_ids, scores, boxes

def get_macronutrients(food_name):
    return FOOD_MACROS.get(food_name.lower(), {
        "proteins": "No disponible",
        "carbs": "No disponible",
        "fats": "No disponible",
        "kcal": "No disponible"
    })

# ✅ Rutas
@app.get("/")
def root():
    return {"message": "FastAPI backend corriendo correctamente"}

@app.post("/detect/")
async def detect_food(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        img = read_imagefile(contents)
        class_ids, scores, _ = detect_objects(img, model)
        threshold = 0.5
        detected_foods = []

        for idx, score in enumerate(scores):
            if score >= threshold:
                class_id = class_ids[idx]
                food_name = classes.get(class_id, "Unknown")
                detected_foods.append(food_name)

        if not detected_foods:
            return JSONResponse(content={"message": "No se detectó ningún alimento conocido."})

        results = []
        for food in detected_foods:
            macros = get_macronutrients(food)
            results.append({
                "food": food,
                "macronutrients": macros
            })

        return JSONResponse(content={"detections": results})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ✅ Endpoint corregido para guardar perfil con requerimientos
@app.post("/profile/", response_model=UserProfileResponse)
def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(UserProfile).filter(UserProfile.name == profile.name).first()

    # Calcular requerimientos nutricionales
    requirements = calculate_requirements(
        age=profile.age,
        gender=profile.gender,
        weight=profile.weight,
        height=profile.height,
        activity_level=profile.activity_level
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
        requirements=NutritionalRequirements(**requirements)
    )

# ✅ Incluir rutas externas
app.include_router(daily_log_router)
app.include_router(profile_router)
app.include_router(recommendations_router)
