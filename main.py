from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image
import io
import os
from food_macros import FOOD_MACROS
import datetime

# Configuración inicial
app = FastAPI()

# CORS (opcional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo desde disco local
model = tf.saved_model.load("ssd_mobilenet_v2_saved_model")
print("✅ Modelo cargado correctamente desde local")

# Diccionario de clases del modelo
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

# ------------------------------
# Configuración de base de datos
# ------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Modelo Usuario
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    age = Column(Integer)
    gender = Column(String)
    height = Column(Float)
    weight = Column(Float)
    activity_level = Column(String)

# Modelo Consumo Diario
class DailyRecord(Base):
    __tablename__ = "daily_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    date = Column(Date, default=func.current_date())
    food = Column(String)
    proteins = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    kcal = Column(Float)

Base.metadata.create_all(bind=engine)

# ------------------------------
# Funciones auxiliares
# ------------------------------
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
        "proteins": 0,
        "carbs": 0,
        "fats": 0,
        "kcal": 0
    })

# ------------------------------
# Endpoints
# ------------------------------
@app.get("/")
def root():
    return {"message": "🍎 API de detección de alimentos funcionando."}

@app.post("/profile/")
def save_user_profile(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    activity_level: str = Form(...)
):
    db = SessionLocal()
    existing = db.query(User).filter(User.name == name).first()
    if existing:
        return {"message": "Perfil ya existe."}
    user = User(name=name, age=age, gender=gender, height=height, weight=weight, activity_level=activity_level)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Perfil guardado", "user_id": user.id}

@app.post("/detect/")
async def detect_food(file: UploadFile = File(...), user_id: int = Form(...)):
    db = SessionLocal()
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
        record = DailyRecord(
            user_id=user_id,
            food=food,
            proteins=macros['proteins'],
            carbs=macros['carbs'],
            fats=macros['fats'],
            kcal=macros['kcal']
        )
        db.add(record)
        db.commit()
        results.append({"food": food, "macronutrients": macros})

    return {"detections": results}
