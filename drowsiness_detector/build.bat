@echo off
echo Nettoyage de l'environnement precedent...
if exist venv rmdir /s /q venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Creation d'un nouvel environnement virtuel...
python -m venv venv
call venv\Scripts\activate.bat

echo Mise a jour des outils de base...
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

echo Installation des dependances (mode binaire uniquement)...
pip install --no-cache-dir -r requirements-build.txt

echo Verification de l'installation des packages...
pip list

echo Creation de l'executable avec le fichier spec...
pyinstaller --clean DrowsinessDetector.spec

echo.
if exist dist\DrowsinessDetector.exe (
    echo Build reussi! L'executable se trouve dans le dossier 'dist'
    echo Verification des fichiers...
    dir dist
) else (
    echo Erreur lors de la creation de l'executable
)
echo.
pause 