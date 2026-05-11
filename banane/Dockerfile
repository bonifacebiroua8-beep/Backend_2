# Dockerfile — UbuntuTech Backend v3.0 — Hugging Face Spaces
FROM python:3.11-slim

# Créer utilisateur non-root (requis par HF Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"
ENV HOME="/home/user"

# Cache Whisper et HuggingFace vers /tmp (seul dossier writable sur HF)
ENV WHISPER_CACHE=/tmp/whisper_cache
ENV HF_HOME=/tmp/huggingface_cache
ENV XDG_CACHE_HOME=/tmp/cache

WORKDIR /app

# Dépendances système (en root avant le switch user)
USER root
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libmagic1 \
    gcc \
    g++ \
    cmake \
    build-essential \
    default-libmysqlclient-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

USER user

# Installer les dépendances Python
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY --chown=user . .

# Créer les dossiers nécessaires dans /tmp (writable sur HF)
RUN mkdir -p /tmp/uploads_temp /tmp/exports /tmp/logs /tmp/whisper_cache

# Port HF Spaces = 7860 obligatoire
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
