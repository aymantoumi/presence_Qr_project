# 1. Image de base Python
FROM python:3.10-slim

# 2. Configuration pour éviter les problèmes de cache et de logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Dossier de travail dans le conteneur
WORKDIR /app

# 4. Installation des dépendances système (Nécessaire pour PyCairo et Psycopg2)
# J'ai ajouté libcairo2-dev et pkg-config car j'ai vu pycairo dans vos requirements
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copie des dépendances et installation
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 6. Copie du code source
COPY . /app/

# 7. Commande de lancement (L'adresse 0.0.0.0 est obligatoire pour Docker)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]