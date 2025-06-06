@echo off
echo Installation de l'environnement de build...

:: Suppression de l'ancien environnement virtuel s'il existe
if exist venv rmdir /s /q venv

:: Création d'un nouvel environnement virtuel
python -m venv venv
call venv\Scripts\activate.bat

:: Mise à jour de pip et installation des dépendances de base
python -m pip install --upgrade pip
pip install setuptools wheel

echo Installation des dependances...
pip install -r requirements-build.txt

echo Creation de l'executable...
python build.py

echo.
echo Build termine ! L'executable se trouve dans le dossier 'dist'
echo.
pause 