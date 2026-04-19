FROM python:3.12-slim

# Installation des dépendances système pour pillow-heif
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie des dépendances Python d'abord (pour mieux utiliser le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le reste du code (y compris static/)
COPY . .

# Exposition du port
EXPOSE 8080

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]