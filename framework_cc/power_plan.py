"""Module de gestion des plans d'alimentation Windows."""

import logging
import subprocess
import json
import asyncio
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .models import LaptopModel
from .utils import get_resource_path
from .constants import RYZENADJ_PARAMS

logger = logging.getLogger(__name__)

class WindowsPowerPlanManager:
    """Gestionnaire des plans d'alimentation Windows."""
    
    # GUIDs des plans d'alimentation Windows
    POWER_PLANS = {
        "Silent": "a1841308-3541-4fab-bc81-f71556f20b4a",    # Power saver
        "Balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",  # Balanced
        "Boost": "e9a42b02-d5df-448d-aa00-03f14749eb61"      # Ultimate Performance
    }
    
    # Paramètres pour le plan Silent (économie d'énergie maximale)
    SILENT_SETTINGS = {
        "54533251-82be-4824-96c1-47b60b740d00": {  # Processor Power Management
            "893dee8e-2bef-41e0-89c6-b55d0929964c": {"ac": 5, "dc": 5},  # Minimum processor state
            "bc5038f7-23e0-4960-96da-33abaf5935ec": {"ac": 30, "dc": 30},  # Maximum processor state
            "be337238-0d82-4146-a960-4f3749d470c7": {"ac": 0, "dc": 0},  # Performance boost mode
            "45bcc044-d885-43e2-8605-ee0ec6e96b59": {"ac": 0, "dc": 0}  # Performance boost policy
        },
        "3c0bc021-c8a8-4e07-a973-6b14bcb2b7e": {  # Display Settings
            "90959d22-d6a1-49b9-af93-bce885ad335b": {"ac": 1, "dc": 1},  # Adaptive display
            "a9ceb8da-cd46-44fb-a98b-02af69de4623": {"ac": 1, "dc": 1},  # Allow display required policy
            "aded5e82-b909-4619-9949-f5d71dac0bcb": {"ac": 30, "dc": 30},  # Display brightness
            "f1fbfde2-a960-4165-9f88-50667911ce96": {"ac": 50, "dc": 50},  # Dimmed display brightness
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 1, "dc": 1}   # Enable adaptive brightness
        },
        "238c9fa8-0aad-41ed-83f4-97be242c8f20": {  # Sleep Settings
            "29f6c1db-86da-48c5-9fad-628d2a5290dc": {"ac": 180, "dc": 180},  # Sleep idle timeout
            "9d7815a6-7ee4-497e-8888-515a05f02364": {"ac": 3600, "dc": 1800},  # Hibernate timeout
            "94ac6d29-73ce-41a6-809f-6363ba21b47e": {"ac": 0, "dc": 0}  # Hybrid sleep
        },
        "501a4d13-42af-4429-9fd1-a8218c2682e0": {  # PCI Express
            "ee12f906-d277-404b-b6da-e5fa1a576df5": {"ac": 2, "dc": 2}  # Link State Power Management
        },
        "e276e160-7cb0-43c6-b20b-73f5dce39954": {  # Graphics Power Management
            "a1662ab2-9d34-4e53-ba8b-2639b9e20857": {"ac": 0, "dc": 0}  # Force power-saving graphics
        },
        "de830923-a562-41af-a086-e3a2c6bad2da": {  # Energy Saver settings
            "13d09884-f74e-474a-a852-b6bde8ad03a8": {"ac": 30, "dc": 30},  # Display brightness weight
            "5c5bb349-ad29-4ee2-9d0b-2b25270f7a81": {"ac": 1, "dc": 1},     # Energy Saver Policy (1 = Aggressive)
            "e69653ca-cf7f-4f05-aa73-cb833fa90ad4": {"ac": 100, "dc": 100}  # Charge level
        },
        "2a737441-1930-4402-8d77-b2bebba308a": {  # USB Power Management
            "48e6b7a6-50f5-4782-a5d4-53bb80f7e226": {"ac": 2, "dc": 2}  # USB selective suspend
        },
        "7516b95f-f776-4464-bc83-06167f40cc99": {  # Adaptive Display
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 1, "dc": 1}  # Adaptive brightness
        },
        "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e": {  # AMD Power Slider
            "38cab4d5-db09-449f-9db5-1c91c909b6d4": {"ac": 0, "dc": 0},  # PMF Controller - Battery saver
            "7ec1751b-60ed-4588-afb5-9819d3d77d90": {"ac": 0, "dc": 0}   # Overlay - Battery saver
        }
    }
    
    # Paramètres pour le plan Balanced (utilisation quotidienne)
    BALANCED_SETTINGS = {
        "54533251-82be-4824-96c1-47b60b740d00": {  # Processor Power Management
            "893dee8e-2bef-41e0-89c6-b55d0929964c": {"ac": 10, "dc": 10},  # Minimum processor state
            "bc5038f7-23e0-4960-96da-33abaf5935ec": {"ac": 99, "dc": 99},  # Maximum processor state
            "be337238-0d82-4146-a960-4f3749d470c7": {"ac": 1, "dc": 1},    # Performance boost mode
            "45bcc044-d885-43e2-8605-ee0ec6e96b59": {"ac": 50, "dc": 50}   # Performance boost policy
        },
        "3c0bc021-c8a8-4e07-a973-6b14bcb2b7e": {  # Display Settings
            "90959d22-d6a1-49b9-af93-bce885ad335b": {"ac": 1, "dc": 1},  # Adaptive display
            "a9ceb8da-cd46-44fb-a98b-02af69de4623": {"ac": 1, "dc": 1},  # Allow display required policy
            "aded5e82-b909-4619-9949-f5d71dac0bcb": {"ac": 70, "dc": 50},  # Display brightness
            "f1fbfde2-a960-4165-9f88-50667911ce96": {"ac": 70, "dc": 50},  # Dimmed display brightness
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 1, "dc": 1}   # Enable adaptive brightness
        },
        "238c9fa8-0aad-41ed-83f4-97be242c8f20": {  # Sleep Settings
            "29f6c1db-86da-48c5-9fad-628d2a5290dc": {"ac": 3600, "dc": 600},  # Sleep idle timeout
            "9d7815a6-7ee4-497e-8888-515a05f02364": {"ac": 14400, "dc": 3600},  # Hibernate timeout
            "94ac6d29-73ce-41a6-809f-6363ba21b47e": {"ac": 0, "dc": 0}  # Hybrid sleep
        },
        "501a4d13-42af-4429-9fd1-a8218c2682e0": {  # PCI Express
            "ee12f906-d277-404b-b6da-e5fa1a576df5": {"ac": 1, "dc": 1}  # Link State Power Management
        },
        "e276e160-7cb0-43c6-b20b-73f5dce39954": {  # Graphics Power Management
            "a1662ab2-9d34-4e53-ba8b-2639b9e20857": {"ac": 1, "dc": 1}  # Optimize power savings
        },
        "de830923-a562-41af-a086-e3a2c6bad2da": {  # Energy Saver settings
            "13d09884-f74e-474a-a852-b6bde8ad03a8": {"ac": 70, "dc": 50},  # Display brightness weight
            "5c5bb349-ad29-4ee2-9d0b-2b25270f7a81": {"ac": 0, "dc": 1},     # Energy Saver Policy
            "e69653ca-cf7f-4f05-aa73-cb833fa90ad4": {"ac": 100, "dc": 100}  # Charge level
        },
        "2a737441-1930-4402-8d77-b2bebba308a": {  # USB Power Management
            "48e6b7a6-50f5-4782-a5d4-53bb80f7e226": {"ac": 1, "dc": 1}  # USB selective suspend
        },
        "7516b95f-f776-4464-bc83-06167f40cc99": {  # Adaptive Display
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 1, "dc": 1}  # Adaptive brightness
        },
        "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e": {  # AMD Power Slider
            "38cab4d5-db09-449f-9db5-1c91c909b6d4": {"ac": 2, "dc": 1},  # PMF Controller - Better performance/Better battery
            "7ec1751b-60ed-4588-afb5-9819d3d77d90": {"ac": 2, "dc": 1}   # Overlay - Better performance/Better battery
        }
    }
    
    # Paramètres pour le plan Boost (performances maximales)
    BOOST_SETTINGS = {
        "54533251-82be-4824-96c1-47b60b740d00": {  # Processor Power Management
            "893dee8e-2bef-41e0-89c6-b55d0929964c": {"ac": 100, "dc": 100},  # Minimum processor state
            "bc5038f7-23e0-4960-96da-33abaf5935ec": {"ac": 100, "dc": 100},  # Maximum processor state
            "be337238-0d82-4146-a960-4f3749d470c7": {"ac": 2, "dc": 2},      # Performance boost mode (Aggressive)
            "45bcc044-d885-43e2-8605-ee0ec6e96b59": {"ac": 100, "dc": 100}   # Performance boost policy
        },
        "3c0bc021-c8a8-4e07-a973-6b14bcb2b7e": {  # Display Settings
            "90959d22-d6a1-49b9-af93-bce885ad335b": {"ac": 0, "dc": 0},  # Adaptive display
            "a9ceb8da-cd46-44fb-a98b-02af69de4623": {"ac": 1, "dc": 1},  # Allow display required policy
            "aded5e82-b909-4619-9949-f5d71dac0bcb": {"ac": 100, "dc": 100},  # Display brightness
            "f1fbfde2-a960-4165-9f88-50667911ce96": {"ac": 100, "dc": 100},  # Dimmed display brightness
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 0, "dc": 0}   # Enable adaptive brightness
        },
        "238c9fa8-0aad-41ed-83f4-97be242c8f20": {  # Sleep Settings
            "29f6c1db-86da-48c5-9fad-628d2a5290dc": {"ac": 0, "dc": 0},  # Sleep idle timeout (Never)
            "9d7815a6-7ee4-497e-8888-515a05f02364": {"ac": 0, "dc": 0},  # Hibernate timeout (Never)
            "94ac6d29-73ce-41a6-809f-6363ba21b47e": {"ac": 0, "dc": 0}  # Hybrid sleep
        },
        "501a4d13-42af-4429-9fd1-a8218c2682e0": {  # PCI Express
            "ee12f906-d277-404b-b6da-e5fa1a576df5": {"ac": 0, "dc": 0}  # Link State Power Management (Off)
        },
        "e276e160-7cb0-43c6-b20b-73f5dce39954": {  # Graphics Power Management
            "a1662ab2-9d34-4e53-ba8b-2639b9e20857": {"ac": 3, "dc": 3}  # Maximize performance
        },
        "de830923-a562-41af-a086-e3a2c6bad2da": {  # Energy Saver settings
            "13d09884-f74e-474a-a852-b6bde8ad03a8": {"ac": 100, "dc": 100},  # Display brightness weight
            "5c5bb349-ad29-4ee2-9d0b-2b25270f7a81": {"ac": 0, "dc": 0},      # Energy Saver Policy (Off)
            "e69653ca-cf7f-4f05-aa73-cb833fa90ad4": {"ac": 100, "dc": 100}   # Charge level
        },
        "2a737441-1930-4402-8d77-b2bebba308a": {  # USB Power Management
            "48e6b7a6-50f5-4782-a5d4-53bb80f7e226": {"ac": 0, "dc": 0}  # USB selective suspend (Off)
        },
        "7516b95f-f776-4464-bc83-06167f40cc99": {  # Adaptive Display
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 0, "dc": 0}  # Adaptive brightness (Off)
        },
        "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e": {  # AMD Power Slider
            "38cab4d5-db09-449f-9db5-1c91c909b6d4": {"ac": 3, "dc": 3},  # PMF Controller - Best performance
            "7ec1751b-60ed-4588-afb5-9819d3d77d90": {"ac": 3, "dc": 3}   # Overlay - Best performance
        }
    }
    
    def __init__(self):
        """Initialize power plan manager."""
        self.current_plan = None
        self._ensure_power_plans_exist()
    
    def _run_powercfg(self, args: List[str]) -> Tuple[int, str, str]:
        """Execute une commande powercfg."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                ["powercfg"] + args,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            stdout = process.stdout if process.stdout else ""
            stderr = process.stderr if process.stderr else ""
            
            return process.returncode, stdout, stderr
            
        except Exception as e:
            logger.error(f"Error running powercfg: {e}")
            return 1, "", str(e)
    
    def _configure_power_settings(self, guid: str, settings: dict, subgroup: str) -> None:
        """Configure both AC and DC power settings for a subgroup."""
        for setting, value in settings.items():
            if isinstance(value, dict) and "ac" in value and "dc" in value:
                # Set AC power setting (plugged in)
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, subgroup, setting, str(value["ac"])])
                if returncode == 0:
                    logger.info(f"✓ {setting} (AC) configuré à {value['ac']}")
                else:
                    logger.error(f"✗ Échec configuration {setting} (AC): {stderr}")
                
                # Set DC power setting (on battery)
                returncode, stdout, stderr = self._run_powercfg(["/setdcvalueindex", guid, subgroup, setting, str(value["dc"])])
                if returncode == 0:
                    logger.info(f"✓ {setting} (DC) configuré à {value['dc']}")
                else:
                    logger.error(f"✗ Échec configuration {setting} (DC): {stderr}")
            else:
                # Regular setting (same for both AC and DC)
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, subgroup, setting, str(value)])
                if returncode == 0:
                    logger.info(f"✓ {setting} configuré à {value}")
                else:
                    logger.error(f"✗ Échec configuration {setting}: {stderr}")
    
    def _configure_boost_plan(self, guid: str) -> None:
        """Configure maximum performance settings for Boost plan."""
        try:
            logger.info("=== Configuring Boost power plan for maximum performance ===")
            logger.info("Profile description:")
            logger.info("- CPU: Maximum performance (100% min/max)")
            logger.info("- CPU Boost: Aggressive mode with maximum boost")
            logger.info("- GPU: Maximum performance")
            logger.info("- Display: Adaptive off, 100% brightness")
            logger.info("- Sleep: Never")
            logger.info("- PCI Express: Maximum performance")
            logger.info("- Energy Saver: Disabled")
            logger.info("- USB: Maximum performance")
            logger.info("- AMD Power: Best performance")
            logger.info(f"Power plan GUID: {guid}")
            
            # Configure processor settings
            logger.info("Configuring processor settings...")
            processor_subgroup = "54533251-82be-4824-96c1-47b60b740d00"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[processor_subgroup], processor_subgroup)
            
            # Configure display settings
            logger.info("Configuring display settings...")
            display_subgroup = "3c0bc021-c8a8-4e07-a973-6b14bcb2b7e"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[display_subgroup], display_subgroup)
            
            # Configure sleep settings
            logger.info("Configuring sleep settings...")
            sleep_subgroup = "238c9fa8-0aad-41ed-83f4-97be242c8f20"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[sleep_subgroup], sleep_subgroup)
            
            # Configure PCI Express settings
            logger.info("Configuring PCI Express settings...")
            pci_subgroup = "501a4d13-42af-4429-9fd1-a8218c2682e0"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[pci_subgroup], pci_subgroup)
            
            # Configure Graphics Power Management
            logger.info("Configuring Graphics Power Management...")
            gpu_subgroup = "e276e160-7cb0-43c6-b20b-73f5dce39954"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[gpu_subgroup], gpu_subgroup)
            
            # Configure Energy Saver settings
            logger.info("Configuring Energy Saver settings...")
            energy_subgroup = "de830923-a562-41af-a086-e3a2c6bad2da"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[energy_subgroup], energy_subgroup)
            
            # Configure USB Power Management
            logger.info("Configuring USB Power Management...")
            usb_subgroup = "2a737441-1930-4402-8d77-b2bebba308a"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[usb_subgroup], usb_subgroup)
            
            # Configure Adaptive Display
            logger.info("Configuring Adaptive Display...")
            adaptive_subgroup = "7516b95f-f776-4464-bc83-06167f40cc99"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[adaptive_subgroup], adaptive_subgroup)
            
            # Configure AMD Power Slider
            logger.info("Configuring AMD Power Slider...")
            amd_subgroup = "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e"
            self._configure_power_settings(guid, self.BOOST_SETTINGS[amd_subgroup], amd_subgroup)
            
            # Verify applied settings
            logger.info("Verifying applied settings...")
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode == 0:
                logger.info("Current Boost plan configuration:")
                logger.info(stdout)
            else:
                logger.error(f"Verification failed: {stderr}")
            
            # Apply changes
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Boost plan activated successfully")
            else:
                logger.error(f"✗ Failed to activate plan: {stderr}")
            
            logger.info("=== Boost plan configuration completed ===")
            
        except Exception as e:
            logger.error(f"Error configuring Boost plan: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _configure_balanced_plan(self, guid: str) -> None:
        """Configure balanced settings for Balanced plan."""
        try:
            logger.info("=== Configuring Balanced power plan for daily use ===")
            logger.info("Profile description:")
            logger.info("- CPU: Balanced performance (10% min, 99% max)")
            logger.info("- CPU Boost: Enabled with moderate boost")
            logger.info("- GPU: Optimized power savings")
            logger.info("- Display: Adaptive enabled, 70% brightness on AC, 50% on battery")
            logger.info("- Sleep: 60min on AC, 10min on battery")
            logger.info("- PCI Express: Moderate power savings")
            logger.info("- Energy Saver: Aggressive on battery only")
            logger.info("- USB: Moderate power savings")
            logger.info("- AMD Power: Better performance on AC, Better battery on DC")
            logger.info(f"Power plan GUID: {guid}")
            
            # Configure processor settings
            logger.info("Configuring processor settings...")
            processor_subgroup = "54533251-82be-4824-96c1-47b60b740d00"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[processor_subgroup], processor_subgroup)
            
            # Configure display settings
            logger.info("Configuring display settings...")
            display_subgroup = "3c0bc021-c8a8-4e07-a973-6b14bcb2b7e"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[display_subgroup], display_subgroup)
            
            # Configure sleep settings
            logger.info("Configuring sleep settings...")
            sleep_subgroup = "238c9fa8-0aad-41ed-83f4-97be242c8f20"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[sleep_subgroup], sleep_subgroup)
            
            # Configure PCI Express settings
            logger.info("Configuring PCI Express settings...")
            pci_subgroup = "501a4d13-42af-4429-9fd1-a8218c2682e0"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[pci_subgroup], pci_subgroup)
            
            # Configure Graphics Power Management
            logger.info("Configuring Graphics Power Management...")
            gpu_subgroup = "e276e160-7cb0-43c6-b20b-73f5dce39954"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[gpu_subgroup], gpu_subgroup)
            
            # Configure Energy Saver settings
            logger.info("Configuring Energy Saver settings...")
            energy_subgroup = "de830923-a562-41af-a086-e3a2c6bad2da"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[energy_subgroup], energy_subgroup)
            
            # Configure USB Power Management
            logger.info("Configuring USB Power Management...")
            usb_subgroup = "2a737441-1930-4402-8d77-b2bebba308a"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[usb_subgroup], usb_subgroup)
            
            # Configure Adaptive Display
            logger.info("Configuring Adaptive Display...")
            adaptive_subgroup = "7516b95f-f776-4464-bc83-06167f40cc99"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[adaptive_subgroup], adaptive_subgroup)
            
            # Configure AMD Power Slider
            logger.info("Configuring AMD Power Slider...")
            amd_subgroup = "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e"
            self._configure_power_settings(guid, self.BALANCED_SETTINGS[amd_subgroup], amd_subgroup)
            
            # Verify applied settings
            logger.info("Verifying applied settings...")
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode == 0:
                logger.info("Current Balanced plan configuration:")
                logger.info(stdout)
            else:
                logger.error(f"Verification failed: {stderr}")
            
            # Apply changes
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Balanced plan activated successfully")
            else:
                logger.error(f"✗ Failed to activate plan: {stderr}")
            
            logger.info("=== Balanced plan configuration completed ===")
            
        except Exception as e:
            logger.error(f"Error configuring Balanced plan: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _configure_silent_plan(self, guid: str) -> None:
        """Configure maximum power saving settings for Silent plan."""
        try:
            logger.info("=== Configuring Silent power plan for maximum power saving ===")
            logger.info("Profile description:")
            logger.info("- CPU: Power saving mode (5% min/30% max)")
            logger.info("- CPU Boost: Disabled")
            logger.info("- GPU: Force power-saving mode")
            logger.info("- Display: Turn off after 3min")
            logger.info("- Sleep: Sleep after 3min")
            logger.info("- PCI Express: Maximum power savings")
            logger.info("- Energy Saver: Aggressive power saving")
            logger.info("- USB: Maximum power savings")
            logger.info("- Adaptive Display: Enabled")
            logger.info(f"Power plan GUID: {guid}")
            
            # Configure processor settings
            logger.info("Configuring processor settings...")
            processor_subgroup = "54533251-82be-4824-96c1-47b60b740d00"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[processor_subgroup], processor_subgroup)
            
            # Configure display settings
            logger.info("Configuring display settings...")
            display_subgroup = "3c0bc021-c8a8-4e07-a973-6b14bcb2b7e"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[display_subgroup], display_subgroup)
            
            # Configure sleep settings
            logger.info("Configuring sleep settings...")
            sleep_subgroup = "238c9fa8-0aad-41ed-83f4-97be242c8f20"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[sleep_subgroup], sleep_subgroup)
            
            # Configure PCI Express settings
            logger.info("Configuring PCI Express settings...")
            pci_subgroup = "501a4d13-42af-4429-9fd1-a8218c2682e0"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[pci_subgroup], pci_subgroup)
            
            # Configure Graphics Power Management
            logger.info("Configuring Graphics Power Management...")
            gpu_subgroup = "e276e160-7cb0-43c6-b20b-73f5dce39954"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[gpu_subgroup], gpu_subgroup)
            
            # Configure Energy Saver settings
            logger.info("Configuring Energy Saver settings...")
            energy_subgroup = "de830923-a562-41af-a086-e3a2c6bad2da"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[energy_subgroup], energy_subgroup)
            
            # Configure USB Power Management
            logger.info("Configuring USB Power Management...")
            usb_subgroup = "2a737441-1930-4402-8d77-b2bebba308a"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[usb_subgroup], usb_subgroup)
            
            # Configure Adaptive Display
            logger.info("Configuring Adaptive Display...")
            adaptive_subgroup = "7516b95f-f776-4464-bc83-06167f40cc99"
            self._configure_power_settings(guid, self.SILENT_SETTINGS[adaptive_subgroup], adaptive_subgroup)
            
            # Verify applied settings
            logger.info("Verifying applied settings...")
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode == 0:
                logger.info("Current Silent plan configuration:")
                logger.info(stdout)
            else:
                logger.error(f"Verification failed: {stderr}")
            
            # Apply changes
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Silent plan activated successfully")
            else:
                logger.error(f"✗ Failed to activate plan: {stderr}")
            
            logger.info("=== Silent plan configuration completed ===")
            
        except Exception as e:
            logger.error(f"Error configuring Silent plan: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _ensure_power_plans_exist(self):
        """S'assure que tous les plans d'alimentation nécessaires existent."""
        for profile_name, guid in self.POWER_PLANS.items():
            # Vérifie si le plan existe déjà
            returncode, stdout, _ = self._run_powercfg(["/list"])
            if guid.lower() not in stdout.lower():
                if profile_name == "Boost":
                    # Duplique le plan Ultimate Performance
                    returncode, stdout, _ = self._run_powercfg(["/duplicatescheme", guid])
                    if returncode == 0 and stdout:
                        # Extrait le nouveau GUID
                        new_guid = None
                        for line in stdout.split('\n'):
                            if line.strip():
                                parts = line.split()
                                if len(parts) > 3:
                                    new_guid = parts[3]
                                    break
                        
                        if new_guid:
                            # Met à jour le GUID dans notre dictionnaire
                            self.POWER_PLANS[profile_name] = new_guid
                            # Renomme le plan
                            self._run_powercfg(["/changename", new_guid, f"Framework - {profile_name}", 
                                              "Power plan optimized for maximum performance"])
                            # Configure les paramètres de performance maximale
                            self._configure_boost_plan(new_guid)
    
    def apply_power_plan(self, profile_name: str) -> bool:
        """Applique un plan d'alimentation Windows."""
        try:
            if profile_name not in self.POWER_PLANS:
                logger.error(f"Invalid power plan profile: {profile_name}")
                return False
            
            guid = self.POWER_PLANS[profile_name]
            logger.info(f"=== Application du profil {profile_name} ===")
            logger.info(f"GUID: {guid}")
            
            # Configurer les paramètres selon le profil
            if profile_name == "Boost":
                logger.info("Profil Boost détecté - Configuration des paramètres de performance maximale")
                self._configure_boost_plan(guid)
            elif profile_name == "Balanced":
                logger.info("Profil Balanced détecté - Configuration des paramètres équilibrés")
                self._configure_balanced_plan(guid)
            elif profile_name == "Silent":
                logger.info("Profil Silent détecté - Configuration des paramètres d'économie d'énergie")
                self._configure_silent_plan(guid)
            
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            
            if returncode != 0:
                logger.error(f"✗ Échec activation du plan {profile_name}: {stderr}")
                return False
            
            self.current_plan = profile_name
            logger.info(f"✓ Plan {profile_name} appliqué avec succès")
            
            # Vérifier le plan actif
            returncode, stdout, stderr = self._run_powercfg(["/getactivescheme"])
            if returncode == 0:
                logger.info(f"Plan actif après application: {stdout}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying Windows power plan: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def cleanup(self) -> None:
        """Nettoyer les plans d'alimentation."""
        # Rien à nettoyer car nous utilisons les plans Windows par défaut
        pass 

class PowerProfile:
    def __init__(self, name: str, tdp: int, cpu_power: int, gpu_power: int, 
                 boost_enabled: bool, fan_mode: str, fan_curve: Dict[str, int], **kwargs):
        self.name = name
        self.tdp = tdp
        self.cpu_power = cpu_power
        self.gpu_power = gpu_power
        self.boost_enabled = boost_enabled
        self.fan_mode = fan_mode
        self.fan_curve = fan_curve
        self.additional_settings = kwargs

class PowerManager:
    def __init__(self, model: LaptopModel):
        self.model = model
        self.windows_power = WindowsPowerPlanManager()
        self.current_profile = None
        self.ryzenadj = False

        # Setup RyzenAdj if AMD model
        if "AMD" in model.name:
            self._setup_ryzenadj()

    def _setup_ryzenadj(self) -> None:
        """Configure RyzenAdj."""
        try:
            ryzenadj_path = get_resource_path("libs/ryzenadj.exe")
            if Path(ryzenadj_path).exists():
                self.ryzenadj = True
                logger.info("RyzenAdj configured successfully")
            else:
                logger.warning("RyzenAdj not found, AMD-specific features will be disabled")
        except Exception as e:
            logger.error(f"Error setting up RyzenAdj: {e}")

    async def apply_profile(self, profile: PowerProfile) -> bool:
        """Apply a complete profile including Windows power plan."""
        try:
            logger.info(f"\n=== Applying {profile.name} Profile ===")
            
            # Log AMD-specific parameters if available
            if hasattr(profile, 'stapm_limit'):
                logger.info("AMD Power Settings:")
                logger.info(f"- STAPM Limit: {profile.stapm_limit} mW")
                logger.info(f"- Fast Limit: {profile.fast_limit} mW")
                logger.info(f"- Slow Limit: {profile.slow_limit} mW")
                logger.info(f"- TCTL Temp: {profile.tctl_temp}°C")
                logger.info(f"- VRM Current: {profile.vrm_current} mA")
                logger.info(f"- VRM Max Current: {profile.vrmmax_current} mA")
                logger.info(f"- VRM SoC Current: {profile.vrmsoc_current} mA")
                logger.info(f"- VRM SoC Max Current: {profile.vrmsocmax_current} mA")
            
            # Log Intel-specific parameters if available
            if hasattr(profile, 'pl1'):
                logger.info("Intel Power Settings:")
                logger.info(f"- PL1 (Sustained): {profile.pl1} W")
                logger.info(f"- PL2 (Boost): {profile.pl2} W")
                logger.info(f"- Tau: {profile.tau} seconds")
                logger.info(f"- CPU Core Offset: {profile.cpu_core_offset} mV")
                logger.info(f"- GPU Core Offset: {profile.gpu_core_offset} mV")
                logger.info(f"- Max Frequency: {profile.max_frequency}")

            # Apply Windows power plan first
            if not self.windows_power.apply_power_plan(profile.name):
                logger.error(f"Failed to apply Windows power plan for profile: {profile.name}")
                return False

            # Apply model-specific settings
            if "AMD" in self.model.name and self.ryzenadj:
                success = await self._apply_ryzenadj_profile(profile)
                if not success:
                    logger.error("Failed to apply RyzenAdj profile")
                    return False
            elif "INTEL" in self.model.name:
                await self._apply_throttlestop_profile(profile)
            
            self.current_profile = profile
            logger.info(f"✓ Successfully applied complete power profile: {profile.name}")
            logger.info("=== Profile application completed ===\n")
            return True

        except Exception as e:
            logger.error(f"Error applying complete power profile: {e}")
            return False

    async def _apply_ryzenadj_profile(self, profile: PowerProfile) -> bool:
        """Apply profile using RyzenAdj."""
        try:
            # Load AMD profiles
            profiles_path = get_resource_path("configs/profiles.json")
            if not Path(profiles_path).exists():
                logger.error("Profiles configuration file not found")
                return False

            with open(profiles_path) as f:
                profiles_config = json.load(f)
                model_key = "16_AMD" if "16" in self.model.name else "13_AMD"
                amd_profiles = profiles_config["amd_profiles"][model_key]
                profile_name = profile.name.lower()
                if profile_name not in amd_profiles:
                    logger.error(f"Profile {profile.name} not found in AMD profiles")
                    return False
                profile_settings = amd_profiles[profile_name]
            
            # Build command with all parameters
            ryzenadj_path = get_resource_path("libs/ryzenadj.exe")
            if not Path(ryzenadj_path).exists():
                logger.error("RyzenAdj executable not found")
                return False

            # Build PowerShell command to run RyzenAdj with admin rights
            cmd_args = []
            for param_name, param_key in RYZENADJ_PARAMS:
                if param_key in profile_settings:
                    cmd_args.append(f"--{param_name}={profile_settings[param_key]}")

            powershell_cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f"Start-Process -FilePath '{ryzenadj_path}' -ArgumentList '{' '.join(cmd_args)}' -Verb RunAs -Wait -WindowStyle Hidden"
            ]
            
            # Configure process to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Run command
            process = await asyncio.create_subprocess_exec(
                *powershell_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                cwd=str(Path(ryzenadj_path).parent)
            )
            stdout_bytes, stderr_bytes = await process.communicate()

            # Decode output
            stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""
            
            if process.returncode != 0:
                logger.error(f"RyzenAdj command failed: {stderr}")
                return False
            
            logger.info("RyzenAdj profile applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying RyzenAdj profile: {e}")
            return False

    async def _apply_throttlestop_profile(self, profile: PowerProfile) -> None:
        """Apply profile using ThrottleStop."""
        try:
            # Load Intel profiles
            profiles_path = get_resource_path("configs/profiles.json")
            if not Path(profiles_path).exists():
                logger.error("Profiles configuration file not found")
                return

            with open(profiles_path) as f:
                profiles_config = json.load(f)
                intel_profiles = profiles_config["intel_profiles"]["13_INTEL"]
                if profile.name.lower() not in intel_profiles:
                    logger.error(f"Profile {profile.name} not found in Intel profiles")
                    return
                profile_settings = intel_profiles[profile.name.lower()]
                
            # ThrottleStop implementation will be added later
            logger.warning("ThrottleStop support not implemented yet")
        except Exception as e:
            logger.error(f"Error applying ThrottleStop profile: {e}")

    def get_current_profile(self) -> Optional[PowerProfile]:
        """Retourne le profil actuellement appliqué."""
        return self.current_profile

    def cleanup(self) -> None:
        """Nettoyer les ressources."""
        if hasattr(self, 'windows_power'):
            self.windows_power.cleanup() 