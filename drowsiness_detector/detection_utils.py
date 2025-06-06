import numpy as np

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
MOUTH_OPEN_THRESHOLD = 0.4
HEAD_ROTATION_THRESHOLD = 0.2
HEAD_TILT_THRESHOLD = 0.1
EYES_CLOSED_TIME_THRESHOLD = 20.0
PHONE_DETECTION_THRESHOLD = 5.0

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
    
    vertical_distance = abs(top.y - bottom.y)
    horizontal_distance = abs(left.x - right.x)
    
    if horizontal_distance == 0:
        return 0, 0
    
    mar = vertical_distance / horizontal_distance
    return mar, vertical_distance

def check_head_position(landmarks):
    """Vérifie la position de la tête"""
    nose = landmarks[NOSE_TIP]
    left_ear = landmarks[LEFT_EAR]
    right_ear = landmarks[RIGHT_EAR]
    forehead = landmarks[FOREHEAD]
    chin = landmarks[CHIN]
    left_temple = landmarks[LEFT_TEMPLE]
    right_temple = landmarks[RIGHT_TEMPLE]
    
    ear_diff = abs(left_ear.x - right_ear.x)
    temple_diff = abs(left_temple.x - right_temple.x)
    rotation = (ear_diff + temple_diff) / 2
    
    vertical_angle = abs(forehead.y - chin.y)
    
    head_state = {
        'turned': False,
        'tilted': False,
        'direction_h': None,
        'direction_v': None
    }
    
    if rotation > HEAD_ROTATION_THRESHOLD:
        head_state['turned'] = True
        head_state['direction_h'] = "gauche" if left_ear.x > right_ear.x else "droite"
    
    if vertical_angle > HEAD_TILT_THRESHOLD:
        head_state['tilted'] = True
        head_state['direction_v'] = "bas" if nose.y > (forehead.y + chin.y)/2 else "haut"
    
    return head_state

def detect_phone_usage(hand_landmarks, image_height, image_width):
    """Détecte si la main tient un téléphone"""
    if not hand_landmarks:
        return False
    
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    middle_tip = hand_landmarks.landmark[12]
    ring_tip = hand_landmarks.landmark[16]
    pinky_tip = hand_landmarks.landmark[20]
    
    thumb = np.array([thumb_tip.x * image_width, thumb_tip.y * image_height])
    index = np.array([index_tip.x * image_width, index_tip.y * image_height])
    middle = np.array([middle_tip.x * image_width, middle_tip.y * image_height])
    ring = np.array([ring_tip.x * image_width, ring_tip.y * image_height])
    pinky = np.array([pinky_tip.x * image_width, pinky_tip.y * image_height])
    
    distances = [
        np.linalg.norm(thumb - index),
        np.linalg.norm(index - middle),
        np.linalg.norm(middle - ring),
        np.linalg.norm(ring - pinky)
    ]
    
    avg_distance = np.mean(distances)
    max_distance = np.max(distances)
    
    fingers_close = avg_distance < image_width * 0.15
    fingers_aligned = max_distance < image_width * 0.25
    
    return fingers_close and fingers_aligned

def determine_alert_level(eyes_closed_time, is_yawning, head_state, phone_detected_time):
    """Détermine le niveau d'alerte"""
    danger_count = 0
    
    if eyes_closed_time > EYES_CLOSED_TIME_THRESHOLD * 0.8:
        danger_count += 2
    elif eyes_closed_time > EYES_CLOSED_TIME_THRESHOLD * 0.5:
        danger_count += 1
    
    if is_yawning:
        danger_count += 1
    
    if head_state['turned'] and head_state['tilted']:
        danger_count += 2
    elif head_state['turned'] or head_state['tilted']:
        danger_count += 1
    
    if phone_detected_time > PHONE_DETECTION_THRESHOLD:
        danger_count += 3
    elif phone_detected_time > 0:
        danger_count += 1
    
    if danger_count >= 3:
        return 'DANGER'
    elif danger_count >= 1:
        return 'WARNING'
    return 'NORMAL' 