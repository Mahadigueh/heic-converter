FROM python:3.12-slim

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libjpeg-dev \
    zlib1g-dev \
    libmupdf-dev \
    mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des packages Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]