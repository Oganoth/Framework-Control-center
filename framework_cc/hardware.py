"""Hardware monitoring module for Framework laptops."""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading

import clr
import psutil

from .models import HardwareMetrics
from .logger import logger
from .constants import HARDWARE_DLL_PATH, CONFIGS_DIR, SENSOR_IDS, SENSOR_IDS_16_AMD, SENSOR_IDS_13_INTEL, SENSOR_IDS_13_AMD

class HardwareMonitor:
    """Hardware monitoring for Framework laptops."""
    
    def __init__(self, model: str = None) -> None:
        """Initialize hardware monitor."""
        self._metrics_cache = None
        self._last_update = 0
        self._update_interval = 1.0  # Default to 1 second, will be updated from config
        self.computer = None
        self.igpu_hardware = None
        self.dgpu_hardware = None
        
        # Select sensor configuration based on model
        if model == "16_AMD":
            logger.info("Using Framework 16 AMD sensor configuration")
            self.sensor_ids = SENSOR_IDS_16_AMD
        elif model == "13_INTEL":
            logger.info("Using Framework 13 Intel sensor configuration")
            self.sensor_ids = SENSOR_IDS_13_INTEL
        else:  # Default to 13_AMD
            logger.info("Using Framework 13 AMD sensor configuration")
            self.sensor_ids = SENSOR_IDS_13_AMD
            
        self.json_file_path = CONFIGS_DIR / "sensors.json"
        
        # Setup LibreHardwareMonitor
        self._setup_lhm()
        
        # Start continuous sensor updates in a separate thread
        self._stop_update = False
        self._update_thread = threading.Thread(target=self._continuous_update, daemon=True)
        self._update_thread.start()

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
                    if "GPU" in hardware.Name or "Radeon" in hardware.Name:
                        logger.info(f"    Full sensor info: Hardware={hardware.Name}, Type={sensor.SensorType}, Value={sensor.Value}")
            
            logger.info("LibreHardwareMonitor initialized successfully")
            
        except Exception as e:
            logger.error("Error setting up LibreHardwareMonitor: %s", e)
            logger.error("Make sure .NET Framework 4.7.2 or later is installed")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            
            # Log all sensors for debugging
            logger.debug("All available sensors:")
            for sensor in sensors_data:
                logger.debug(f"  {sensor['Hardware']} - {sensor['Name']} ({sensor['Type']}): {sensor['Value']}")
            
            # Find the matching sensor
            for sensor in sensors_data:
                # Convert sensor type to match expected format
                current_type = sensor["Type"].split('.')[-1]  # Extract last part of type string
                
                # Log the comparison for debugging
                logger.debug(f"Comparing - Looking for: {hardware_type}/{sensor_type}/{sensor_name}")
                logger.debug(f"           Found: {sensor['Hardware']}/{current_type}/{sensor['Name']}")
                
                # Direct match for exact hardware name, type and sensor name
                if (sensor["Hardware"] == hardware_type and 
                    current_type.lower() == sensor_type.lower() and 
                    sensor["Name"] == sensor_name):
                    logger.debug(f"Found exact match sensor: {sensor}")
                    return sensor["Value"]
                
                # Special case for CPU sensors
                if hardware_type == "Cpu" and "CPU" in sensor["Hardware"]:
                    if current_type.lower() == sensor_type.lower() and sensor["Name"].lower() == sensor_name.lower():
                        logger.debug(f"Found CPU sensor: {sensor}")
                        return sensor["Value"]
                
                # Special case for GPU sensors
                if hardware_type in sensor["Hardware"]:
                    if current_type.lower() == sensor_type.lower() and sensor["Name"] == sensor_name:
                        logger.debug(f"Found GPU sensor: {sensor}")
                        return sensor["Value"]
            
            logger.debug(f"No sensor found for {hardware_type}/{sensor_type}/{sensor_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting sensor value: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _continuous_update(self) -> None:
        """Continuously update sensors in a separate thread."""
        while not self._stop_update:
            try:
                self._update_sensors()
                time.sleep(self._update_interval)
            except Exception as e:
                logger.error(f"Error in continuous update: {e}")
                time.sleep(1)  # Wait a bit longer on error

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self._stop_update = True
            if hasattr(self, '_update_thread'):
                self._update_thread.join(timeout=1)
            if hasattr(self, 'computer'):
                self.computer.Close()
            if self.json_file_path.exists():
                self.json_file_path.unlink()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def get_metrics(self) -> HardwareMetrics:
        """Get current hardware metrics from sensors.json."""
        try:
            if not self.json_file_path.exists():
                return HardwareMetrics()

            with open(self.json_file_path, "r", encoding="utf-8") as f:
                sensors_data = json.load(f)

            # Initialize metrics with default values
            metrics = {
                'cpu_temp': 0.0,
                'cpu_load': 0.0,
                'ram_usage': 0.0,
                'igpu_temp': 0.0,
                'igpu_load': 0.0,
                'dgpu_temp': 0.0,
                'dgpu_load': 0.0
            }

            # Process CPU metrics for AMD processors
            cpu_loads = []
            for sensor in sensors_data:
                if "AMD Ryzen" in sensor["Hardware"]:
                    if sensor["Type"] == "Load":
                        if "CPU Core" in sensor["Name"]:
                            cpu_loads.append(sensor["Value"])
                        elif sensor["Name"] == "CPU Total":
                            metrics['cpu_load'] = sensor["Value"]
                    elif sensor["Type"] == "Temperature":
                        if sensor["Name"] == "Core (Tctl/Tdie)":
                            metrics['cpu_temp'] = sensor["Value"]

            # Use average core load if total is not available
            if metrics['cpu_load'] == 0.0 and cpu_loads:
                metrics['cpu_load'] = sum(cpu_loads) / len(cpu_loads)

            # Process RAM metrics
            for sensor in sensors_data:
                if sensor["Hardware"] == "Generic Memory" and sensor["Type"] == "Load":
                    if sensor["Name"] == "Memory":
                        metrics['ram_usage'] = sensor["Value"]

            # Process GPU metrics
            for sensor in sensors_data:
                # Integrated GPU (780M)
                if "AMD Radeon(TM) 780M" in sensor["Hardware"]:
                    if sensor["Type"] == "Temperature" and sensor["Name"] == "GPU VR SoC":
                        metrics['igpu_temp'] = sensor["Value"]
                    elif sensor["Type"] == "Load" and sensor["Name"] == "D3D 3D":
                        metrics['igpu_load'] = sensor["Value"]
                    # Fallback to CPU temp if GPU temp not available (for 13_AMD)
                    if metrics['igpu_temp'] == 0.0:
                        metrics['igpu_temp'] = metrics['cpu_temp']
                
                # Discrete GPU (7700S) - for 16_AMD
                elif "AMD Radeon(TM) RX 7700S" in sensor["Hardware"]:
                    if sensor["Type"] == "Temperature" and sensor["Name"] == "GPU Core":
                        metrics['dgpu_temp'] = sensor["Value"]
                    elif sensor["Type"] == "Load" and sensor["Name"] == "GPU Core":
                        metrics['dgpu_load'] = sensor["Value"]

            # Get battery info
            try:
                battery = psutil.sensors_battery()
                battery_percentage = int(battery.percent) if battery else 100
                is_charging = battery.power_plugged if battery else True
                battery_time = battery.secsleft if battery and battery.secsleft > 0 else 0
            except Exception as e:
                logger.error(f"Error getting battery info: {e}")
                battery_percentage = 100
                is_charging = True
                battery_time = 0

            return HardwareMetrics(
                cpu_temp=metrics['cpu_temp'],
                cpu_load=metrics['cpu_load'],
                ram_usage=metrics['ram_usage'],
                igpu_temp=metrics['igpu_temp'],
                igpu_load=metrics['igpu_load'],
                dgpu_temp=metrics['dgpu_temp'],
                dgpu_load=metrics['dgpu_load'],
                battery_percentage=battery_percentage,
                battery_time_remaining=battery_time / 60 if battery_time > 0 else 0.0,
                is_charging=is_charging
            )

        except Exception as e:
            logger.error(f"Error getting metrics from sensors.json: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return HardwareMetrics()

    def set_update_interval(self, interval_ms: int) -> None:
        """Update the sensor update interval."""
        self._update_interval = interval_ms / 1000.0  # Convert ms to seconds