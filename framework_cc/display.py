"""Display management module for Framework laptops."""

import asyncio
import subprocess
from typing import Optional, Dict, List, Tuple
import win32api
import win32con
import pywintypes
import psutil
import time
from pathlib import Path

from .logger import logger
from .models import LaptopModel

class DisplayManager:
    """Display manager for Framework laptops with improved error handling."""
    
    # Valid refresh rates per model
    VALID_RATES: Dict[str, List[str]] = {
        "16_AMD": ["60", "165"],
        "13_AMD": ["60", "120"],
        "13_INTEL": ["60", "120"]
    }

    def __init__(self, model: Optional[LaptopModel] = None):
        """Initialize display manager.
        
        Args:
            model: The laptop model information
        """
        self._current_device = win32api.EnumDisplayDevices(None, 0).DeviceName
        self.model = model
        
        # Map full model names to profile keys
        model_map = {
            "Framework 16 AMD": "16_AMD",
            "Framework 13 AMD": "13_AMD",
            "Framework 13 Intel": "13_INTEL"
        }
        
        # Get model name and map it to the correct key
        model_name = model.name if model else ""
        model_key = model_map.get(model_name, "")
        
        # Get valid rates for the model
        self._valid_rates = self.VALID_RATES.get(model_key, ["60"])
        
        logger.info(f"Initialized DisplayManager for model: {model_name if model else 'Unknown'}")
        logger.info(f"Model key: {model_key}, Valid refresh rates: {self._valid_rates}")

    async def set_brightness(self, value: int) -> bool:
        """Set display brightness with improved error handling.
        
        Args:
            value: Brightness value (0-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure value is between 0 and 100
            value = max(0, min(100, value))
            
            # Use PowerShell to set brightness with hidden window
            cmd = f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{value})'
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = await asyncio.create_subprocess_exec(
                'powershell',
                '-WindowStyle', 'Hidden',
                '-NonInteractive',
                '-NoProfile',
                '-Command', cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                startupinfo=startupinfo
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to set brightness: {stderr.decode() if stderr else 'Unknown error'}")
                return False
                
            logger.info(f"Successfully set brightness to {value}%")
            return True
            
        except Exception as e:
            logger.error(f"Error setting brightness: {e}")
            return False

    def _get_current_display_settings(self) -> Tuple[int, int, int, int]:
        """Get current display settings.
        
        Returns:
            Tuple[int, int, int, int]: width, height, bits_per_pixel, refresh_rate
        """
        try:
            settings = win32api.EnumDisplaySettings(self._current_device, win32con.ENUM_CURRENT_SETTINGS)
            return (
                settings.PelsWidth,
                settings.PelsHeight,
                settings.BitsPerPel,
                settings.DisplayFrequency
            )
        except Exception as e:
            logger.error(f"Error getting current display settings: {e}")
            raise

    async def set_refresh_rate(self, mode: str, max_rate: str) -> bool:
        """Set display refresh rate with improved validation and error handling.
        
        Args:
            mode: Refresh rate mode ("auto" or specific rate)
            max_rate: Maximum refresh rate to use in auto mode
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate mode and max_rate
            mode = mode.lower()
            valid_rates = ["auto"] + self._valid_rates
            
            if mode not in valid_rates:
                logger.error(f"Invalid refresh rate mode: {mode}")
                return False

            if max_rate not in self._valid_rates:
                logger.error(f"Invalid max refresh rate: {max_rate}")
                return False

            # If auto mode, detect power source
            if mode == "auto":
                battery = psutil.sensors_battery()
                is_plugged = battery.power_plugged if battery else True
                target_rate = int(max_rate if is_plugged else "60")
                logger.info(f"Auto mode: Power {'plugged' if is_plugged else 'unplugged'}, setting to {target_rate}Hz")
            else:
                target_rate = int(mode)
            
            # Get current display settings
            try:
                width, height, bits_per_pixel, _ = self._get_current_display_settings()
            except Exception as e:
                logger.error(f"Failed to get current display settings: {e}")
                return False

            # Search for matching mode
            i = 0
            found = False
            while True:
                try:
                    mode = win32api.EnumDisplaySettings(self._current_device, i)
                    if (mode.PelsWidth == width and
                        mode.PelsHeight == height and
                        mode.BitsPerPel == bits_per_pixel and
                        mode.DisplayFrequency == target_rate):
                        
                        # Apply new rate
                        mode.Fields = win32con.DM_DISPLAYFREQUENCY
                        result = win32api.ChangeDisplaySettings(mode, 0)
                        
                        if result == win32con.DISP_CHANGE_SUCCESSFUL:
                            logger.info(f"Successfully set refresh rate to {target_rate}Hz")
                            found = True
                            break
                        else:
                            logger.error(f"Failed to change display settings, code: {result}")
                            return False
                    
                    i += 1
                    
                except pywintypes.error:
                    break
            
            if not found:
                logger.error(f"Could not find display mode with {target_rate}Hz")
                return False

            return True
            
        except Exception as e:
            logger.error(f"Error setting refresh rate: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Display manager cleanup complete")