@echo off
echo Installation de l'environnement de build...
python -m venv venv
call venv\Scripts\activate.bat

echo Installation des dependances...
pip install -r requirements-build.txt

echo Creation de l'executable...
python build.py

echo.
echo Build termine ! L'executable se trouve dans le dossier 'dist'
echo.
pause 