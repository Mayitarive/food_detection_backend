FROM python:3.11-slim

WORKDIR /app

# 🛠 Instalar bibliotecas necesarias para OpenCV y Ultralytics
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ✅ Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copiar todo el proyecto
COPY . .

# ✅ Exponer puerto usado por FastAPI
EXPOSE 8080

# ✅ Comando para iniciar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
