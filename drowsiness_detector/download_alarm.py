import urllib.request
import os

def download_alarm():
    # URL d'un son d'alarme libre de droits (nouvelle source)
    url = "https://github.com/opencv/opencv/raw/4.x/samples/data/alarm.wav"
    output_path = "data/alarm.wav"
    
    # Création du dossier data si nécessaire
    os.makedirs("data", exist_ok=True)
    
    try:
        print("Téléchargement du fichier audio d'alarme...")
        urllib.request.urlretrieve(url, output_path)
        print(f"Fichier audio téléchargé avec succès dans {output_path}")
    except Exception as e:
        print(f"Erreur lors du téléchargement : {str(e)}")
        print("Veuillez télécharger manuellement un fichier audio 'alarm.wav' et le placer dans le dossier data/")

if __name__ == "__main__":
    download_alarm() 