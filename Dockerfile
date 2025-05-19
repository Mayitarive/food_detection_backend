FROM python:3.11-slim

WORKDIR /app

# Instalar librerías necesarias para OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .
# Exponer puerto estándar para Railway
EXPOSE 8080

# Comando para iniciar FastAPI (usando el mismo puerto)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
