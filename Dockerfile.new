FROM python:3.11-slim

WORKDIR /app

# 🛠 Instalar librerías del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# ✅ Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copiar todo el código del proyecto
COPY . .

# ✅ Exponer puerto (opcional porque Railway usa el puerto que tú definas)
EXPOSE 10000

# ✅ Iniciar FastAPI con el puerto de Railway o por defecto 10000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
