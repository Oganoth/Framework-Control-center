"""Display management module for Framework laptops."""

import asyncio
import subprocess
from typing import Optional
import win32api
import win32con
import pywintypes
import psutil
import time

from .logger import logger

class DisplayManager:
    def __init__(self):
        """Initialize display manager."""
        self._current_device = win32api.EnumDisplayDevices(None, 0).DeviceName

    async def set_brightness(self, value: int) -> None:
        """Set display brightness."""
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
            await process.communicate()
            
        except Exception as e:
            logger.error(f"Error setting brightness: {e}")
            raise

    async def set_refresh_rate(self, mode: str, max_rate: str) -> None:
        """Set display refresh rate."""
        try:
            # Valider le mode
            mode = mode.lower()
            if mode not in ["auto", "60", "165"]:
                logger.error(f"Invalid refresh rate mode: {mode}")
                raise ValueError("Invalid refresh rate mode")

            # Valider le taux maximum
            if max_rate not in ["60", "165"]:
                logger.error(f"Invalid max refresh rate: {max_rate}")
                raise ValueError("Invalid max refresh rate")

            # Si le mode est auto, détecter l'alimentation
            if mode == "auto":
                battery = psutil.sensors_battery()
                is_plugged = battery.power_plugged if battery else True
                target_rate = int(max_rate if is_plugged else "60")
                logger.info(f"Auto mode: Power {'plugged' if is_plugged else 'unplugged'}, setting to {target_rate}Hz")
            else:
                target_rate = int(mode)
            
            # Obtenir les paramètres d'affichage actuels
            current_settings = win32api.EnumDisplaySettings(self._current_device, win32con.ENUM_CURRENT_SETTINGS)
            
            # Chercher un mode correspondant
            i = 0
            found = False
            while True:
                try:
                    mode = win32api.EnumDisplaySettings(self._current_device, i)
                    if (mode.PelsWidth == current_settings.PelsWidth and
                        mode.PelsHeight == current_settings.PelsHeight and
                        mode.BitsPerPel == current_settings.BitsPerPel and
                        mode.DisplayFrequency == target_rate):
                        
                        # Appliquer le nouveau taux
                        mode.Fields = win32con.DM_DISPLAYFREQUENCY
                        result = win32api.ChangeDisplaySettings(mode, 0)
                        
                        if result == win32con.DISP_CHANGE_SUCCESSFUL:
                            logger.info(f"Successfully set refresh rate to {target_rate}Hz")
                            found = True
                            break
                        else:
                            logger.error(f"Failed to change display settings, code: {result}")
                            raise RuntimeError(f"Failed to change display settings, code: {result}")
                    
                    i += 1
                    
                except pywintypes.error:
                    break
            
            if not found:
                logger.error(f"Could not find display mode with {target_rate}Hz")
                raise ValueError(f"Could not find display mode with {target_rate}Hz")
            
        except Exception as e:
            logger.error(f"Error setting refresh rate: {e}")
            raise