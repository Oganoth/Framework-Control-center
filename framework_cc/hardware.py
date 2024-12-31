"""Hardware monitoring module for Framework laptops."""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import clr
import psutil

from .models import HardwareMetrics
from .logger import logger
from .constants import HARDWARE_DLL_PATH, CONFIGS_DIR, SENSOR_IDS

class HardwareMonitor:
    """Hardware monitoring for Framework laptops."""
    
    def __init__(self) -> None:
        """Initialize hardware monitor."""
        self._metrics_cache = None
        self._last_update = 0
        self._update_interval = 1.0  # 1 second
        self.computer = None
        self.igpu_hardware = None
        self.dgpu_hardware = None
        self.sensor_ids = SENSOR_IDS
        self.json_file_path = CONFIGS_DIR / "sensors.json"
        
        # Setup LibreHardwareMonitor
        self._setup_lhm()
        
        # Initial sensors update
        self._update_sensors()

    def _download_lhm(self) -> None:
        """Download and extract LibreHardwareMonitor DLL."""
        import requests
        import zipfile
        import io
        
        logger.info("Downloading LibreHardwareMonitor...")
        url = "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/latest/download/LibreHardwareMonitor-net472.zip"
        
        try:
            # Create libs directory if it doesn't exist
            HARDWARE_DLL_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Download and extract
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                # Extract all DLL files
                for file in zip_ref.namelist():
                    if file.endswith(".dll"):
                        logger.info(f"Extracting: {file}")
                        zip_ref.extract(file, HARDWARE_DLL_PATH.parent)
                        # If this is the main DLL, rename it
                        if file.endswith("LibreHardwareMonitorLib.dll"):
                            extracted_path = HARDWARE_DLL_PATH.parent / file
                            extracted_path.rename(HARDWARE_DLL_PATH)
            
            logger.info(f"LibreHardwareMonitor files extracted to: {HARDWARE_DLL_PATH.parent}")
            
        except Exception as e:
            logger.error(f"Error downloading LibreHardwareMonitor: {e}")
            raise

    def _setup_lhm(self) -> None:
        """Setup LibreHardwareMonitor library."""
        if not HARDWARE_DLL_PATH.exists():
            self._download_lhm()
        
        try:
            # Add reference using absolute path
            dll_path = str(HARDWARE_DLL_PATH.absolute())
            logger.info(f"Loading LibreHardwareMonitor from: {dll_path}")
            clr.AddReference(dll_path)
            
            from LibreHardwareMonitor.Hardware import Computer
            
            # Create computer instance with all features enabled
            self.computer = Computer()
            self.computer.IsCpuEnabled = True
            self.computer.IsGpuEnabled = True
            self.computer.IsMemoryEnabled = True
            self.computer.IsMotherboardEnabled = True
            self.computer.IsControllerEnabled = True
            self.computer.IsNetworkEnabled = True
            self.computer.IsStorageEnabled = True
            
            # Open computer
            self.computer.Open()
            
            # Update all hardware
            for hardware in self.computer.Hardware:
                hardware.Update()
                for subHardware in hardware.SubHardware:
                    subHardware.Update()
            
            # Log all available sensors for debugging
            logger.info("Available hardware sensors:")
            for hardware in self.computer.Hardware:
                logger.info(f"Hardware: {hardware.Name}")
                for sensor in hardware.Sensors:
                    logger.info(f"  - {sensor.Name} ({sensor.SensorType}): {sensor.Value}")
            
            logger.info("LibreHardwareMonitor initialized successfully")
            
        except Exception as e:
            logger.error("Error setting up LibreHardwareMonitor: %s", e)
            logger.error("Make sure .NET Framework 4.7.2 or later is installed")
            raise

    def _update_sensors(self) -> None:
        """Update all hardware sensors and write to JSON file."""
        try:
            if not hasattr(self, 'computer'):
                return

            # Force update all hardware
            for hardware in self.computer.Hardware:
                hardware.Update()
                for subHardware in hardware.SubHardware:
                    subHardware.Update()

            # Collect sensor data
            sensors_data = []
            for hardware in self.computer.Hardware:
                for sensor in hardware.Sensors:
                    if sensor.Value is not None:
                        sensors_data.append({
                            "Name": sensor.Name,
                            "Hardware": hardware.Name,
                            "Type": str(sensor.SensorType),
                            "Value": float(sensor.Value)
                        })

            # Write to JSON file
            self.json_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(sensors_data, json_file, indent=4, ensure_ascii=False)

            # Log update
            logger.debug(f"Sensors data updated in {self.json_file_path}")

            # Check file size and recreate if too large
            if self.json_file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                self.json_file_path.unlink()
                logger.warning("Sensors file too large, recreating...")
                self._update_sensors()

        except Exception as e:
            logger.error(f"Error updating sensors: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _get_sensor_value(self, hardware_type: str, sensor_type: str, sensor_name: str, gpu_type: str = None) -> Optional[float]:
        """Get sensor value from JSON file."""
        try:
            # Force update sensors before reading
            self._update_sensors()
            
            # Read the JSON file
            if not self.json_file_path.exists():
                return None
            
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                sensors_data = json.load(f)
            
            # Find the matching sensor
            for sensor in sensors_data:
                # Pour les GPU intégrés, vérifie les deux modèles
                if gpu_type == "Integrated":
                    if ("760M" in sensor["Hardware"] or "780M" in sensor["Hardware"]) and sensor_type == sensor["Type"] and sensor_name == sensor["Name"]:
                        logger.debug(f"Found iGPU sensor: {sensor}")
                        return sensor["Value"]
                # Pour les autres capteurs, comportement normal
                elif hardware_type in sensor["Hardware"] and sensor_type == sensor["Type"] and sensor_name == sensor["Name"]:
                    if hardware_type == "Cpu":
                        logger.debug(f"Found CPU sensor: {sensor}")
                    elif hardware_type == "Memory":
                        logger.debug(f"Found RAM sensor: {sensor}")
                    elif gpu_type == "Dedicated":
                        logger.debug(f"Found dGPU sensor: {sensor}")
                    return sensor["Value"]
            
            logger.debug(f"No sensor found for {hardware_type}/{sensor_type}/{sensor_name} (gpu_type={gpu_type})")
            return None
            
        except Exception as e:
            logger.error(f"Error getting sensor value: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def get_metrics(self) -> HardwareMetrics:
        """Get current hardware metrics with caching."""
        current_time = time.time()
        
        # Check cache
        if (self._metrics_cache and 
            (current_time - self._last_update) < self._update_interval):
            return self._metrics_cache

        try:
            # Update sensors
            self._update_sensors()
            
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
            battery_time = battery.secsleft if battery and battery.secsleft > 0 else 0
            logger.debug(f"Battery: {battery_percentage}%, Charging: {is_charging}")

            metrics = HardwareMetrics(
                cpu_temp=cpu_temp or 0.0,
                cpu_load=cpu_load or 0.0,
                ram_usage=ram_usage,
                igpu_temp=igpu_temp or 0.0,
                igpu_load=igpu_load or 0.0,
                dgpu_temp=dgpu_temp or 0.0,
                dgpu_load=dgpu_load or 0.0,
                battery_percentage=battery_percentage,
                battery_time_remaining=battery_time / 60 if battery_time > 0 else 0.0,
                is_charging=is_charging
            )
            
            # Update cache
            self._metrics_cache = metrics
            self._last_update = current_time
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._metrics_cache if self._metrics_cache else HardwareMetrics()

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if hasattr(self, 'computer'):
                self.computer.Close()
            if self.json_file_path.exists():
                self.json_file_path.unlink()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")