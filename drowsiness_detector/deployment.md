# Guide de Déploiement sur VPS

## Prérequis VPS

- Ubuntu 20.04 ou plus récent
- Au moins 2GB de RAM
- 20GB d'espace disque
- Accès SSH root ou sudo

## 1. Installation des Dépendances Système

```bash
# Mise à jour du système
sudo apt update
sudo apt upgrade -y

# Installation des paquets nécessaires
sudo apt install -y python3-pip
sudo apt install -y python3-opencv
sudo apt install -y libopencv-dev
sudo apt install -y python3-venv
sudo apt install -y ffmpeg

# Installation des dépendances pour OpenCV et MediaPipe
sudo apt install -y libsm6 libxext6 libxrender-dev
sudo apt install -y libglib2.0-0
```

## 2. Configuration de l'Environnement

```bash
# Création du répertoire du projet
mkdir -p /opt/drowsiness_detector
cd /opt/drowsiness_detector

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
pip install --upgrade pip
pip install opencv-python
pip install mediapipe
pip install numpy
pip install pygame
```

## 3. Configuration du Service Systemd

Créez un fichier service pour gérer le démarrage automatique :

```bash
sudo nano /etc/systemd/system/drowsiness_detector.service
```

Contenu du fichier service :
```ini
[Unit]
Description=Drowsiness Detector Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/drowsiness_detector
Environment=DISPLAY=:0
Environment=PYTHONPATH=/opt/drowsiness_detector
ExecStart=/opt/drowsiness_detector/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## 4. Configuration de X11 (pour l'affichage)

```bash
# Installation de X11
sudo apt install -y xorg
sudo apt install -y x11vnc
sudo apt install -y xvfb

# Configuration de l'écran virtuel
sudo nano /etc/X11/xorg.conf
```

Contenu de xorg.conf :
```conf
Section "Device"
    Identifier "Dummy Driver"
    Driver "dummy"
EndSection

Section "Monitor"
    Identifier "Dummy Monitor"
EndSection

Section "Screen"
    Identifier "Dummy Screen"
    Device "Dummy Driver"
    Monitor "Dummy Monitor"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080"
    EndSubSection
EndSection
```

## 5. Script de Déploiement

Créez un script de déploiement `deploy.sh` :

```bash
#!/bin/bash

# Arrêt du service existant
sudo systemctl stop drowsiness_detector

# Copie des fichiers du projet
sudo cp -r ./* /opt/drowsiness_detector/

# Installation des dépendances
cd /opt/drowsiness_detector
source venv/bin/activate
pip install -r requirements.txt

# Démarrage du service
sudo systemctl daemon-reload
sudo systemctl enable drowsiness_detector
sudo systemctl start drowsiness_detector

# Vérification du statut
sudo systemctl status drowsiness_detector
```

## 6. Commandes de Gestion

```bash
# Démarrer le service
sudo systemctl start drowsiness_detector

# Arrêter le service
sudo systemctl stop drowsiness_detector

# Redémarrer le service
sudo systemctl restart drowsiness_detector

# Voir les logs
sudo journalctl -u drowsiness_detector -f

# Vérifier le statut
sudo systemctl status drowsiness_detector
```

## 7. Configuration de la Caméra

Si vous utilisez une caméra IP ou une webcam réseau :

```python
# Modifiez la ligne dans main.py
cap = cv2.VideoCapture("rtsp://username:password@camera_ip:554/stream1")
```

## 8. Sécurité

1. Configurez un pare-feu :
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
```

2. Créez un utilisateur dédié :
```bash
sudo useradd -m -s /bin/bash drowsiness
sudo usermod -aG sudo drowsiness
```

3. Configurez les permissions :
```bash
sudo chown -R drowsiness:drowsiness /opt/drowsiness_detector
sudo chmod -R 755 /opt/drowsiness_detector
```

## 9. Surveillance

Installez des outils de monitoring :

```bash
# Installation de htop pour la surveillance des ressources
sudo apt install htop

# Installation de netdata pour le monitoring web
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

## 10. Sauvegarde

Créez un script de sauvegarde `backup.sh` :

```bash
#!/bin/bash
BACKUP_DIR="/backup/drowsiness_detector"
DATE=$(date +%Y%m%d_%H%M%S)

# Création du répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarde des fichiers du projet
tar -czf $BACKUP_DIR/drowsiness_detector_$DATE.tar.gz /opt/drowsiness_detector/

# Suppression des sauvegardes de plus de 7 jours
find $BACKUP_DIR -type f -mtime +7 -name '*.tar.gz' -delete
```

## Dépannage

1. Si l'affichage ne fonctionne pas :
```bash
export DISPLAY=:0
sudo Xvfb :0 -screen 0 1920x1080x24 &
```

2. Si la caméra n'est pas détectée :
```bash
ls -l /dev/video*
sudo usermod -a -G video drowsiness
```

3. Si le service ne démarre pas :
```bash
sudo systemctl status drowsiness_detector
sudo journalctl -u drowsiness_detector -n 50
``` 