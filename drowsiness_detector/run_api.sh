#!/bin/bash

# Activer l'environnement virtuel si nécessaire
# source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
uvicorn api:app --host 0.0.0.0 --port 8000 --reload 