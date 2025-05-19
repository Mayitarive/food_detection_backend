FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer puerto
EXPOSE 10000

# Usar 10000 si Railway no define PORT
ENV PORT=10000

# Usar ENTRYPOINT con exec explícito (mejor que CMD para Railway)
ENTRYPOINT ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
