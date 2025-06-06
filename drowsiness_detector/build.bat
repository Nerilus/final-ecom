@echo off
echo Nettoyage de l'environnement precedent...
if exist venv rmdir /s /q venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Creation d'un nouvel environnement virtuel...
python -m venv venv
call venv\Scripts\activate.bat

echo Mise a jour des outils de base...
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

echo Installation des dependances (mode binaire uniquement)...
pip install --no-cache-dir -r requirements-build.txt

echo Verification de l'installation de PyInstaller...
pip show pyinstaller
if errorlevel 1 (
    echo Installation de PyInstaller...
    pip install --no-cache-dir pyinstaller
)

echo Creation de l'executable...
pyinstaller --noconfirm --onefile --windowed ^
    --add-data "data/alarm.wav;data" ^
    --hidden-import mediapipe ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import pygame ^
    --name DrowsinessDetector ^
    main.py

echo.
if exist dist\DrowsinessDetector.exe (
    echo Build reussi! L'executable se trouve dans le dossier 'dist'
) else (
    echo Erreur lors de la creation de l'executable
)
echo.
pause 