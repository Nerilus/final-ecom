#!/bin/bash

# Créer un certificat SSL auto-signé si non existant
if [ ! -f "./ssl/cert.pem" ] || [ ! -f "./ssl/key.pem" ]; then
    mkdir -p ssl
    openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365 -subj "/CN=localhost"
fi

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API avec SSL
uvicorn api:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./ssl/key.pem --ssl-certfile=./ssl/cert.pem --reload 