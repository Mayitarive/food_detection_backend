from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import os
from dotenv import load_dotenv
from food_macros import FOOD_MACROS
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import date

# -------------------------
# Cargar variables de entorno
# -------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# -------------------------
# Configurar SQLAlchemy
# -------------------------
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------
# Modelo de base de datos
# -------------------------
class DailyLog(Base):
    __tablename__ = "daily_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    date = Column(Date, default=date.today)
    food = Column(String, nullable=False)
    proteins = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    kcal = Column(Float)

Base.metadata.create_all(bind=engine)

# -------------------------
# Iniciar FastAPI
# -------------------------
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    global model
    print("🔁 Cargando modelo desde disco local...")
    model = tf.saved_model.load("./ssd_mobilenet_v2_saved_model")
    print("✅ Modelo cargado correctamente desde local")

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
    return class_ids, scores

def get_macronutrients(food_name):
    return FOOD_MACROS.get(food_name.lower(), {
        "proteins": 0,
        "carbs": 0,
        "fats": 0,
        "kcal": 0
    })

# -------------------------
# Dependencia para sesión DB
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Endpoint de prueba
# -------------------------
@app.get("/")
def root():
    return {"message": "FastAPI backend corriendo correctamente"}

# -------------------------
# Endpoint principal
# -------------------------
@app.post("/detect/")
async def detect_food(file: UploadFile = File(...), user_name: str = "anon", db: SessionLocal = Depends(get_db)):
    contents = await file.read()
    img = read_imagefile(contents)

    class_ids, scores = detect_objects(img, model)
    threshold = 0.5
    detected_foods = []

    for idx, score in enumerate(scores):
        if score >= threshold:
            class_id = class_ids[idx]
            food_name = classes.get(class_id, "Unknown")
            if food_name != "Unknown":
                macros = get_macronutrients(food_name)
                log = DailyLog(
                    user_name=user_name,
                    food=food_name,
                    proteins=macros["proteins"],
                    carbs=macros["carbs"],
                    fats=macros["fats"],
                    kcal=macros["kcal"]
                )
                db.add(log)
                db.commit()
                detected_foods.append({"food": food_name, "macronutrients": macros})

    if not detected_foods:
        return JSONResponse(content={"message": "No se detectó ningún alimento conocido."})

    return JSONResponse(content={"detections": detected_foods})
