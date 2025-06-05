# Détecteur de Somnolence

Ce projet utilise la vision par ordinateur pour détecter la somnolence en analysant les yeux du conducteur en temps réel.

## Fonctionnalités

- Détection en temps réel des yeux via la webcam
- Calcul du ratio d'aspect des yeux (EAR)
- Alerte sonore en cas de détection de somnolence
- Enregistrement des événements de somnolence dans un fichier log
- Affichage visuel des points de repère des yeux
- Affichage du ratio EAR en temps réel

## Prérequis

- Python 3.8 ou supérieur
- Webcam fonctionnelle
- Fichier audio 'alarm.wav' dans le dossier data/

## Installation

1. Cloner le repository
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```
3. Ajouter un fichier audio 'alarm.wav' dans le dossier data/

## Utilisation

Pour lancer le détecteur de somnolence :
```bash
python main.py
```

- Appuyez sur 'q' pour quitter le programme
- Le programme enregistre les événements de somnolence dans 'data/alerts.log'

## Comment ça marche

1. Le programme utilise MediaPipe pour détecter les points de repère du visage
2. Il calcule le ratio d'aspect des yeux (EAR) pour déterminer si les yeux sont fermés
3. Si les yeux restent fermés pendant trop longtemps, une alerte sonore est déclenchée
4. Les événements sont enregistrés dans un fichier log

## Paramètres

- `EYE_AR_THRESH` : Seuil pour détecter si l'œil est fermé (défaut : 0.2)
- `EYE_AR_CONSEC_FRAMES` : Nombre de frames consécutives avant l'alerte (défaut : 20) 