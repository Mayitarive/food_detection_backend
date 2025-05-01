from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tensorflow as tf
import numpy as np
from PIL import Image
import io
from food_macros import FOOD_MACROS
import os

app = FastAPI()

# -------------------------
# Evento de inicio y apagado
# -------------------------
@app.on_event("startup")
async def startup_event():
    global model
    try:
        print("🔁 Cargando modelo desde disco local...")
        model = tf.saved_model.load("ssd_mobilenet_v2_saved_model")
        print("✅ Modelo cargado correctamente desde local")
    except Exception as e:
        print("❌ Error al cargar modelo local:", e)

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Aplicación FastAPI cerrada.")

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
    return {"message": "FastAPI backend corriendo correctamente con modelo local"}

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
# Trigger redeployment

