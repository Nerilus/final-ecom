#!/bin/bash

echo "Déploiement du Détecteur de Somnolence sur VPS"
echo "=============================================="

# Vérification des droits sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté avec les droits sudo"
    exit 1
fi

echo "1. Mise à jour du système..."
apt update && apt upgrade -y

echo "2. Installation des dépendances système..."
apt install -y python3-pip python3-opencv libopencv-dev python3-venv ffmpeg
apt install -y libsm6 libxext6 libxrender-dev libglib2.0-0
apt install -y xorg x11vnc xvfb

echo "3. Création du répertoire du projet..."
mkdir -p /opt/drowsiness_detector
cp -r ./* /opt/drowsiness_detector/

echo "4. Configuration de l'environnement Python..."
cd /opt/drowsiness_detector
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install opencv-python mediapipe numpy pygame

echo "5. Configuration du service systemd..."
cat > /etc/systemd/system/drowsiness_detector.service << EOL
[Unit]
Description=Drowsiness Detector Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/drowsiness_detector
Environment=DISPLAY=:0
Environment=PYTHONPATH=/opt/drowsiness_detector
Environment=SDL_AUDIODRIVER=dummy
Environment=AUDIODEV=null
ExecStart=/opt/drowsiness_detector/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

echo "6. Configuration de l'écran virtuel..."
cat > /etc/X11/xorg.conf << EOL
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
EOL

echo "7. Configuration de la sécurité..."
# Création de l'utilisateur dédié
useradd -m -s /bin/bash drowsiness 2>/dev/null || true
usermod -aG sudo drowsiness
usermod -a -G video drowsiness

# Configuration des permissions
chown -R drowsiness:drowsiness /opt/drowsiness_detector
chmod -R 755 /opt/drowsiness_detector

# Configuration du pare-feu
ufw enable
ufw allow ssh
ufw allow http
ufw allow https

echo "8. Installation des outils de monitoring..."
apt install -y htop
bash <(curl -Ss https://my-netdata.io/kickstart.sh) --non-interactive

echo "9. Configuration des sauvegardes..."
cat > /opt/drowsiness_detector/backup.sh << EOL
#!/bin/bash
BACKUP_DIR="/backup/drowsiness_detector"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR
tar -czf \$BACKUP_DIR/drowsiness_detector_\$DATE.tar.gz /opt/drowsiness_detector/
find \$BACKUP_DIR -type f -mtime +7 -name '*.tar.gz' -delete
EOL

chmod +x /opt/drowsiness_detector/backup.sh

echo "10. Démarrage des services..."
# Démarrage de l'écran virtuel
export DISPLAY=:0
Xvfb :0 -screen 0 1920x1080x24 &

# Configuration du service
systemctl daemon-reload
systemctl enable drowsiness_detector
systemctl start drowsiness_detector

echo "11. Vérification du statut..."
systemctl status drowsiness_detector

echo "=============================================="
echo "Installation terminée !"
echo "Pour voir les logs : sudo journalctl -u drowsiness_detector -f"
echo "Pour vérifier le statut : sudo systemctl status drowsiness_detector"
echo "Interface de monitoring : http://votre-ip:19999"
echo "==============================================" 