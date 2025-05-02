from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import requests
from food_macros import FOOD_MACROS
from routes import daily_log

app = FastAPI()

app.include_router(daily_log.router)

# -------------------------
# Evento de inicio y apagado
# -------------------------
@app.on_event("startup")
async def startup_event():
    print("✅ Aplicación FastAPI iniciando...")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Aplicación FastAPI cerrada.")

# -------------------------
# Modelo de detección (cargado localmente)
# -------------------------
try:
    model_path = "ssd_mobilenet_v2_saved_model"  # carpeta local
    model = tf.saved_model.load(model_path)
    print("✅ Modelo local cargado correctamente")
except Exception as e:
    print("❌ Error cargando el modelo local:", e)

# -------------------------
# Clases del modelo (COCO)
# -------------------------
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

# -------------------------
# Endpoint de prueba
# -------------------------
@app.get("/")
def root():
    return {"message": "FastAPI backend corriendo correctamente"}

# -------------------------
# Funciones auxiliares
# -------------------------
def read_imagefile(file) -> np.ndarray:
    image = Image.open(io.BytesIO(file)).convert("RGB")
    return np.array(image)

def detect_objects(image, model):
    input_tensor = tf.convert_to_tensor(image)
    input_tensor = input_tensor[tf.newaxis, ...]
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

# -------------------------
# Endpoint principal de detección
# -------------------------
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


from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_profile import UserProfile
from schemas.user_profile import (
    UserProfileCreate,
    UserProfileResponse,
    NutritionalRequirements
)
from utils.requirements import calculate_requirements

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/profile/", response_model=UserProfileResponse)
def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(UserProfile).filter(UserProfile.name == profile.name).first()
    
    if db_profile:
        for key, value in profile.dict().items():
            setattr(db_profile, key, value)
    else:
        db_profile = UserProfile(**profile.dict())
        db.add(db_profile)
    
    db.commit()
    db.refresh(db_profile)

    requirements = calculate_requirements(
        age=profile.age,
        gender=profile.gender,
        weight=profile.weight,
        height=profile.height,
        activity_level=profile.activity_level
    )

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

