from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Union
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import io
import time
from datetime import datetime
import base64
import json
import pygame
import os
from pathlib import Path

# Initialisation de pygame pour l'audio
pygame.mixer.init()
ALARM_SOUND = str(Path(__file__).parent / "data" / "alarm.wav")
if not os.path.exists(ALARM_SOUND):
    raise FileNotFoundError(f"Le fichier audio {ALARM_SOUND} n'existe pas")
pygame.mixer.music.load(ALARM_SOUND)

# Import des fonctions de détection
from detection_utils import (
    calculate_eye_opening,
    calculate_mouth_opening,
    check_head_position,
    detect_phone_usage,
    determine_alert_level
)

# Variables globales pour la gestion de l'alarme
danger_start_time = {}  # Pour suivre le début de l'état DANGER pour chaque connexion
DANGER_THRESHOLD = 5  # Secondes avant de déclencher l'alarme

app = FastAPI(
    title="Drowsiness Detection API",
    description="API pour la détection de somnolence et de distractions au volant",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation de MediaPipe
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

hands = mp.solutions.hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

class HeadPosition(BaseModel):
    turned: bool
    tilted: bool
    direction_h: Optional[str] = None
    direction_v: Optional[str] = None

class DetectionResponse(BaseModel):
    alert_level: str
    eyes_state: Dict[str, float]
    mouth_state: Dict[str, float]
    head_position: HeadPosition
    phone_detected: bool
    timestamp: str
    alarm_active: bool = False

def check_and_handle_alarm(alert_level: str, connection_id: str) -> bool:
    """Gère l'activation et la désactivation de l'alarme"""
    current_time = time.time()
    alarm_active = False

    if alert_level == 'DANGER':
        if connection_id not in danger_start_time:
            danger_start_time[connection_id] = current_time
        elif current_time - danger_start_time[connection_id] >= DANGER_THRESHOLD:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)  # -1 pour jouer en boucle
            alarm_active = True
    else:
        if connection_id in danger_start_time:
            del danger_start_time[connection_id]
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

    return alarm_active

def process_image(image_bytes: bytes, connection_id: str) -> DetectionResponse:
    """Traite une image et retourne les résultats de détection"""
    try:
        # Conversion des bytes en image numpy
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Image invalide")

        height, width = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Analyse du visage
        face_results = face_mesh.process(image_rgb)
        if not face_results.multi_face_landmarks:
            return DetectionResponse(
                alert_level="WARNING",
                eyes_state={"left": 0, "right": 0},
                mouth_state={"mar": 0, "opening": 0},
                head_position=HeadPosition(
                    turned=False,
                    tilted=False,
                    direction_h=None,
                    direction_v=None
                ),
                phone_detected=False,
                timestamp=datetime.now().isoformat(),
                alarm_active=False
            )

        landmarks = face_results.multi_face_landmarks[0].landmark

        # Analyse des yeux
        left_eye = calculate_eye_opening(landmarks, 386, 374, height)
        right_eye = calculate_eye_opening(landmarks, 159, 145, height)

        # Analyse de la bouche
        mar, mouth_opening = calculate_mouth_opening(
            landmarks, 13, 14, 78, 308
        )

        # Analyse de la position de la tête
        head_state = check_head_position(landmarks)

        # Analyse des mains
        hands_results = hands.process(image_rgb)
        phone_detected = False
        if hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                if detect_phone_usage(hand_landmarks, height, width):
                    phone_detected = True
                    break

        # Détermination du niveau d'alerte
        alert_level = determine_alert_level(
            20.0 if (left_eye + right_eye) / 2 < 0.02 else 0,
            mar > 0.4,
            head_state,
            5.0 if phone_detected else 0
        )

        # Gestion de l'alarme
        alarm_active = check_and_handle_alarm(alert_level, connection_id)

        return DetectionResponse(
            alert_level=alert_level,
            eyes_state={
                "left": float(left_eye),
                "right": float(right_eye)
            },
            mouth_state={
                "mar": float(mar),
                "opening": float(mouth_opening)
            },
            head_position=head_state,
            phone_detected=phone_detected,
            timestamp=datetime.now().isoformat(),
            alarm_active=alarm_active
        )

    except Exception as e:
        if connection_id in danger_start_time:
            del danger_start_time[connection_id]
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour le flux vidéo en temps réel"""
    await websocket.accept()
    connection_id = str(id(websocket))  # Identifiant unique pour cette connexion
    try:
        while True:
            data = await websocket.receive_text()
            try:
                image_data = base64.b64decode(data.split(',')[1])
                result = process_image(image_data, connection_id)
                await websocket.send_json(result.dict())
            except Exception as e:
                await websocket.send_json({"error": str(e)})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Nettoyage lors de la déconnexion
        if connection_id in danger_start_time:
            del danger_start_time[connection_id]
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

@app.get("/")
async def root():
    """Page d'accueil avec interface de test"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Système de Détection de Somnolence</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #3498db;
                --success-color: #2ecc71;
                --warning-color: #f1c40f;
                --danger-color: #e74c3c;
                --background-color: #ecf0f1;
                --card-background: #ffffff;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--background-color);
                color: var(--primary-color);
                line-height: 1.6;
                padding: 20px;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: var(--primary-color);
                color: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }

            .subtitle {
                font-size: 1.2em;
                color: rgba(255, 255, 255, 0.8);
            }

            .main-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 20px;
            }

            .video-container {
                background: var(--card-background);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            #videoElement {
                width: 100%;
                border-radius: 5px;
                background-color: #666;
            }

            .results-container {
                background: var(--card-background);
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .status-card {
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 5px;
                background: rgba(255, 255, 255, 0.9);
                border-left: 4px solid var(--secondary-color);
            }

            .metric {
                margin: 15px 0;
                padding: 10px;
                border-radius: 5px;
                background: rgba(0, 0, 0, 0.05);
            }

            .metric-title {
                font-weight: bold;
                color: var(--primary-color);
                margin-bottom: 5px;
            }

            .metric-value {
                font-size: 1.1em;
            }

            .error { 
                color: var(--danger-color);
                padding: 10px;
                border-radius: 5px;
                background: rgba(231, 76, 60, 0.1);
            }

            .success { 
                color: var(--success-color);
                padding: 10px;
                border-radius: 5px;
                background: rgba(46, 204, 113, 0.1);
            }

            .warning { 
                color: var(--warning-color);
                padding: 10px;
                border-radius: 5px;
                background: rgba(241, 196, 15, 0.1);
            }

            .danger { 
                color: var(--danger-color);
                padding: 10px;
                border-radius: 5px;
                background: rgba(231, 76, 60, 0.1);
            }

            .alarm-active {
                animation: blink 1s infinite;
                background: rgba(231, 76, 60, 0.2);
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                text-align: center;
                font-weight: bold;
                font-size: 1.2em;
            }

            @keyframes blink {
                0% { background: rgba(231, 76, 60, 0.2); }
                50% { background: rgba(231, 76, 60, 0.4); }
                100% { background: rgba(231, 76, 60, 0.2); }
            }

            .alert-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 15px;
                font-weight: bold;
            }

            .alert-badge.normal {
                background: var(--success-color);
                color: white;
            }

            .alert-badge.warning {
                background: var(--warning-color);
                color: var(--primary-color);
            }

            .alert-badge.danger {
                background: var(--danger-color);
                color: white;
            }

            @media (max-width: 768px) {
                .main-content {
                    grid-template-columns: 1fr;
                }

                .container {
                    padding: 10px;
                }

                h1 {
                    font-size: 2em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Système de Détection de Somnolence</h1>
                <p class="subtitle">Surveillance en temps réel pour une conduite plus sûre</p>
            </header>

            <div class="main-content">
                <div class="video-container">
                    <h2>Flux Vidéo</h2>
                    <video id="videoElement" autoplay></video>
                    <div id="status" class="status-card"></div>
                </div>

                <div class="results-container">
                    <h2>Analyse en Temps Réel</h2>
                    <div id="results"></div>
                </div>
            </div>
        </div>

        <script>
            const video = document.getElementById('videoElement');
            const results = document.getElementById('results');
            const status = document.getElementById('status');
            let ws = null;

            function formatAlertLevel(level, isAlarmActive) {
                const className = level.toLowerCase();
                const badgeClass = `alert-badge ${className}`;
                const alarmClass = isAlarmActive ? 'alarm-active' : '';
                return `<span class="${badgeClass}">${level}</span> ${isAlarmActive ? '<div class="alarm-active">⚠️ ALARME ACTIVE - Attention danger !</div>' : ''}`;
            }

            async function startCamera() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { 
                            width: 640,
                            height: 480,
                            facingMode: "user"
                        } 
                    });
                    video.srcObject = stream;
                    status.innerHTML = '<p class="success">✓ Caméra activée avec succès</p>';
                    connectWebSocket();
                } catch (err) {
                    console.error('Erreur camera:', err);
                    status.innerHTML = `
                        <div class="error">
                            <h3>❌ Erreur d'accès à la caméra</h3>
                            <p>${err.message}</p>
                            <h4>Solutions possibles :</h4>
                            <ul>
                                <li>Vérifiez que votre caméra est connectée et fonctionne</li>
                                <li>Autorisez l'accès à la caméra dans les paramètres du navigateur</li>
                                <li>Pour Chrome : activez l'option dans chrome://flags/#unsafely-treat-insecure-origin-as-secure</li>
                            </ul>
                        </div>
                    `;
                }
            }

            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    console.log('Connected to WebSocket');
                    status.innerHTML += '<p class="success">✓ Connexion WebSocket établie</p>';
                    sendImages();
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.error) {
                        results.innerHTML = `<div class="error">❌ Erreur: ${data.error}</div>`;
                        return;
                    }
                    results.innerHTML = `
                        <div class="metric">
                            <div class="metric-title">Niveau d'Alerte</div>
                            <div class="metric-value">${formatAlertLevel(data.alert_level, data.alarm_active)}</div>
                        </div>

                        <div class="metric">
                            <div class="metric-title">État des Yeux</div>
                            <div class="metric-value">
                                Gauche: ${data.eyes_state.left.toFixed(3)}
                                Droite: ${data.eyes_state.right.toFixed(3)}
                            </div>
                        </div>

                        <div class="metric">
                            <div class="metric-title">État de la Bouche</div>
                            <div class="metric-value">MAR: ${data.mouth_state.mar.toFixed(3)}</div>
                        </div>

                        <div class="metric">
                            <div class="metric-title">Position de la Tête</div>
                            <div class="metric-value">
                                ${data.head_position.turned ? '↔️ Tournée' : '✓ Normale'} 
                                ${data.head_position.direction_h ? `(${data.head_position.direction_h})` : ''}<br>
                                ${data.head_position.tilted ? '↕️ Inclinée' : '✓ Droite'}
                                ${data.head_position.direction_v ? `(${data.head_position.direction_v})` : ''}
                            </div>
                        </div>

                        <div class="metric">
                            <div class="metric-title">Utilisation du Téléphone</div>
                            <div class="metric-value">
                                ${data.phone_detected ? '📱 Détecté' : '✓ Aucun téléphone détecté'}
                            </div>
                        </div>
                    `;
                };

                ws.onclose = () => {
                    console.log('WebSocket closed');
                    status.innerHTML += '<p class="warning">⚠️ Connexion perdue, tentative de reconnexion...</p>';
                    setTimeout(connectWebSocket, 1000);
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    status.innerHTML += `<p class="error">❌ Erreur WebSocket: ${error.message}</p>`;
                };
            }

            function sendImages() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    try {
                        const canvas = document.createElement('canvas');
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(video, 0, 0);
                        const imageData = canvas.toDataURL('image/jpeg', 0.8);
                        ws.send(imageData);
                    } catch (error) {
                        console.error('Error sending image:', error);
                        status.innerHTML += `<p class="error">❌ Erreur d'envoi d'image: ${error.message}</p>`;
                    }
                }
                setTimeout(sendImages, 100);
            }

            startCamera();
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Endpoint de vérification de l'état de l'API"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()} 