"""Windows Power Plan Management for Framework Laptops.

This module handles the creation, installation, and management of custom power plans
for Framework laptops. It creates three distinct power plans optimized for different
use cases:
- Framework-Silent: Maximum battery life
- Framework-Balanced: Good compromise between battery and performance
- Framework-Boost: Maximum performance
"""

import logging
import subprocess
import asyncio
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys
import winreg
import ctypes
from ctypes import windll, create_unicode_buffer, byref, c_uint32

from .models import LaptopModel, PowerProfile
from .utils import get_resource_path
from .constants import RYZENADJ_PARAMS

logger = logging.getLogger(__name__)

# Power overlay GUIDs for Windows 11
POWER_OVERLAYS = {
    "Framework-Silent": "961cc777-2547-4f9d-8174-7d86181b8a7a",
    "Framework-Balanced": "3af9b8d9-7c97-431d-ad78-34a8bfea439f",
    "Framework-Boost": "ded574b5-45a0-4f42-8737-46345c09c238"
}

# Power settings for each profile
POWER_SETTINGS = {
    "Framework-Silent": {
        "processor_performance_increase_threshold": 90,
        "processor_performance_decrease_threshold": 80,
        "processor_performance_core_parking_min_cores": 25,
        "processor_performance_core_parking_max_cores": 100,
        "processor_idle_disable": 0,
        "processor_performance_boost_policy": 0,  # Disabled
        "system_cooling_policy": 1,  # Passive
        "processor_performance_increase_policy": 0,  # Gradual
        "processor_performance_decrease_policy": 0,  # Gradual
        "processor_idle_time_check": 50000,
        "processor_performance_history_count": 20,
        "processor_duty_cycling": 1,  # Enable duty cycling
        "processor_idle_state_maximum": 2,  # Deep idle states allowed
        "standby_budget_percent": 70,  # More aggressive standby
        "energysaver_brightness": 30,
        "energysaver_battery_threshold": 20,
    },
    "Framework-Balanced": {
        "processor_performance_increase_threshold": 60,
        "processor_performance_decrease_threshold": 40,
        "processor_performance_core_parking_min_cores": 50,
        "processor_performance_core_parking_max_cores": 100,
        "processor_idle_disable": 0,
        "processor_performance_boost_policy": 2,  # Aggressive
        "system_cooling_policy": 0,  # Balanced
        "processor_performance_increase_policy": 2,  # Medium
        "processor_performance_decrease_policy": 1,  # Medium
        "processor_idle_time_check": 30000,
        "processor_performance_history_count": 30,
        "processor_duty_cycling": 0,  # Disable duty cycling
        "processor_idle_state_maximum": 1,  # Moderate idle states
        "standby_budget_percent": 50,  # Balanced standby
        "energysaver_brightness": 50,
        "energysaver_battery_threshold": 15,
    },
    "Framework-Boost": {
        "processor_performance_increase_threshold": 30,
        "processor_performance_decrease_threshold": 10,
        "processor_performance_core_parking_min_cores": 100,
        "processor_performance_core_parking_max_cores": 100,
        "processor_idle_disable": 1,
        "processor_performance_boost_policy": 3,  # Aggressive at all times
        "system_cooling_policy": 0,  # Active
        "processor_performance_increase_policy": 3,  # Aggressive
        "processor_performance_decrease_policy": 1,  # Gradual
        "processor_idle_time_check": 20000,
        "processor_performance_history_count": 50,
        "processor_duty_cycling": 0,  # Disable duty cycling
        "processor_idle_state_maximum": 0,  # Minimal idle states
        "standby_budget_percent": 30,  # Less aggressive standby
        "energysaver_brightness": 100,
        "energysaver_battery_threshold": 10,
    }
}

class PowerPlanManager:
    """Manages Framework laptop power plans."""
    
    def __init__(self):
        """Initialize the power plan manager."""
        self._powercfg_path = os.path.join(os.environ["WINDIR"], "System32", "powercfg.exe")
        self._current_plan = None
        self._plans = {}
        
    async def initialize(self) -> None:
        """Initialize power plans."""
        try:
            # Create custom power plans if they don't exist
            for plan_name in POWER_OVERLAYS.keys():
                await self._create_or_get_power_plan(plan_name)
            
            logger.info("Power plans initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize power plans: {e}")
            raise
    
    async def _create_or_get_power_plan(self, plan_name: str) -> str:
        """Create a new power plan or get existing one."""
        try:
            # Check if plan already exists
            guid = await self._get_plan_guid(plan_name)
            if guid:
                logger.debug(f"Power plan {plan_name} already exists with GUID: {guid}")
                return guid
            
            # Create new plan based on balanced template
            proc = await asyncio.create_subprocess_exec(
                self._powercfg_path, "-duplicatescheme", "381b4222-f694-41f0-9685-ff5bb260df2e",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to create power plan: {stderr.decode()}")
            
            new_guid = stdout.decode().strip().split()[3]
            
            # Rename the plan
            await asyncio.create_subprocess_exec(
                self._powercfg_path, "-changename", new_guid, plan_name,
                "Custom Framework power plan for specific performance profile"
            )
            
            # Apply settings for the plan
            await self._apply_power_settings(new_guid, POWER_SETTINGS[plan_name])
            
            # Link with Windows 11 power overlay
            await self._link_power_overlay(new_guid, POWER_OVERLAYS[plan_name])
            
            logger.info(f"Created new power plan: {plan_name} with GUID: {new_guid}")
            return new_guid
            
        except Exception as e:
            logger.error(f"Error creating power plan {plan_name}: {e}")
            raise
    
    async def _get_plan_guid(self, plan_name: str) -> Optional[str]:
        """Get GUID for a power plan by name."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self._powercfg_path, "-list",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to list power plans: {stderr.decode()}")
            
            for line in stdout.decode().split('\n'):
                if plan_name in line:
                    return line.split()[3]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting plan GUID for {plan_name}: {e}")
            raise
    
    async def _apply_power_settings(self, guid: str, settings: Dict[str, int]) -> None:
        """Apply power settings to a plan."""
        try:
            for setting, value in settings.items():
                proc = await asyncio.create_subprocess_exec(
                    self._powercfg_path, "-setacvalueindex", guid, "SUB_PROCESSOR", setting, str(value),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                await proc.communicate()
                
                # Also set for battery power
                proc = await asyncio.create_subprocess_exec(
                    self._powercfg_path, "-setdcvalueindex", guid, "SUB_PROCESSOR", setting, str(value),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                await proc.communicate()
            
            logger.debug(f"Applied power settings to plan {guid}")
            
        except Exception as e:
            logger.error(f"Error applying power settings to plan {guid}: {e}")
            raise
    
    async def _link_power_overlay(self, guid: str, overlay_guid: str) -> None:
        """Link power plan with Windows 11 power overlay."""
        try:
            # Use powercfg to set the power mode directly
            proc = await asyncio.create_subprocess_exec(
                self._powercfg_path, "/setactive", guid,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to set active power plan: {stderr.decode()}")

            # Set the power mode using powercfg
            mode_map = {
                "961cc777-2547-4f9d-8174-7d86181b8a7a": "power-saver",      # Silent
                "3af9b8d9-7c97-431d-ad78-34a8bfea439f": "balanced",         # Balanced
                "ded574b5-45a0-4f42-8737-46345c09c238": "high-performance"  # Boost
            }

            if overlay_guid in mode_map:
                mode = mode_map[overlay_guid]
                proc = await asyncio.create_subprocess_exec(
                    self._powercfg_path, "/setacvalueindex", guid, "SUB_PROCESSOR", "PERFBOOSTMODE", 
                    "1" if mode == "high-performance" else "0",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                await proc.communicate()

                # Apply the changes
                proc = await asyncio.create_subprocess_exec(
                    self._powercfg_path, "/setactive", guid,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                await proc.communicate()

            logger.debug(f"Set power plan {guid} with mode {mode_map.get(overlay_guid, 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error linking power overlay for plan {guid}: {e}")
            raise
    
    async def set_power_plan(self, plan_name: str) -> None:
        """Set the active power plan."""
        try:
            guid = await self._get_plan_guid(plan_name)
            if not guid:
                raise ValueError(f"Power plan {plan_name} not found")
            
            proc = await asyncio.create_subprocess_exec(
                self._powercfg_path, "-setactive", guid,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            await proc.communicate()
            
            self._current_plan = plan_name
            logger.info(f"Activated power plan: {plan_name}")
            
        except Exception as e:
            logger.error(f"Error setting power plan {plan_name}: {e}")
            raise
    
    async def get_current_plan(self) -> Optional[str]:
        """Get the name of the current power plan."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self._powercfg_path, "-getactivescheme",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get active scheme: {stderr.decode()}")
            
            current_guid = stdout.decode().strip().split()[3]
            
            # Find plan name by GUID
            for name, guid in self._plans.items():
                if guid == current_guid:
                    return name
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current power plan: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up custom power plans."""
        try:
            for plan_name in POWER_OVERLAYS.keys():
                guid = await self._get_plan_guid(plan_name)
                if guid:
                    proc = await asyncio.create_subprocess_exec(
                        self._powercfg_path, "-delete", guid,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    await proc.communicate()
                    logger.debug(f"Deleted power plan: {plan_name}")
            
            logger.info("Cleaned up all custom power plans")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise
    
    async def apply_profile(self, profile: PowerProfile) -> bool:
        """Apply a power profile by setting both Windows power plan and RyzenAdj parameters."""
        try:
            success = True
            
            # 1. Apply Windows Power Plan
            profile_map = {
                "Silent": "Framework-Silent",
                "Balanced": "Framework-Balanced",
                "Boost": "Framework-Boost"
            }

            plan_name = profile_map.get(profile.name)
            if plan_name:
                # Initialize power plans if not done yet
                if not self._plans:
                    await self.initialize()
                # Set the power plan
                await self.set_power_plan(plan_name)
                logger.info(f"Applied Windows power plan: {profile.name} -> {plan_name}")
            else:
                logger.error(f"Invalid profile name for Windows power plan: {profile.name}")
                success = False

            # 2. Apply RyzenAdj Settings
            ryzenadj_path = os.path.join("libs", "ryzenadj.exe")
            if not os.path.exists(ryzenadj_path):
                logger.error("RyzenAdj not found at: %s", ryzenadj_path)
                return False

            # Log RyzenAdj values before applying
            logger.info(f"\nApplying RyzenAdj settings for profile '{profile.name}':")
            if hasattr(profile, 'stapm_limit'):
                logger.info(f"  STAPM Limit: {profile.stapm_limit} mW")
            if hasattr(profile, 'fast_limit'):
                logger.info(f"  Fast Limit: {profile.fast_limit} mW")
            if hasattr(profile, 'slow_limit'):
                logger.info(f"  Slow Limit: {profile.slow_limit} mW")
            if hasattr(profile, 'tctl_temp'):
                logger.info(f"  TCTL Temp: {profile.tctl_temp}°C")
            if hasattr(profile, 'vrm_current'):
                logger.info(f"  VRM Current: {profile.vrm_current} mA")
            if hasattr(profile, 'vrmmax_current'):
                logger.info(f"  VRM Max Current: {profile.vrmmax_current} mA")
            if hasattr(profile, 'vrmsoc_current'):
                logger.info(f"  VRM SoC Current: {profile.vrmsoc_current} mA")
            if hasattr(profile, 'vrmsocmax_current'):
                logger.info(f"  VRM SoC Max Current: {profile.vrmsocmax_current} mA")

            # Build RyzenAdj command with profile parameters
            cmd = [ryzenadj_path]
            
            # Add parameters if they exist in the profile
            if hasattr(profile, 'stapm_limit'):
                cmd.extend(['--stapm-limit', str(profile.stapm_limit)])
            if hasattr(profile, 'fast_limit'):
                cmd.extend(['--fast-limit', str(profile.fast_limit)])
            if hasattr(profile, 'slow_limit'):
                cmd.extend(['--slow-limit', str(profile.slow_limit)])
            if hasattr(profile, 'tctl_temp'):
                cmd.extend(['--tctl-temp', str(profile.tctl_temp)])
            if hasattr(profile, 'vrm_current'):
                cmd.extend(['--vrm-current', str(profile.vrm_current)])
            if hasattr(profile, 'vrmmax_current'):
                cmd.extend(['--vrmmax-current', str(profile.vrmmax_current)])
            if hasattr(profile, 'vrmsoc_current'):
                cmd.extend(['--vrmsoc-current', str(profile.vrmsoc_current)])
            if hasattr(profile, 'vrmsocmax_current'):
                cmd.extend(['--vrmsocmax-current', str(profile.vrmsocmax_current)])

            # Log the full command being executed
            logger.debug(f"Executing RyzenAdj command: {' '.join(cmd)}")

            # Execute RyzenAdj command
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Successfully applied RyzenAdj settings for profile: {profile.name}")
                    logger.debug(f"RyzenAdj output: {stdout.decode()}")
                else:
                    logger.error(f"RyzenAdj error: {stderr.decode()}")
                    success = False
                    
            except Exception as e:
                logger.error(f"Error executing RyzenAdj: {e}")
                success = False

            return success

        except Exception as e:
            logger.error(f"Error applying power profile {profile.name}: {e}")
            return False
