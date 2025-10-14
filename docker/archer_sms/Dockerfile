ARG PROJECT_SRC=./code/

ARG PROJECT=archer_sms

ARG DOCKER_PATH=./docker/${PROJECT}

FROM python:3.11-slim

ARG PROJECT_SRC
ARG DOCKER_PATH

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY $DOCKER_PATH/config/requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script
COPY $PROJECT_SRC/mr200_sms.py .
COPY $PROJECT_SRC/api_server.py .

# Créer le dossier de logs
RUN mkdir -p /app/logs

# Exposer le port API
EXPOSE 5333

# Script par défaut (serveur API)
CMD ["python3", "api_server.py"]