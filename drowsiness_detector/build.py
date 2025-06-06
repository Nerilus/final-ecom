import PyInstaller.__main__
import os
import shutil

def build_exe():
    # Nettoyage des dossiers de build précédents
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Configuration de PyInstaller
    PyInstaller.__main__.run([
        'main.py',                      # Script principal
        '--name=DrowsinessDetector',    # Nom de l'exécutable
        '--onefile',                    # Créer un seul fichier
        '--windowed',                   # Mode fenêtré (pas de console)
        '--add-data=data/alarm.wav;data', # Inclure le fichier audio
        '--hidden-import=mediapipe',    # Imports cachés
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=pygame',
        '--icon=data/icon.ico',         # Icône de l'application (à créer)
        '--clean',                      # Nettoyer avant la construction
        '--log-level=INFO',            # Niveau de log
    ])
    
    print("Build terminé ! L'exécutable se trouve dans le dossier 'dist'")

if __name__ == "__main__":
    build_exe() 