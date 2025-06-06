import cv2
import mediapipe as mp
# import mediapipe.python.solutions.drawing_utils as mp_drawing # Non utilisé, donc commenté/supprimé
import numpy as np
import pygame
import time
from datetime import datetime
import os

# Initialisation de pygame pour les alertes sonores
audio_available = False
try:
    pygame.mixer.init()
    pygame.mixer.music.load("data/alarm.wav")
    audio_available = True
    print("Audio system initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize audio system ({str(e)}). Running in silent mode.")

# Initialisation de MediaPipe Face Mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialisation de MediaPipe Hands
hands = mp.solutions.hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# Points des yeux
LEFT_EYE_TOP = 386
LEFT_EYE_BOTTOM = 374
RIGHT_EYE_TOP = 159
RIGHT_EYE_BOTTOM = 145

# Points pour la bouche (bâillement)
MOUTH_TOP = 13      # Lèvre supérieure
MOUTH_BOTTOM = 14   # Lèvre inférieure
MOUTH_LEFT = 78     # Coin gauche de la bouche
MOUTH_RIGHT = 308   # Coin droit de la bouche
MOUTH_INNER_TOP = 12    # Point intérieur haut
MOUTH_INNER_BOTTOM = 15 # Point intérieur bas

# Points pour la position de la tête
NOSE_TIP = 1
LEFT_EAR = 234
RIGHT_EAR = 454
FOREHEAD = 10       # Point du front
CHIN = 152         # Point du menton
LEFT_TEMPLE = 447   # Temple gauche
RIGHT_TEMPLE = 227  # Temple droit

# Paramètres de détection
EYE_CLOSED_THRESHOLD = 0.02
MOUTH_OPEN_THRESHOLD = 0.4     # Ajusté pour mieux détecter les bâillements
MOUTH_ASPECT_RATIO_THRESHOLD = 0.6  # Ratio largeur/hauteur de la bouche
HEAD_ROTATION_THRESHOLD = 0.2   # Ajusté pour la rotation de la tête
HEAD_TILT_THRESHOLD = 0.1      # Seuil pour l'inclinaison de la tête
EYES_CLOSED_TIME_THRESHOLD = 10.0
PHONE_DETECTION_THRESHOLD = 5.0  # Temps en secondes pour détecter l'utilisation du téléphone

# Niveaux d'alerte
ALERT_LEVELS = {
    'NORMAL': {'color': (0, 255, 0), 'sound': False},
    'WARNING': {'color': (0, 255, 255), 'sound': False},
    'DANGER': {'color': (0, 0, 255), 'sound': True}
}

def calculate_eye_opening(landmarks, top_idx, bottom_idx, image_height):
    """Calcule l'ouverture de l'œil"""
    top = landmarks[top_idx]
    bottom = landmarks[bottom_idx]
    return abs(top.y - bottom.y)

def calculate_mouth_opening(landmarks, top_idx, bottom_idx, left_idx, right_idx):
    """Calcule l'ouverture de la bouche avec ratio d'aspect"""
    top = landmarks[top_idx]
    bottom = landmarks[bottom_idx]
    left = landmarks[left_idx]
    right = landmarks[right_idx]
    
    # Calcul de la hauteur et largeur de la bouche
    vertical_distance = abs(top.y - bottom.y)
    horizontal_distance = abs(left.x - right.x)
    
    # Calcul du ratio d'aspect de la bouche (MAR - Mouth Aspect Ratio)
    if horizontal_distance == 0:
        return 0
    
    mar = vertical_distance / horizontal_distance
    return mar, vertical_distance

def check_head_position(landmarks):
    """Vérifie la position de la tête de manière plus précise"""
    nose = landmarks[NOSE_TIP]
    left_ear = landmarks[LEFT_EAR]
    right_ear = landmarks[RIGHT_EAR]
    forehead = landmarks[FOREHEAD]
    chin = landmarks[CHIN]
    left_temple = landmarks[LEFT_TEMPLE]
    right_temple = landmarks[RIGHT_TEMPLE]
    
    # Calcul de la rotation horizontale (gauche-droite)
    ear_diff = abs(left_ear.x - right_ear.x)
    temple_diff = abs(left_temple.x - right_temple.x)
    rotation = (ear_diff + temple_diff) / 2
    
    # Calcul de l'inclinaison (haut-bas)
    vertical_angle = abs(forehead.y - chin.y)
    
    # Détermination de la direction
    head_state = {
        'turned': False,
        'tilted': False,
        'direction_h': None,
        'direction_v': None
    }
    
    # Vérification de la rotation horizontale
    if rotation > HEAD_ROTATION_THRESHOLD:
        head_state['turned'] = True
        head_state['direction_h'] = "gauche" if left_ear.x > right_ear.x else "droite"
    
    # Vérification de l'inclinaison verticale
    if vertical_angle > HEAD_TILT_THRESHOLD:
        head_state['tilted'] = True
        head_state['direction_v'] = "bas" if nose.y > (forehead.y + chin.y)/2 else "haut"
    
    return head_state

def detect_phone_usage(hand_landmarks, image_height, image_width):
    """Détecte si la main tient potentiellement un téléphone"""
    if not hand_landmarks:
        return False
    
    # Points clés de la main
    thumb_tip = hand_landmarks.landmark[4]  # Pouce
    index_tip = hand_landmarks.landmark[8]  # Index
    middle_tip = hand_landmarks.landmark[12] # Majeur
    ring_tip = hand_landmarks.landmark[16]   # Annulaire
    pinky_tip = hand_landmarks.landmark[20]  # Auriculaire
    
    # Conversion en coordonnées pixels
    thumb = np.array([thumb_tip.x * image_width, thumb_tip.y * image_height])
    index = np.array([index_tip.x * image_width, index_tip.y * image_height])
    middle = np.array([middle_tip.x * image_width, middle_tip.y * image_height])
    ring = np.array([ring_tip.x * image_width, ring_tip.y * image_height])
    pinky = np.array([pinky_tip.x * image_width, pinky_tip.y * image_height])
    
    # Calcul des distances entre les doigts
    distances = [
        np.linalg.norm(thumb - index),
        np.linalg.norm(index - middle),
        np.linalg.norm(middle - ring),
        np.linalg.norm(ring - pinky)
    ]
    
    # Configuration typique de la main tenant un téléphone :
    # - Doigts relativement proches les uns des autres
    # - Position horizontale ou légèrement inclinée
    avg_distance = np.mean(distances)
    max_distance = np.max(distances)
    
    # Vérification de la position et de l'écartement des doigts
    fingers_close = avg_distance < image_width * 0.15  # Les doigts sont proches
    fingers_aligned = max_distance < image_width * 0.25  # Les doigts sont alignés
    
    return fingers_close and fingers_aligned

def determine_alert_level(eyes_closed_time, is_yawning, head_state, phone_detected_time):
    """Détermine le niveau d'alerte basé sur plusieurs facteurs"""
    danger_count = 0
    
    # Vérification des yeux fermés
    if eyes_closed_time > EYES_CLOSED_TIME_THRESHOLD * 0.8:
        danger_count += 2
    elif eyes_closed_time > EYES_CLOSED_TIME_THRESHOLD * 0.5:
        danger_count += 1
    
    # Vérification du bâillement
    if is_yawning:
        danger_count += 1
    
    # Vérification de la position de la tête
    if head_state['turned'] and head_state['tilted']:
        danger_count += 2
    elif head_state['turned'] or head_state['tilted']:
        danger_count += 1
    
    # Vérification de l'utilisation du téléphone
    if phone_detected_time > PHONE_DETECTION_THRESHOLD:
        danger_count += 3  # Danger plus élevé pour l'utilisation du téléphone
    elif phone_detected_time > 0:
        danger_count += 1
    
    # Détermination du niveau d'alerte
    if danger_count >= 3:
        return 'DANGER'
    elif danger_count >= 1:
        return 'WARNING'
    return 'NORMAL'

def log_detection(message, ear_value=None):
    """Enregistre les événements de détection"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp}: {message}"
    if ear_value is not None:
        log_message += f" (EAR: {ear_value:.3f})"
    
    print(log_message)  # Affichage console
    with open("data/detection.log", "a") as f:
        f.write(log_message + "\n")

def main():
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Tentative avec une autre caméra...")
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Impossible d'accéder à la caméra.")
        return
    
    print("Démarrage du système de détection de somnolence")
    
    # Variables de suivi
    eyes_closed_start = None
    alert_active = False
    yawn_count = 0
    last_yawn_time = time.time()
    consecutive_yawns = 0
    phone_detection_start = None
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Échec de la capture de la caméra.")
            break
            
        height, width = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Détection du visage
        face_results = face_mesh.process(image_rgb)
        
        # Détection des mains
        hands_results = hands.process(image_rgb)
        
        current_time = time.time()
        phone_detected = False
        
        # Analyse des mains pour la détection du téléphone
        if hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                if detect_phone_usage(hand_landmarks, height, width):
                    phone_detected = True
                    if phone_detection_start is None:
                        phone_detection_start = current_time
                    
                    # Dessiner les points de la main
                    mp.solutions.drawing_utils.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp.solutions.hands.HAND_CONNECTIONS,
                        mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),
                        mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )
        
        if not phone_detected:
            phone_detection_start = None
        
        phone_detected_time = (current_time - phone_detection_start) if phone_detection_start else 0
        
        if face_results.multi_face_landmarks:
            landmarks = face_results.multi_face_landmarks[0].landmark
            
            # Détection des yeux fermés
            left_eye_opening = calculate_eye_opening(landmarks, LEFT_EYE_TOP, LEFT_EYE_BOTTOM, height)
            right_eye_opening = calculate_eye_opening(landmarks, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM, height)
            
            # Détection améliorée du bâillement
            mar, mouth_height = calculate_mouth_opening(
                landmarks, 
                MOUTH_INNER_TOP, 
                MOUTH_INNER_BOTTOM,
                MOUTH_LEFT,
                MOUTH_RIGHT
            )
            is_yawning = mar > MOUTH_ASPECT_RATIO_THRESHOLD and mouth_height > MOUTH_OPEN_THRESHOLD
            
            # Détection améliorée de la position de la tête
            head_state = check_head_position(landmarks)
            
            # Vérification des yeux fermés
            eyes_closed = (left_eye_opening < EYE_CLOSED_THRESHOLD and 
                         right_eye_opening < EYE_CLOSED_THRESHOLD)
            
            # Gestion du bâillement
            if is_yawning:
                if current_time - last_yawn_time > 3.0:  # Minimum 3s entre les bâillements
                    yawn_count += 1
                    consecutive_yawns += 1
                    last_yawn_time = current_time
            else:
                if current_time - last_yawn_time > 10.0:  # Réinitialisation après 10s sans bâillement
                    consecutive_yawns = 0
            
            # Calcul du temps écoulé yeux fermés
            if eyes_closed:
                if eyes_closed_start is None:
                    eyes_closed_start = current_time
                elapsed_time = current_time - eyes_closed_start
            else:
                elapsed_time = 0
                eyes_closed_start = None
            
            # Mise à jour du niveau d'alerte avec la détection du téléphone
            alert_level = determine_alert_level(
                elapsed_time if eyes_closed_start else 0,
                consecutive_yawns >= 2,
                head_state,
                phone_detected_time
            )
            
            # Affichage des informations
            alert_color = ALERT_LEVELS[alert_level]['color']
            if ALERT_LEVELS[alert_level]['sound'] and not alert_active and audio_available:
                try:
                    pygame.mixer.music.play(-1)
                    alert_active = True
                except Exception as e:
                    print(f"Warning: Could not play alert sound ({str(e)})")
            elif not ALERT_LEVELS[alert_level]['sound'] and alert_active and audio_available:
                try:
                    pygame.mixer.music.stop()
                    alert_active = False
                except Exception as e:
                    print(f"Warning: Could not stop alert sound ({str(e)})")
            elif not audio_available:
                # Visual-only alert when audio is not available
                alert_active = ALERT_LEVELS[alert_level]['sound']
            
            # Affichage des informations
            cv2.putText(image, f"Niveau: {alert_level}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, alert_color, 2)
            
            if eyes_closed:
                remaining_time = max(0, EYES_CLOSED_TIME_THRESHOLD - elapsed_time)
                cv2.putText(image, f"Temps: {remaining_time:.1f}s", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, alert_color, 2)
            
            # Affichage des bâillements
            if is_yawning:
                cv2.putText(image, f"BAILLEMENT! ({consecutive_yawns})", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Affichage de la position de la tête
            head_text = []
            if head_state['turned']:
                head_text.append(f"Rotation: {head_state['direction_h']}")
            if head_state['tilted']:
                head_text.append(f"Inclinaison: {head_state['direction_v']}")
            
            if head_text:
                cv2.putText(image, " + ".join(head_text), (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.putText(image, f"Total Bâillements: {yawn_count}", (10, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Affichage de l'utilisation du téléphone
            if phone_detected:
                warning_text = f"ATTENTION: Téléphone détecté! ({phone_detected_time:.1f}s)"
                cv2.putText(image, warning_text, (10, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Dessin du rectangle d'alerte
            if alert_level == 'DANGER':
                cv2.rectangle(image, (0, 0), (width, height), alert_color, 3)
        
        else:
            cv2.putText(image, "Visage non détecté", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            eyes_closed_start = None
        
        # Affichage de l'image
        cv2.imshow('Détecteur de Somnolence', image)
        
        # Sortie avec 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    if audio_available:
        pygame.mixer.quit()

if __name__ == "__main__":
    # Création des dossiers et fichiers nécessaires
    os.makedirs("data", exist_ok=True)
    
    # Vérification du fichier son
    if not os.path.exists("data/alarm.wav"):
        print("ATTENTION: Fichier d'alarme manquant. Veuillez ajouter un fichier 'alarm.wav' dans le dossier data/")
    else:
        main() 