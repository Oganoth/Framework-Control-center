import clr
import os
import logging
from typing import Dict, Optional, Any
import time

logger = logging.getLogger(__name__)

class LibreHardwareMonitor:
    def __init__(self):
        try:
            # Chemin vers le DLL
            dll_path = os.path.join(os.path.dirname(__file__), "libs", "LibreHardwareMonitorLib.dll")
            
            if not os.path.exists(dll_path):
                raise FileNotFoundError(f"LibreHardwareMonitorLib.dll non trouvé dans {dll_path}")
                
            # Chargement du DLL
            clr.AddReference(dll_path)
            
            from LibreHardwareMonitor.Hardware import Computer
            
            # Initialiser l'ordinateur
            self.computer = Computer()
            self.computer.IsCpuEnabled = True
            self.computer.IsGpuEnabled = True
            self.computer.IsMemoryEnabled = True
            self.computer.IsMotherboardEnabled = False
            self.computer.IsControllerEnabled = False
            self.computer.IsStorageEnabled = False
            self.computer.IsNetworkEnabled = False
            
            # Ouvrir la connexion
            self.computer.Open()
            logger.info("LibreHardwareMonitor initialisé avec succès")
            
            # Liste tous les capteurs disponibles au démarrage
            self._list_available_sensors()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de LibreHardwareMonitor: {e}")
            raise
            
    def _list_available_sensors(self) -> None:
        """Liste tous les capteurs disponibles pour le débogage"""
        try:
            for hardware in self.computer.Hardware:
                hardware.Update()  # Met à jour les valeurs
                for sensor in hardware.Sensors:
                    # On garde la mise à jour des valeurs mais on supprime les logs
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors du listage des capteurs: {e}")
            
    def update(self) -> None:
        """Met à jour toutes les valeurs"""
        try:
            for hardware in self.computer.Hardware:
                hardware.Update()
                for subhardware in hardware.SubHardware:
                    subhardware.Update()
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des capteurs: {e}")
            
    def get_system_metrics(self) -> Dict[str, Any]:
        """Retourne toutes les métriques système"""
        try:
            self.update()
            metrics = {
                'cpu': {
                    'temperature': 0.0,
                    'load': 0.0,
                    'power': 0.0,
                    'frequency': 0.0,
                    'total_load': 0.0,
                    'usage': 0.0
                },
                'igpu': {  # GPU intégré (780M)
                    'temperature': 0.0,
                    'load': 0.0,
                    'memory': 0.0,
                    'frequency': 0.0,
                    'usage': 0.0
                },
                'dgpu': {  # GPU dédié (7700S)
                    'temperature': 0.0,
                    'load': 0.0,
                    'memory': 0.0,
                    'frequency': 0.0,
                    'usage': 0.0
                },
                'ram': {
                    'used': 0.0,
                    'available': 0.0,
                    'total': 0.0,
                    'percent': 0.0,
                    'usage': 0.0
                }
            }
            
            for hardware in self.computer.Hardware:
                hardware_type = str(hardware.HardwareType)
                hardware_name = str(hardware.Name)
                
                if hardware_type == "Cpu":
                    for sensor in hardware.Sensors:
                        sensor_type = str(sensor.SensorType)
                        sensor_name = str(sensor.Name)
                        
                        if sensor_type == "Temperature" and "Tctl/Tdie" in sensor_name:
                            metrics['cpu']['temperature'] = round(float(sensor.Value), 1) if sensor.Value else 0.0
                        elif sensor_type == "Load" and "CPU Total" in sensor_name:
                            value = round(float(sensor.Value), 1) if sensor.Value else 0.0
                            metrics['cpu']['usage'] = value
                            metrics['cpu']['total_load'] = value
                        elif sensor_type == "Power" and "Package" in sensor_name:
                            metrics['cpu']['power'] = round(float(sensor.Value), 1) if sensor.Value else 0.0
                        elif sensor_type == "Clock" and "Core #1" in sensor_name:
                            metrics['cpu']['frequency'] = round(float(sensor.Value), 1) if sensor.Value else 0.0
                            
                elif hardware_type == "GpuAmd":
                    gpu_key = 'igpu' if "780M" in hardware_name else 'dgpu' if "7700S" in hardware_name else None
                    if gpu_key:
                        logger.debug(f"Traitement du GPU {hardware_name} ({gpu_key})")
                        for sensor in hardware.Sensors:
                            sensor_type = str(sensor.SensorType)
                            sensor_name = str(sensor.Name)
                            sensor_value = float(sensor.Value) if sensor.Value else 0.0
                            
                            logger.debug(f"  Capteur trouvé: {sensor_name} ({sensor_type}) = {sensor_value}")
                            
                            # Température GPU
                            if sensor_type == "Temperature":
                                if gpu_key == 'igpu' and "SoC" in sensor_name:
                                    metrics[gpu_key]['temperature'] = round(sensor_value, 1)
                                    logger.debug(f"  → Température iGPU SoC: {metrics[gpu_key]['temperature']}°C")
                                elif gpu_key == 'dgpu' and "GPU Core" in sensor_name:
                                    metrics[gpu_key]['temperature'] = round(sensor_value, 1)
                                    logger.debug(f"  → Température dGPU Core: {metrics[gpu_key]['temperature']}°C")
                            # Autres métriques GPU
                            elif sensor_type == "Load" and "GPU Core" in sensor_name:
                                value = round(sensor_value, 1)
                                metrics[gpu_key]['usage'] = value
                                metrics[gpu_key]['load'] = value
                                logger.debug(f"  → Utilisation GPU: {value}%")
                            elif sensor_type == "Clock" and "GPU Core" in sensor_name:
                                metrics[gpu_key]['frequency'] = round(sensor_value, 1)
                                logger.debug(f"  → Fréquence GPU: {metrics[gpu_key]['frequency']} MHz")
                            elif sensor_type == "SmallData" and "GPU Memory" in sensor_name:
                                metrics[gpu_key]['memory'] = round(sensor_value, 1)
                                logger.debug(f"  → Mémoire GPU: {metrics[gpu_key]['memory']} GB")
                                
                elif hardware_type == "Memory":
                    for sensor in hardware.Sensors:
                        if str(sensor.SensorType) == "Data":
                            if "Memory Used" in str(sensor.Name):
                                metrics['ram']['used'] = round(float(sensor.Value), 1) if sensor.Value else 0.0
                            elif "Memory Available" in str(sensor.Name):
                                metrics['ram']['available'] = round(float(sensor.Value), 1) if sensor.Value else 0.0
                    
                    if metrics['ram']['used'] > 0 and metrics['ram']['available'] > 0:
                        total = metrics['ram']['used'] + metrics['ram']['available']
                        metrics['ram']['total'] = total
                        usage = round((metrics['ram']['used'] / total) * 100, 1) if total > 0 else 0.0
                        metrics['ram']['usage'] = usage
                        metrics['ram']['percent'] = usage
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques: {e}")
            return {
                'cpu': {'temperature': 0.0, 'load': 0.0, 'power': 0.0, 'frequency': 0.0, 'total_load': 0.0, 'usage': 0.0},
                'igpu': {'temperature': 0.0, 'load': 0.0, 'memory': 0.0, 'frequency': 0.0, 'usage': 0.0},
                'dgpu': {'temperature': 0.0, 'load': 0.0, 'memory': 0.0, 'frequency': 0.0, 'usage': 0.0},
                'ram': {'used': 0.0, 'available': 0.0, 'total': 0.0, 'percent': 0.0, 'usage': 0.0}
            }
            
    def __del__(self):
        """Nettoyage à la destruction de l'objet"""
        try:
            if hasattr(self, 'computer'):
                self.computer.Close()
        except:
            pass