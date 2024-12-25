"""Hardware monitoring module for Framework laptops."""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any
import clr
import psutil
import wmi
from comtypes import GUID

from .models import HardwareMetrics
from .logger import logger
from .constants import (
    LIBS_DIR,
    HARDWARE_DLL_PATH,
    LHM_DOWNLOAD_URL,
    METRICS_CACHE_TTL,
    SENSOR_IDS
)

class HardwareMonitor:
    def __init__(self):
        self._setup_lhm()
        self.wmi = wmi.WMI()
        self._last_update = 0
        self._metrics_cache = None
        self._update_interval = METRICS_CACHE_TTL  # Utiliser la constante
        
        # Utiliser les identifiants des capteurs depuis les constantes
        self.sensor_ids = SENSOR_IDS
        
        # Identifier les GPUs disponibles
        self._scan_gpus()

    def _setup_lhm(self) -> None:
        """Setup LibreHardwareMonitor library."""
        if not HARDWARE_DLL_PATH.exists():
            self._download_lhm()
        
        try:
            # Add reference using absolute path
            dll_path = str(HARDWARE_DLL_PATH.absolute())
            logger.info(f"Loading LibreHardwareMonitor from: {dll_path}")
            clr.AddReference(dll_path)
            
            from LibreHardwareMonitor import Hardware
            
            # Create computer instance
            self.computer = Hardware.Computer()
            self.computer.IsCpuEnabled = True
            self.computer.IsGpuEnabled = True
            self.computer.IsMemoryEnabled = True
            self.computer.Open()
            
            # Do initial update
            for hardware in self.computer.Hardware:
                hardware.Update()
            
            logger.info("LibreHardwareMonitor initialized successfully")
            
        except Exception as e:
            logger.error("Error setting up LibreHardwareMonitor: %s", e)
            logger.error("Make sure .NET Framework 4.7.2 or later is installed")
            raise

    def _download_lhm(self) -> None:
        """Download and extract LibreHardwareMonitor files."""
        import requests
        from zipfile import ZipFile
        from io import BytesIO
        
        # Create libs directory if it doesn't exist
        LIBS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Download ZIP file
        logger.info("Downloading LibreHardwareMonitor...")
        try:
            response = requests.get(LHM_DOWNLOAD_URL)
            response.raise_for_status()
        except Exception as e:
            logger.error("Error downloading LibreHardwareMonitor: %s", e)
            raise
        
        # Extract required files
        try:
            with ZipFile(BytesIO(response.content)) as zip_file:
                # Extract all DLL and config files
                required_extensions = {'.dll', '.config', '.xml', '.pdb'}
                for file_info in zip_file.filelist:
                    file_ext = Path(file_info.filename).suffix.lower()
                    if file_ext in required_extensions:
                        target_path = LIBS_DIR / Path(file_info.filename).name
                        logger.debug("Extracting %s...", file_info.filename)
                        with zip_file.open(file_info.filename) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
            
            logger.info("LibreHardwareMonitor setup complete")
        except Exception as e:
            logger.error("Error extracting files: %s", e)
            raise

    def _scan_gpus(self) -> None:
        """Scan et identifie les GPUs disponibles."""
        try:
            self.igpu_hardware = None
            self.dgpu_hardware = None
            
            for hardware in self.computer.Hardware:
                if str(hardware.HardwareType) == "GpuAmd":
                    hardware_name = str(hardware.Name).lower()
                    hardware_id = str(hardware.Identifier).lower()
                    logger.debug(f"Found GPU: {hardware_name} (ID: {hardware_id})")
                    
                    # Détection plus précise des GPUs
                    if "780m" in hardware_name or "radeon(tm) 780m" in hardware_name.lower():
                        self.igpu_hardware = hardware
                        logger.info(f"Found iGPU: {hardware.Name}")
                        hardware.Update()  # Mise à jour initiale
                    elif "7700s" in hardware_name or "radeon(tm) rx 7700s" in hardware_name.lower():
                        self.dgpu_hardware = hardware
                        logger.info(f"Found dGPU: {hardware.Name}")
                        hardware.Update()  # Mise à jour initiale
            
            if not self.igpu_hardware:
                logger.warning("No iGPU (780M) found")
            if not self.dgpu_hardware:
                logger.warning("No dGPU (7700S) found")
                
        except Exception as e:
            logger.error(f"Error scanning GPUs: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _get_gpu_value(self, gpu_hardware: Any, sensor_type: str, sensor_name: str) -> Optional[float]:
        """Get sensor value from a specific GPU."""
        if not gpu_hardware:
            return None
            
        try:
            from LibreHardwareMonitor.Hardware import SensorType
            sensor_type_enum = getattr(SensorType, sensor_type, None)
            if not sensor_type_enum:
                return None
                
            gpu_hardware.Update()
            for sensor in gpu_hardware.Sensors:
                sensor_name_str = str(sensor.Name)
                logger.debug(f"GPU {gpu_hardware.Name} - {sensor_name_str}: {sensor.Value}")
                if (sensor.SensorType == sensor_type_enum and 
                    sensor_name in sensor_name_str):
                    value = sensor.Value
                    if value is not None:
                        return float(value)
            
            logger.debug(f"No matching sensor found for {sensor_name} in {gpu_hardware.Name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting GPU value: {e}")
            return None

    def _get_sensor_value(self, hw_type: str, sensor_type: str, sensor_name: str, gpu_type: Optional[str] = None) -> Optional[float]:
        """Get sensor value from LibreHardwareMonitor."""
        try:
            # Pour les GPUs, utiliser la fonction spécialisée
            if hw_type == "GpuAmd":
                if gpu_type == "Integrated":
                    return self._get_gpu_value(self.igpu_hardware, sensor_type, sensor_name)
                elif gpu_type == "Dedicated":
                    return self._get_gpu_value(self.dgpu_hardware, sensor_type, sensor_name)
                return None
            
            # Pour les autres types de hardware
            from LibreHardwareMonitor.Hardware import SensorType
            sensor_type_enum = getattr(SensorType, sensor_type, None)
            if not sensor_type_enum:
                logger.error(f"Invalid sensor type: {sensor_type}")
                return None
                
            for hardware in self.computer.Hardware:
                if str(hardware.HardwareType) == hw_type:
                    hardware.Update()
                    for sensor in hardware.Sensors:
                        if (sensor.SensorType == sensor_type_enum and 
                            sensor_name in str(sensor.Name)):
                            value = sensor.Value
                            if value is not None:
                                logger.debug(f"Found sensor value for {sensor.Name}: {value}")
                                return float(value)
                            else:
                                logger.debug(f"Sensor {sensor.Name} returned None")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting sensor value: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def get_metrics(self) -> HardwareMetrics:
        """Get current hardware metrics with caching."""
        current_time = time.time()
        
        # Vérifier le cache
        if (self._metrics_cache and 
            (current_time - self._last_update) < self._update_interval):
            return self._metrics_cache

        try:
            # Get CPU metrics
            cpu_temp = self._get_sensor_value(*self.sensor_ids['cpu_temp'])
            cpu_load = self._get_sensor_value(*self.sensor_ids['cpu_load'])
            if cpu_load is None:
                cpu_load = psutil.cpu_percent()
                logger.debug(f"Using psutil CPU load: {cpu_load}")

            # Get RAM usage
            ram_usage = psutil.virtual_memory().percent
            logger.debug(f"RAM usage: {ram_usage}%")

            # Get GPU metrics
            igpu_temp = self._get_sensor_value(*self.sensor_ids['igpu_temp'], gpu_type="Integrated")
            igpu_load = self._get_sensor_value(*self.sensor_ids['igpu_load'], gpu_type="Integrated")
            logger.debug(f"iGPU metrics - Temp: {igpu_temp}, Load: {igpu_load}")

            dgpu_temp = self._get_sensor_value(*self.sensor_ids['dgpu_temp'], gpu_type="Dedicated")
            dgpu_load = self._get_sensor_value(*self.sensor_ids['dgpu_load'], gpu_type="Dedicated")
            logger.debug(f"dGPU metrics - Temp: {dgpu_temp}, Load: {dgpu_load}")

            # Get battery info
            battery = psutil.sensors_battery()
            battery_percentage = int(battery.percent) if battery else 100
            is_charging = battery.power_plugged if battery else True
            logger.debug(f"Battery: {battery_percentage}%, Charging: {is_charging}")

            metrics = HardwareMetrics(
                cpu_temp=cpu_temp or 0.0,
                cpu_load=cpu_load,
                ram_usage=ram_usage,
                igpu_temp=igpu_temp,
                igpu_load=igpu_load,
                dgpu_temp=dgpu_temp,
                dgpu_load=dgpu_load,
                battery_percentage=battery_percentage,
                is_charging=is_charging
            )

            # Update cache
            self._metrics_cache = metrics
            self._last_update = current_time
            
            return metrics
            
        except Exception as e:
            logger.error("Error updating metrics: %s", e)
            import traceback
            logger.error("Traceback: %s", traceback.format_exc())
            # Return last cached metrics if available
            if self._metrics_cache:
                return self._metrics_cache
            # Return default metrics
            return HardwareMetrics()

    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, "computer"):
            self.computer.Close()