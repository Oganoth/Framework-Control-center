import os
import logging
from typing import Dict, Any, Optional
from hardware_monitor import LibreHardwareMonitor

logger = logging.getLogger(__name__)

class HardwareManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialiser LibreHardwareMonitor
        try:
            self.monitor = LibreHardwareMonitor()
        except Exception as e:
            self.logger.error(f"Erreur fatale: Impossible d'initialiser LibreHardwareMonitor: {e}")
            raise
            
        # Initialiser les informations CPU
        self._cpu_info = self._get_cpu_info()
        
        # Vérifier la compatibilité AMD
        if not self._check_amd_compatibility():
            raise RuntimeError("Ce logiciel nécessite un processeur AMD Ryzen")
            
    def _check_amd_compatibility(self) -> bool:
        """Vérifie si le système utilise un processeur AMD"""
        try:
            cpu_info = self._cpu_info
            return "AMD" in cpu_info.get("manufacturer", "").upper() and "RYZEN" in cpu_info.get("name", "").upper()
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de compatibilité AMD: {e}")
            return False
            
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Récupère les informations du CPU via LibreHardwareMonitor"""
        try:
            for hardware in self.monitor.computer.Hardware:
                if str(hardware.HardwareType) == "Cpu":
                    hardware.Update()
                    
                    # Récupérer le nom complet du CPU
                    cpu_name = hardware.Name
                    
                    # Déterminer le modèle
                    model = "model_16"  # Par défaut Framework 16
                    cpu_name_lower = cpu_name.lower()
                    
                    if "7840hs" in cpu_name_lower:  # Framework 16 AMD
                        model = "model_16"
                    elif "7840u" in cpu_name_lower:  # Framework 13 AMD
                        model = "model_13_amd"
                    elif "7040u" in cpu_name_lower:  # Framework 13 AMD
                        model = "model_13_amd"
                    
                    logger.info(f"Processeur détecté: {cpu_name}")
                    logger.info(f"Modèle détecté: {model}")
                    
                    # Compter les cœurs et threads
                    cores = sum(1 for sensor in hardware.Sensors if str(sensor.SensorType) == "Clock" and "CPU Core #" in sensor.Name)
                    
                    return {
                        "manufacturer": "AMD",
                        "name": cpu_name,
                        "model": model,
                        "cores": cores,
                        "threads": cores * 2,  # Estimation raisonnable pour Ryzen
                        "base_clock": next((
                            sensor.Value 
                            for sensor in hardware.Sensors 
                            if str(sensor.SensorType) == "Clock" and "CPU Core #1" in sensor.Name
                        ), 3000),
                    }
                    
            raise Exception("Aucun CPU détecté")
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos CPU: {e}")
            return {
                "manufacturer": "AMD",  # Valeur par défaut
                "name": "AMD Ryzen",
                "model": "model_16",  # On met model_16 par défaut
                "cores": 8,
                "threads": 16,
                "base_clock": 3000,
            }
            
    def get_cpu_temp(self) -> float:
        """Récupère la température CPU"""
        try:
            temp = self.monitor.get_cpu_temp()
            if temp is not None:
                return temp
        except Exception as e:
            self.logger.error(f"Erreur lecture température CPU: {e}")
        return 0.0

    def get_system_metrics(self) -> Dict[str, Any]:
        """Récupère toutes les métriques système"""
        try:
            return self.monitor.get_system_metrics()
        except Exception as e:
            self.logger.error(f"Erreur récupération métriques: {e}")
            return {
                'cpu': {'temperature': 0.0, 'load': 0.0, 'power': 0.0, 'frequency': 0.0, 'total_load': 0.0, 'usage': 0.0},
                'igpu': {'temperature': 0.0, 'load': 0.0, 'memory': 0.0, 'frequency': 0.0, 'usage': 0.0},
                'dgpu': {'temperature': 0.0, 'load': 0.0, 'memory': 0.0, 'frequency': 0.0, 'usage': 0.0},
                'ram': {'used': 0.0, 'available': 0.0, 'total': 0.0, 'percent': 0.0, 'usage': 0.0}
            }
            
    @property
    def cpu_info(self) -> Dict[str, Any]:
        """Getter pour les informations CPU"""
        return self._cpu_info