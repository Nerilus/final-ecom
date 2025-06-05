import cv2
import mediapipe as mp
# import mediapipe.python.solutions.drawing_utils as mp_drawing # Non utilisé, donc commenté/supprimé
import numpy as np
import pygame
import time
from datetime import datetime
import os

# Initialisation de pygame pour les alertes sonores
pygame.mixer.init()
pygame.mixer.music.load("data/alarm.wav")

# Initialisation de MediaPipe Face Mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Points des yeux (haut et bas)
LEFT_EYE_TOP = 386     # Point du haut de l'œil gauche
LEFT_EYE_BOTTOM = 374  # Point du bas de l'œil gauche
RIGHT_EYE_TOP = 159    # Point du haut de l'œil droit
RIGHT_EYE_BOTTOM = 145 # Point du bas de l'œil droit

# Paramètres de détection
EYE_CLOSED_THRESHOLD = 0.02  # Seuil pour détecter si l'œil est fermé (en pourcentage de la hauteur du visage)
EYE_AR_CONSEC_FRAMES = 3    # Nombre de frames consécutives pour déclencher l'alerte

def calculate_eye_opening(landmarks, top_idx, bottom_idx, image_height):
    """Calcule l'ouverture de l'œil en pourcentage de la hauteur de l'image"""
    top = landmarks[top_idx]
    bottom = landmarks[bottom_idx]
    
    # Calcul de la distance verticale
    distance = abs(top.y - bottom.y)
    
    # Normalisation par rapport à la hauteur de l'image
    return distance

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
    # Essayer d'abord avec l'index 1, puis 0 si ça ne marche pas
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Tentative avec une autre caméra...")
        cap = cv2.VideoCapture(0)
    
    frame_counter = 0
    start_time = time.time()
    alert_active = False
    last_log_time = time.time()
    
    if not cap.isOpened():
        print("Impossible d'accéder à la caméra. Vérifiez les permissions et les connexions.")
        return
    
    log_detection("Démarrage du système de détection de somnolence")
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Échec de la capture de la caméra.")
            break
        
        # Afficher les dimensions de l'image
        height, width = image.shape[:2]
        print(f"Dimensions de l'image: {width}x{height}")
            
        # Conversion en RGB pour MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)
        
        # Debug - vérifier si le visage est détecté
        if not results.multi_face_landmarks:
            print("Aucun visage détecté")
            cv2.putText(image, "AUCUN VISAGE DETECTE", (int(width/4), int(height/2)),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
        else:
            print("Visage détecté!")
            landmarks = results.multi_face_landmarks[0].landmark
            
            # Debug - afficher tous les points du visage
            for idx, landmark in enumerate(landmarks):
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                # Afficher les points des yeux en bleu
                if idx in [LEFT_EYE_TOP, LEFT_EYE_BOTTOM, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM]:
                    cv2.circle(image, (x, y), 3, (255, 0, 0), -1)
                    cv2.putText(image, str(idx), (x+5, y+5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            
            # Calcul de l'ouverture des yeux
            left_eye_opening = calculate_eye_opening(landmarks, LEFT_EYE_TOP, LEFT_EYE_BOTTOM, height)
            right_eye_opening = calculate_eye_opening(landmarks, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM, height)
            
            # Vérification si les yeux sont fermés
            eyes_closed = (left_eye_opening < EYE_CLOSED_THRESHOLD and 
                         right_eye_opening < EYE_CLOSED_THRESHOLD)
            
            if eyes_closed:
                frame_counter += 1
                print(f"Yeux fermés! Frame {frame_counter}/{EYE_AR_CONSEC_FRAMES}")
                cv2.putText(image, "YEUX FERMES!", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                if frame_counter >= EYE_AR_CONSEC_FRAMES and not alert_active:
                    print("ALERTE: Somnolence détectée!")
                    pygame.mixer.music.play(-1)
                    alert_active = True
                    cv2.rectangle(image, (0, 0), (width, height), (0, 0, 255), 3)
            else:
                if frame_counter > 0:
                    print("Yeux ouverts détectés")
                frame_counter = 0
                if alert_active:
                    pygame.mixer.music.stop()
                    alert_active = False
            
            # Affichage des valeurs
            cv2.putText(image, f"Oeil G: {left_eye_opening:.4f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(image, f"Oeil D: {right_eye_opening:.4f}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(image, f"Seuil: {EYE_CLOSED_THRESHOLD:.4f}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Affichage du compteur de frames
            if frame_counter > 0:
                cv2.putText(image, f"Frames: {frame_counter}/{EYE_AR_CONSEC_FRAMES}", (10, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Afficher l'image
        cv2.imshow('Debug Détecteur de Somnolence', image)
        
        # Sortie avec 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.quit()

if __name__ == "__main__":
    # Création des dossiers et fichiers nécessaires
    os.makedirs("data", exist_ok=True)
    
    # Vérification du fichier son
    if not os.path.exists("data/alarm.wav"):
        print("ATTENTION: Fichier d'alarme manquant. Veuillez ajouter un fichier 'alarm.wav' dans le dossier data/")
    else:
        main() 