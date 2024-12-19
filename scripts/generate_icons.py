from PIL import Image
import os

def create_icons():
    """Crée les icônes manquantes à partir de logo.ico"""
    try:
        # Créer le dossier assets s'il n'existe pas
        if not os.path.exists("assets"):
            os.makedirs("assets")
            
        # Charger l'icône principale
        main_icon = Image.open("assets/logo.ico")
        
        # Créer les différentes versions
        icons = {
            "tray_icon.png": (32, 32),
            "error_icon.png": (16, 16),
            "info_icon.png": (16, 16)
        }
        
        for filename, size in icons.items():
            icon = main_icon.resize(size)
            icon.save(f"assets/{filename}")
            print(f"Created {filename}")
            
    except Exception as e:
        print(f"Error creating icons: {e}")

if __name__ == "__main__":
    create_icons() 