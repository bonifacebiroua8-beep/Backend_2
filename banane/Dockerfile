# Dockerfile — UbuntuTech Backend v3.0 — Railway optimisé
FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libmagic1 \
    gcc \
    g++ \
    cmake \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads_temp exports logs .logs

EXPOSE 8000

# Railway injecte $PORT automatiquement
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
