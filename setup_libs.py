import os
import requests
import zipfile
import logging

logger = logging.getLogger(__name__)

def setup_monitoring_libs():
    """Configure les bibliothèques nécessaires pour le monitoring"""
    try:
        # Créer le dossier libs s'il n'existe pas
        libs_dir = os.path.join(os.path.dirname(__file__), "libs")
        os.makedirs(libs_dir, exist_ok=True)
        
        # URLs des DLLs nécessaires
        lhm_url = "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v0.9.3/LibreHardwareMonitor-net472.zip"
        
        # Télécharger et extraire LibreHardwareMonitor
        lhm_zip = os.path.join(libs_dir, "lhm.zip")
        if not os.path.exists(os.path.join(libs_dir, "LibreHardwareMonitorLib.dll")):
            logger.info("Téléchargement de LibreHardwareMonitor...")
            response = requests.get(lhm_url)
            with open(lhm_zip, 'wb') as f:
                f.write(response.content)
            
            # Extraire les DLLs nécessaires
            with zipfile.ZipFile(lhm_zip) as z:
                for file in z.namelist():
                    if file.endswith('.dll'):
                        z.extract(file, libs_dir)
            
            # Nettoyer
            os.remove(lhm_zip)
            
        logger.info("Configuration des bibliothèques terminée")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration des bibliothèques: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_monitoring_libs() 