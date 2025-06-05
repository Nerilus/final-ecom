# Détecteur de Somnolence et de Distractions

Ce projet est un système avancé de détection de somnolence et de distractions qui utilise la vision par ordinateur pour surveiller le conducteur en temps réel.

## Fonctionnalités

### 1. Détection de Somnolence
- Surveillance en temps réel des yeux
- Minuteur de 20 secondes avant l'alerte principale
- Alarme sonore en cas de somnolence détectée
- Affichage visuel de l'état des yeux

### 2. Détection des Bâillements
- Analyse de l'ouverture de la bouche
- Calcul du ratio d'aspect de la bouche (MAR)
- Compteur de bâillements consécutifs
- Réinitialisation après 10 secondes sans bâillement

### 3. Position de la Tête
- Détection de la rotation horizontale (gauche/droite)
- Détection de l'inclinaison verticale (haut/bas)
- Utilisation de 8 points de référence
- Affichage des mouvements combinés

### 4. Détection du Téléphone
- Reconnaissance des mains tenant un téléphone
- Analyse de la position des doigts
- Mesure du temps d'utilisation
- Alerte après 5 secondes d'utilisation

### 5. Système d'Alerte Intelligent
- Trois niveaux d'alerte : NORMAL, WARNING, DANGER
- Combinaison de tous les facteurs de risque
- Alertes visuelles et sonores
- Code couleur intuitif (vert, jaune, rouge)

## Prérequis

### Matériel
- Ordinateur avec webcam
- Bonne luminosité
- Position stable de la caméra

### Logiciel
- Python 3.x
- Bibliothèques requises :
  ```bash
  opencv-python    # Vision par ordinateur
  mediapipe       # Détection des points du visage et des mains
  numpy           # Calculs numériques
  pygame          # Alertes sonores
  ```

## Installation

1. Clonez le repository :
   ```bash
   git clone [URL_DU_REPO]
   cd drowsiness_detector
   ```

2. Installez les dépendances :
   ```bash
   pip3 install opencv-python mediapipe numpy pygame
   ```

3. Vérifiez la structure du projet :
   ```
   drowsiness_detector/
   ├── main.py
   └── data/
       └── alarm.wav
   ```

## Utilisation

1. Lancez le programme :
   ```bash
   python3 main.py
   ```

2. Configuration optimale :
   - Placez-vous à 50-60 cm de la caméra
   - Assurez-vous d'avoir un bon éclairage
   - Évitez les mouvements brusques
   - Gardez la tête dans le champ de vision

3. Fonctionnalités en action :
   - Points verts : détection des yeux active
   - Points rouges/bleus : détection des mains
   - Compte à rebours : temps avant alerte
   - Messages d'état en temps réel
   - Rectangle rouge : alerte de niveau DANGER

4. Commandes :
   - 'q' : Quitter le programme
   - L'alarme s'arrête automatiquement quand le danger est écarté

## Paramètres Personnalisables

Dans `main.py`, vous pouvez ajuster :

```python
# Seuils de détection
EYE_CLOSED_THRESHOLD = 0.02        # Sensibilité yeux fermés
MOUTH_OPEN_THRESHOLD = 0.4         # Seuil bâillement
HEAD_ROTATION_THRESHOLD = 0.2      # Rotation de la tête
HEAD_TILT_THRESHOLD = 0.1         # Inclinaison de la tête
PHONE_DETECTION_THRESHOLD = 5.0    # Temps avant alerte téléphone

# Temps de détection
EYES_CLOSED_TIME_THRESHOLD = 20.0  # Secondes yeux fermés
```

## Dépannage

1. Problèmes de caméra :
   - Vérifiez les permissions
   - Fermez les autres applications utilisant la caméra
   - Essayez un autre index de caméra (0 ou 1)

2. Détection imprécise :
   - Améliorez l'éclairage
   - Ajustez votre position
   - Modifiez les seuils de détection

3. Faux positifs téléphone :
   - Ajustez PHONE_DETECTION_THRESHOLD
   - Évitez les mouvements rapides des mains
   - Maintenez une distance constante

## Contribution

Les contributions sont bienvenues ! Vous pouvez :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités
- Optimiser les algorithmes de détection

## Sécurité

Ce système est conçu comme une aide à la vigilance et ne remplace pas :
- Une conduite responsable
- Des pauses régulières
- Le respect du code de la route
- L'attention constante au volant

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 