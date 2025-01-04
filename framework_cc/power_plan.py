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

# Check if pywin32 is installed, if not install it
try:
    import win32con
except ImportError:
    logger = logging.getLogger(__name__)
    logger.info("Installing required package: pywin32")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
    import win32con

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
        # Processor Power Management
        "processor_performance_increase_threshold": 90,  # Only increase when very high load
        "processor_performance_decrease_threshold": 80,  # Quickly decrease when load drops
        "processor_performance_core_parking_min_cores": 25,  # Allow aggressive core parking
        "processor_performance_core_parking_max_cores": 50,  # Limit max cores for power saving
        "processor_idle_disable": 0,  # Enable idle states
        "processor_performance_boost_policy": 0,  # Disabled
        "system_cooling_policy": 0,  # Passive cooling
        "processor_performance_increase_policy": 0,  # Gradual increase
        "processor_performance_decrease_policy": 2,  # Aggressive decrease
        "processor_idle_time_check": 50000,  # Longer idle check
        "processor_performance_history_count": 5,  # Short history for quick power saving
        "processor_duty_cycling": 1,  # Enable duty cycling
        "processor_idle_state_maximum": 2,  # Deep idle states allowed
        "processor_performance_autonomous_mode": 0,  # Disabled for power saving
        "processor_performance_boost_mode": 0,  # Disabled
        "minimum_processor_state": 5,  # Very low minimum state
        "maximum_processor_state": 50,  # Limited maximum state
        "heterogeneous_policy": 4,  # Prefer efficient cores
        
        # Graphics & Display
        "gpu_preference_policy": 1,  # Low power
        "enable_adaptive_brightness": 1,  # On
        "adaptive_brightness": 1,  # Enable adaptive brightness for power saving
        "dimmed_display_brightness": 30,
        "video_playback_quality_bias": 0,  # Power saving
        "switchable_dynamic_graphics": 0,  # Force power-saving graphics
        
        # Hard Disk & Storage
        "disk_idle_timeout": 60,  # Quick disk sleep
        "nvme_power_state_timeout": 100,  # Aggressive NVMe power saving
        
        # USB & PCI Express
        "usb_selective_suspend": 1,  # Enabled
        "usb3_link_power_management": 3,  # Maximum power savings
        "pci_express_power_management": 2,  # Maximum power savings
        
        # Wireless Settings
        "wireless_adapter_power_mode": 3,  # Maximum Power Saving
        
        # Energy Saver
        "energy_saver_policy": 1,  # Aggressive
        "energy_saver_brightness": 30,  # Low brightness
        "energy_saver_battery_threshold": 30,  # Start saving early
        
        # Battery
        "battery_action_critical": 2,  # Hibernate
        "critical_battery_level": 7,
        "low_battery_level": 15,
        "reserve_battery_level": 10
    },
    
    "Framework-Balanced": {
        # Processor Power Management
        "processor_performance_increase_threshold": 60,
        "processor_performance_decrease_threshold": 40,
        "processor_performance_core_parking_min_cores": 50,
        "processor_performance_core_parking_max_cores": 100,
        "processor_idle_disable": 0,
        "processor_performance_boost_policy": 2,  # Aggressive
        "system_cooling_policy": 1,  # Active cooling
        "processor_performance_increase_policy": 2,  # Medium
        "processor_performance_decrease_policy": 1,  # Medium
        "processor_idle_time_check": 30000,
        "processor_performance_history_count": 20,
        "processor_duty_cycling": 0,  # Disabled
        "processor_idle_state_maximum": 1,  # Moderate idle states
        "processor_performance_autonomous_mode": 1,  # Enabled
        "processor_performance_boost_mode": 2,  # Aggressive
        "minimum_processor_state": 10,
        "maximum_processor_state": 100,
        "heterogeneous_policy": 5,  # Automatic
        
        # Graphics & Display
        "gpu_preference_policy": 0,  # Balanced
        "enable_adaptive_brightness": 1,  # On
        "adaptive_brightness": 1,  # Enable adaptive brightness for balanced usage
        "dimmed_display_brightness": 40,
        "video_playback_quality_bias": 1,  # Balanced
        "switchable_dynamic_graphics": 1,  # Optimize power savings
        
        # Hard Disk & Storage
        "disk_idle_timeout": 300,
        "nvme_power_state_timeout": 500,
        
        # USB & PCI Express
        "usb_selective_suspend": 1,
        "usb3_link_power_management": 2,  # Moderate power savings
        "pci_express_power_management": 1,  # Moderate savings
        
        # Wireless Settings
        "wireless_adapter_power_mode": 2,  # Medium Power Saving
        
        # Energy Saver
        "energy_saver_policy": 0,  # User
        "energy_saver_brightness": 50,  # Medium brightness
        "energy_saver_battery_threshold": 20,  # Default threshold
        
        # Battery
        "battery_action_critical": 2,  # Hibernate
        "critical_battery_level": 5,
        "low_battery_level": 10,
        "reserve_battery_level": 7
    },
    
    "Framework-Boost": {
        # Processor Power Management
        "processor_performance_increase_threshold": 30,  # Quick to increase
        "processor_performance_decrease_threshold": 10,  # Slow to decrease
        "processor_performance_core_parking_min_cores": 100,  # No core parking
        "processor_performance_core_parking_max_cores": 100,  # All cores available
        "processor_idle_disable": 0,  # Enable idle states
        "processor_performance_boost_policy": 3,  # Aggressive at all times
        "system_cooling_policy": 1,  # Active cooling
        "processor_performance_increase_policy": 3,  # Aggressive
        "processor_performance_decrease_policy": 0,  # Gradual decrease
        "processor_idle_time_check": 20000,  # Quick idle check
        "processor_performance_history_count": 50,  # Long history for sustained performance
        "processor_duty_cycling": 0,  # Disabled
        "processor_idle_state_maximum": 1,  # Minimal idle states
        "processor_performance_autonomous_mode": 1,  # Enabled
        "processor_performance_boost_mode": 3,  # Aggressive at all times
        "minimum_processor_state": 50,  # High minimum state
        "maximum_processor_state": 100,  # Maximum performance
        "heterogeneous_policy": 1,  # Use performance cores
        
        # Graphics & Display
        "gpu_preference_policy": 0,  # High performance
        "enable_adaptive_brightness": 0,  # Off
        "adaptive_brightness": 0,  # Disable adaptive brightness for max performance
        "dimmed_display_brightness": 100,
        "video_playback_quality_bias": 1,  # Performance
        "switchable_dynamic_graphics": 3,  # Maximize performance
        
        # Hard Disk & Storage
        "disk_idle_timeout": 0,  # Never idle
        "nvme_power_state_timeout": 2000,  # Reduced power management
        
        # USB & PCI Express
        "usb_selective_suspend": 0,  # Disabled
        "usb3_link_power_management": 0,  # Off
        "pci_express_power_management": 0,  # Off
        
        # Wireless Settings
        "wireless_adapter_power_mode": 0,  # Maximum Performance
        
        # Energy Saver
        "energy_saver_policy": 0,  # User
        "energy_saver_brightness": 100,  # Maximum brightness
        "energy_saver_battery_threshold": 10,  # Low threshold
        
        # Battery
        "battery_action_critical": 2,  # Hibernate
        "critical_battery_level": 3,
        "low_battery_level": 7,
        "reserve_battery_level": 5
    }
}

class PowerManager:
    """Manages Framework laptop power plans."""
    
    def __init__(self) -> None:
        """Initialize power plan manager."""
        self._powercfg_path = "powercfg.exe"
        self._current_plan = None
        self._plans = {}
        self._guid_activation_key = "HKLM:\\SOFTWARE\\Framework\\PowerPlan"
        
    async def _check_and_activate_guids(self) -> None:
        """Check if power plan GUIDs have been activated and activate them if needed."""
        try:
            # Check if we've already activated GUIDs
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    "SOFTWARE\\Framework\\PowerPlan",
                    0,
                    win32con.KEY_READ | win32con.KEY_WOW64_64KEY
                )
                value = winreg.QueryValueEx(key, "GUIDsActivated")[0]
                winreg.CloseKey(key)
                if value == 1:
                    logger.info("Power plan GUIDs already activated")
                    return
            except WindowsError:
                pass  # Key doesn't exist, need to activate GUIDs
            
            logger.info("Activating power plan GUIDs...")
            
            # Run PowerShell command to activate GUIDs with elevated privileges
            ps_command = """
            Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings' -Recurse | 
            Where-Object { $_.Name -notmatch 'DefaultPowerSchemeValues' -and $_.Name -notmatch '\\\\[0-9]$' -and $_.Name -notmatch '\\\\255$' } | 
            ForEach-Object { Set-ItemProperty -Path ($_.PSPath -replace 'Microsoft.PowerShell.Core\\\\Registry::HKEY_LOCAL_MACHINE', 'HKLM:') -Name 'Attributes' -Value 2 -Force }
            """
            
            # Create PowerShell process with elevated privileges
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle", "Hidden",
                "-Command", ps_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Failed to activate GUIDs: {stderr.decode()}")
            
            # Create registry key to mark GUIDs as activated
            try:
                key = winreg.CreateKeyEx(
                    winreg.HKEY_LOCAL_MACHINE,
                    "SOFTWARE\\Framework\\PowerPlan",
                    0,
                    win32con.KEY_WRITE | win32con.KEY_WOW64_64KEY
                )
                winreg.SetValueEx(key, "GUIDsActivated", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
                logger.info("Power plan GUIDs activated successfully")
            except WindowsError as e:
                logger.error(f"Failed to create registry key: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error checking/activating power plan GUIDs: {e}")
            raise
        
    async def initialize(self) -> None:
        """Initialize power plans."""
        try:
            # First, check and activate GUIDs if needed
            await self._check_and_activate_guids()
            
            # Create or get each power plan
            for plan_name in POWER_OVERLAYS.keys():
                guid = await self._create_or_get_power_plan(plan_name)
                self._plans[plan_name] = guid
                logger.info(f"Initialized power plan: {plan_name} with GUID: {guid}")
        except Exception as e:
            logger.error(f"Error initializing power plans: {e}")
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
            # Map settings to their correct GUIDs
            # These GUIDs are from Windows power settings
            subgroup_map = {
                # Processor power management (54533251-82be-4824-96c1-47b60b740d00)
                "processor_performance_increase_threshold": ("54533251-82be-4824-96c1-47b60b740d00", "4009edd0-e3d4-4148-b7a4-3fe4908ed43e"),
                "processor_performance_decrease_threshold": ("54533251-82be-4824-96c1-47b60b740d00", "4009edd1-e3d4-4148-b7a4-3fe4908ed43e"),
                "processor_performance_core_parking_min_cores": ("54533251-82be-4824-96c1-47b60b740d00", "0cc5b647-c1df-4637-891a-dec35c318583"),
                "processor_performance_core_parking_max_cores": ("54533251-82be-4824-96c1-47b60b740d00", "ea062031-0e34-4ff1-9b6d-eb1059334028"),
                "processor_idle_disable": ("54533251-82be-4824-96c1-47b60b740d00", "5d76a2ca-e8c0-402f-a133-2158492d58ad"),
                "processor_performance_boost_policy": ("54533251-82be-4824-96c1-47b60b740d00", "45bcc044-d885-43e2-8605-ee0ec6e96b59"),
                "system_cooling_policy": ("54533251-82be-4824-96c1-47b60b740d00", "94d3a615-a899-4ac5-ae2b-e4d8f634367f"),
                "processor_performance_increase_policy": ("54533251-82be-4824-96c1-47b60b740d00", "c7be0679-2817-4d69-9d02-519a537ed0c6"),
                "processor_performance_decrease_policy": ("54533251-82be-4824-96c1-47b60b740d00", "71021b41-c749-4d21-be74-a00f335d582b"),
                "processor_idle_time_check": ("54533251-82be-4824-96c1-47b60b740d00", "c4581c31-89ab-4597-8e2b-9c9cab440e6b"),
                "processor_performance_history_count": ("54533251-82be-4824-96c1-47b60b740d00", "7d24baa7-0b84-480f-840c-1b0743c00f5f"),
                "processor_duty_cycling": ("54533251-82be-4824-96c1-47b60b740d00", "4e4450b3-6179-4e91-b8f1-5bb9938f81a1"),
                "processor_idle_state_maximum": ("54533251-82be-4824-96c1-47b60b740d00", "9943e905-9a30-4ec1-9b99-44dd3b76f7a2"),
                "processor_performance_autonomous_mode": ("54533251-82be-4824-96c1-47b60b740d00", "8baa4a8a-14c6-4451-8e8b-14bdbd197537"),
                "processor_performance_boost_mode": ("54533251-82be-4824-96c1-47b60b740d00", "be337238-0d82-4146-a960-4f3749d470c7"),
                "minimum_processor_state": ("54533251-82be-4824-96c1-47b60b740d00", "893dee8e-2bef-41e0-89c6-b55d0929964c"),
                "maximum_processor_state": ("54533251-82be-4824-96c1-47b60b740d00", "bc5038f7-23e0-4960-96da-33abaf5935ec"),
                "heterogeneous_policy": ("54533251-82be-4824-96c1-47b60b740d00", "7f2f5cfa-f10c-4823-b5e1-e93ae85f46b5"),

                # Display settings (7516b95f-f776-4464-8c53-06167f40cc99)
                "gpu_preference_policy": ("7516b95f-f776-4464-8c53-06167f40cc99", "dd848b2a-8a5d-4451-9ae2-39cd41658f6c"),
                "enable_adaptive_brightness": ("7516b95f-f776-4464-8c53-06167f40cc99", "fbd9aa66-9553-4097-ba44-ed6e9d65eab8"),
                "adaptive_brightness": ("7516b95f-f776-4464-8c53-06167f40cc99", "aded5e82-b909-4619-9949-f5d71dac0bcb"),
                "dimmed_display_brightness": ("7516b95f-f776-4464-8c53-06167f40cc99", "f1fbfde2-a960-4165-9f88-50667911ce96"),
                "video_playback_quality_bias": ("7516b95f-f776-4464-8c53-06167f40cc99", "10778347-1370-4ee0-8bbd-33bdacaade49"),

                # Graphics settings (5fb4938d-1ee8-4b0f-9a3c-5036b0ab995c)
                "switchable_dynamic_graphics": ("5fb4938d-1ee8-4b0f-9a3c-5036b0ab995c", "dd848b2a-8a5d-4451-9ae2-39cd41658f6c"),

                # Disk settings (0012ee47-9041-4b5d-9b77-535fba8b1442)
                "disk_idle_timeout": ("0012ee47-9041-4b5d-9b77-535fba8b1442", "6738e2c4-e8a5-4a42-b16a-e040e769756e"),
                "nvme_power_state_timeout": ("0012ee47-9041-4b5d-9b77-535fba8b1442", "fc95af4d-40e7-4b6d-835a-56d131dbc80e"),

                # USB settings (2a737441-1930-4402-8d77-b2bebba308a3)
                "usb_selective_suspend": ("2a737441-1930-4402-8d77-b2bebba308a3", "48e6b7a6-50f5-4782-a5d4-53bb8f07e226"),
                "usb3_link_power_management": ("2a737441-1930-4402-8d77-b2bebba308a3", "d4e98f31-5ffe-4ce1-be31-1b38b384c009"),

                # PCI Express settings (501a4d13-42af-4429-9fd1-a8218c268e20)
                "pci_express_power_management": ("501a4d13-42af-4429-9fd1-a8218c268e20", "ee12f906-d277-404b-b6da-e5fa1a576df5"),

                # Wireless adapter settings (19cbb8fa-5279-450e-9fac-8a3d5fedd0c1)
                "wireless_adapter_power_mode": ("19cbb8fa-5279-450e-9fac-8a3d5fedd0c1", "12bbebe6-58d6-4636-95bb-3217ef867c1a"),

                # Battery settings (e73a048d-bf27-4f12-9731-8b2076e8891f)
                "battery_action_critical": ("e73a048d-bf27-4f12-9731-8b2076e8891f", "637ea02f-bbcb-4015-8e2c-a1c7b9c0b546"),
                "critical_battery_level": ("e73a048d-bf27-4f12-9731-8b2076e8891f", "9a66d8d7-4ff7-4ef9-b5a2-5a326ca2a469"),
                "low_battery_level": ("e73a048d-bf27-4f12-9731-8b2076e8891f", "8183ba9a-e910-48da-8769-14ae6dc1170a"),
                "reserve_battery_level": ("e73a048d-bf27-4f12-9731-8b2076e8891f", "f3c5027d-cd16-4930-aa6b-90db844a8f00"),
            }
            
            for setting, value in settings.items():
                if setting in subgroup_map:
                    subgroup_guid, setting_guid = subgroup_map[setting]
                    
                    # Apply for AC power
                    proc = await asyncio.create_subprocess_exec(
                        self._powercfg_path, "/setacvalueindex", guid, subgroup_guid, setting_guid, str(value),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    if proc.returncode != 0:
                        logger.warning(f"Failed to set AC value for {setting}: {stderr.decode()}")
                    
                    # Verify AC setting was applied
                    proc = await asyncio.create_subprocess_exec(
                        self._powercfg_path, "/query", guid, subgroup_guid, setting_guid,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    if proc.returncode == 0:
                        output = stdout.decode()
                        if "Current AC Power Setting Index:" in output:
                            current_value = int(output.split("Current AC Power Setting Index:")[1].split()[0], 16)
                            if current_value != value:
                                logger.warning(f"AC value verification failed for {setting}: expected {value}, got {current_value}")
                    
                    # Apply for DC power (battery)
                    proc = await asyncio.create_subprocess_exec(
                        self._powercfg_path, "/setdcvalueindex", guid, subgroup_guid, setting_guid, str(value),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    if proc.returncode != 0:
                        logger.warning(f"Failed to set DC value for {setting}: {stderr.decode()}")
                    
                    # Verify DC setting was applied
                    proc = await asyncio.create_subprocess_exec(
                        self._powercfg_path, "/query", guid, subgroup_guid, setting_guid,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    if proc.returncode == 0:
                        output = stdout.decode()
                        if "Current DC Power Setting Index:" in output:
                            current_value = int(output.split("Current DC Power Setting Index:")[1].split()[0], 16)
                            if current_value != value:
                                logger.warning(f"DC value verification failed for {setting}: expected {value}, got {current_value}")
                    
                    logger.debug(f"Applied and verified setting {setting} = {value}")
            
            # Apply all changes
            proc = await asyncio.create_subprocess_exec(
                self._powercfg_path, "/setactive", guid,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning(f"Failed to set active power plan: {stderr.decode()}")
            else:
                logger.debug(f"Applied all power settings to plan {guid}")
            
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
        """Apply a power profile."""
        try:
            # First, apply Windows power plan
            windows_plan_name = f"Framework-{profile.name}"
            await self.set_power_plan(windows_plan_name)
            logger.info(f"Applied Windows power plan: {profile.name} -> {windows_plan_name}")

            # Set brightness based on profile
            try:
                from .display import DisplayManager
                display = DisplayManager()
                brightness_levels = {
                    "Silent": 0,
                    "Balanced": 50,
                    "Boost": 100
                }
                if profile.name in brightness_levels:
                    await display.set_brightness(brightness_levels[profile.name])
                    logger.info(f"Set brightness to {brightness_levels[profile.name]}% for profile {profile.name}")
            except Exception as e:
                logger.error(f"Error setting brightness: {e}")

            # Then try to apply RyzenAdj settings if available
            if hasattr(profile, 'stapm_limit'):
                try:
                    logger.info(f"\nApplying RyzenAdj settings for profile '{profile.name}':")
                    logger.info(f"  STAPM Limit: {profile.stapm_limit} mW")
                    logger.info(f"  Fast Limit: {profile.fast_limit} mW")
                    logger.info(f"  Slow Limit: {profile.slow_limit} mW")
                    logger.info(f"  TCTL Temp: {profile.tctl_temp}°C")
                    logger.info(f"  VRM Current: {profile.vrm_current} mA")
                    logger.info(f"  VRM Max Current: {profile.vrmmax_current} mA")
                    logger.info(f"  VRM SoC Current: {profile.vrmsoc_current} mA")
                    logger.info(f"  VRM SoC Max Current: {profile.vrmsocmax_current} mA")

                    # Find RyzenAdj executable
                    if getattr(sys, 'frozen', False):
                        # If running as compiled executable
                        base_path = sys._MEIPASS
                    else:
                        # If running from Python interpreter
                        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                    ryzenadj_paths = [
                        os.path.join(base_path, "libs", "ryzenadj.exe"),
                        os.path.join(base_path, "ryzenadj.exe"),
                        os.path.join("libs", "ryzenadj.exe"),
                        "ryzenadj.exe"
                    ]

                    ryzenadj_exe = None
                    for path in ryzenadj_paths:
                        if os.path.exists(path):
                            ryzenadj_exe = path
                            logger.debug(f"Found RyzenAdj at: {path}")
                            break

                    if not ryzenadj_exe:
                        logger.error("RyzenAdj not found in any of these locations:")
                        for path in ryzenadj_paths:
                            logger.error(f"  - {os.path.abspath(path)}")
                        logger.error("Continuing with Windows power plan only")
                        return True

                    # Build RyzenAdj command
                    cmd = [
                        ryzenadj_exe,
                        f"--stapm-limit={profile.stapm_limit}",
                        f"--fast-limit={profile.fast_limit}",
                        f"--slow-limit={profile.slow_limit}",
                        f"--tctl-temp={profile.tctl_temp}",
                        f"--vrm-current={profile.vrm_current}",
                        f"--vrmmax-current={profile.vrmmax_current}",
                        f"--vrmsoc-current={profile.vrmsoc_current}",
                        f"--vrmsocmax-current={profile.vrmsocmax_current}"
                    ]

                    # Try to run RyzenAdj
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()

                    if process.returncode != 0:
                        logger.error(f"RyzenAdj error: {stderr.decode() if stderr else 'Unknown error'}")
                        logger.error(f"RyzenAdj command was: {' '.join(cmd)}")
                        logger.error(f"RyzenAdj stdout: {stdout.decode() if stdout else 'No output'}")
                        # Continue anyway - we at least have Windows power plan
                    else:
                        logger.info("RyzenAdj settings applied successfully")

                except Exception as e:
                    logger.error(f"Error applying RyzenAdj settings: {e}")
                    logger.error(f"Continuing with Windows power plan only")
                    # Continue anyway - we at least have Windows power plan

            return True

        except Exception as e:
            logger.error(f"Error applying power profile: {e}")
            return False
    
    async def reset_power_plans(self) -> None:
        """Reset all power plans by deleting and recreating them."""
        try:
            # First, delete existing plans
            await self.cleanup()
            
            # Clear the plans dictionary
            self._plans.clear()
            
            # Recreate all plans
            await self.initialize()
            
            logger.info("Successfully reset all power plans")
            
        except Exception as e:
            logger.error(f"Error resetting power plans: {e}")
            raise