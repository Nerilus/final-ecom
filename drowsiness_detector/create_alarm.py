import numpy as np
from scipy.io import wavfile
import os

def create_alarm():
    # Paramètres du son
    sample_rate = 44100  # Hz
    duration = 1.0  # secondes
    frequency = 440.0  # Hz (note La)
    
    # Création du signal
    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * frequency * t)
    
    # Ajout d'une enveloppe pour éviter les clics
    envelope = np.ones_like(signal)
    attack = int(0.1 * sample_rate)
    release = int(0.1 * sample_rate)
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[-release:] = np.linspace(1, 0, release)
    signal = signal * envelope
    
    # Normalisation
    signal = np.int16(signal * 32767)
    
    # Création du dossier data si nécessaire
    os.makedirs("data", exist_ok=True)
    
    # Sauvegarde du fichier
    output_path = "data/alarm.wav"
    wavfile.write(output_path, sample_rate, signal)
    print(f"Fichier audio créé avec succès dans {output_path}")

if __name__ == "__main__":
    create_alarm() 