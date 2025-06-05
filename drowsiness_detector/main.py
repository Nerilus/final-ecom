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

# Indices des points de repère pour les yeux
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

# Paramètres de détection
EYE_AR_THRESH = 0.2  # Seuil pour détecter si l'œil est fermé
EYE_AR_CONSEC_FRAMES = 20  # Nombre de frames consécutives pour déclencher l'alerte

def calculate_ear(landmarks, eye_indices):
    """Calcule le ratio d'aspect de l'œil (EAR)"""
    points = []
    for i in eye_indices:
        point = [landmarks[i].x, landmarks[i].y]
        points.append(point)
    
    # Calcul des distances verticales
    v1 = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    v2 = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
    
    # Calcul de la distance horizontale
    h = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
    
    # Calcul du ratio
    ear = (v1 + v2) / (2.0 * h)
    return ear

def main():
    cap = cv2.VideoCapture(0)
    frame_counter = 0
    start_time = time.time()
    alert_active = False
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Échec de la capture de la caméra.")
            break
            
        # Conversion en RGB pour MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # Calcul de l'EAR pour chaque œil
            left_ear = calculate_ear(landmarks, LEFT_EYE)
            right_ear = calculate_ear(landmarks, RIGHT_EYE)
            
            # Moyenne des deux yeux
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Dessin des yeux sur l'image
            for eye in [LEFT_EYE, RIGHT_EYE]:
                for i in eye:
                    pt = landmarks[i]
                    x = int(pt.x * image.shape[1])
                    y = int(pt.y * image.shape[0])
                    cv2.circle(image, (x, y), 1, (0, 255, 0), -1)
            
            # Vérification de la somnolence
            if avg_ear < EYE_AR_THRESH:
                frame_counter += 1
                if frame_counter >= EYE_AR_CONSEC_FRAMES and not alert_active:
                    # Déclenchement de l'alerte
                    pygame.mixer.music.play(-1)  # -1 pour jouer en boucle
                    alert_active = True
                    
                    # Enregistrement de l'événement
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open("data/alerts.log", "a") as f:
                        f.write(f"{timestamp}: Somnolence détectée\n")
            else:
                frame_counter = 0
                if alert_active:
                    pygame.mixer.music.stop()
                    alert_active = False
            
            # Affichage du ratio EAR
            cv2.putText(image, f"EAR: {avg_ear:.2f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Affichage du temps écoulé
        elapsed_time = int(time.time() - start_time)
        cv2.putText(image, f"Temps: {elapsed_time}s", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Affichage de l'image
        cv2.imshow('Détecteur de Somnolence', image)
        
        # Sortie avec 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.quit()

if __name__ == "__main__":
    # Création du dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    
    # Vérification du fichier son
    if not os.path.exists("data/alarm.wav"):
        print("ATTENTION: Fichier d'alarme manquant. Veuillez ajouter un fichier 'alarm.wav' dans le dossier data/")
    else:
        main() 