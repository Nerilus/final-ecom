#!/bin/bash

echo "Déploiement du Détecteur de Somnolence sur VPS"
echo "=============================================="

# Vérification des droits sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté avec les droits sudo"
    exit 1
fi

# Configuration du serveur audio virtuel
setup_audio() {
    echo "Configuration du serveur audio virtuel..."
    apt-get install -y pulseaudio alsa-utils
    
    # Création de l'utilisateur pulse si nécessaire
    id -u pulse &>/dev/null || useradd -r -g audio pulse
    
    # Configuration de PulseAudio pour fonctionner sans interface graphique
    cat > /etc/pulse/default.pa << EOL
load-module module-native-protocol-unix
load-module module-null-sink sink_name=dummy
load-module module-always-sink
EOL
    
    # Démarrage de PulseAudio en mode système
    pulseaudio -D --system
}

echo "1. Mise à jour du système..."
apt update && apt upgrade -y

echo "2. Installation des dépendances système..."
apt install -y python3-pip python3-opencv libopencv-dev python3-venv
apt install -y libsm6 libxext6 libxrender-dev libglib2.0-0
apt install -y xvfb # Pour le support d'affichage virtuel

# Installation des dépendances audio
setup_audio

echo "3. Création du répertoire du projet..."
PROJECT_DIR="/opt/drowsiness_detector"
mkdir -p $PROJECT_DIR
cp -r ./* $PROJECT_DIR/

echo "4. Configuration de l'environnement Python..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "5. Configuration du service systemd..."
cat > /etc/systemd/system/drowsiness_detector.service << EOL
[Unit]
Description=Drowsiness Detector Service
After=network.target pulseaudio.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=DISPLAY=:0
Environment=PULSE_SERVER=unix:/run/pulse/native
Environment=PYTHONPATH=$PROJECT_DIR
ExecStartPre=/usr/bin/Xvfb :0 -screen 0 1920x1080x24 &
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

echo "6. Configuration des permissions..."
chown -R root:root $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

echo "7. Configuration du monitoring..."
apt install -y htop
curl -sSL https://raw.githubusercontent.com/netdata/netdata/master/packaging/installer/install.sh | bash

echo "8. Démarrage des services..."
systemctl daemon-reload
systemctl enable drowsiness_detector
systemctl start drowsiness_detector

echo "9. Vérification du statut..."
systemctl status drowsiness_detector

echo "=============================================="
echo "Installation terminée !"
echo "Pour voir les logs : sudo journalctl -u drowsiness_detector -f"
echo "Pour vérifier le statut : sudo systemctl status drowsiness_detector"
echo "Pour tester l'audio : paplay /usr/share/sounds/alsa/Front_Center.wav"
echo "=============================================="

# Création d'un script de test audio
cat > $PROJECT_DIR/test_audio.py << EOL
import pygame
import time

def test_audio():
    pygame.mixer.init()
    try:
        pygame.mixer.music.load("data/alarm.wav")
        print("Test de lecture audio...")
        pygame.mixer.music.play()
        time.sleep(2)
        pygame.mixer.music.stop()
        print("Test audio réussi!")
    except Exception as e:
        print(f"Erreur lors du test audio: {str(e)}")
    finally:
        pygame.mixer.quit()

if __name__ == "__main__":
    test_audio()
EOL

echo "Pour tester l'audio spécifiquement : python3 $PROJECT_DIR/test_audio.py" 