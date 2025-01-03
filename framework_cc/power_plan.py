"""Module de gestion des plans d'alimentation Windows."""

import logging
import subprocess
import json
import asyncio
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

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
            "893dee8e-2bef-41e0-89c6-b55d0929964c": {"ac": 5, "dc": 5},     # Minimum processor state
            "bc5038f7-23e0-4960-96da-33abaf5935ec": {"ac": 30, "dc": 30},   # Maximum processor state
            "be337238-0d82-4146-a960-4f3749d470c7": {"ac": 0, "dc": 0},     # Performance boost mode (Disabled)
            "45bcc044-d885-43e2-8605-ee0ec6e96b59": {"ac": 0, "dc": 0},     # Performance boost policy (Disabled)
            "94d3a615-a899-4ac5-ae2b-e4d8f634367f": {"ac": 0, "dc": 0},     # System cooling policy (Passive)
            "4b92d758-5a24-4851-a470-815d78aee119": {"ac": 40, "dc": 40},   # Processor idle demote threshold
            "7b224883-b3cc-4d79-819f-8374152cbe7c": {"ac": 60, "dc": 60}    # Processor idle promote threshold
        },
        "7516b95f-f776-4464-8c53-06167f40cc99": {  # Display
            "aded5e82-b909-4619-9949-f5d71dac0bcb": {"ac": 30, "dc": 30},   # Display brightness
            "f1fbfde2-a960-4165-9f88-50667911ce96": {"ac": 20, "dc": 20},   # Dimmed display brightness
            "17aaa29b-8b43-4b94-aafe-35f64daaf1ee": {"ac": 60, "dc": 30},   # Dim display after (seconds)
            "3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e": {"ac": 180, "dc": 120}, # Turn off display after
            "90959d22-d6a1-49b9-af93-bce885ad335b": {"ac": 1, "dc": 1},     # Adaptive display (On)
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 1, "dc": 1},     # Enable adaptive brightness (On)
            "a9ceb8da-cd46-44fb-a98b-02af69de4623": {"ac": 1, "dc": 1}      # Allow display required policy
        },
        "238c9fa8-0aad-41ed-83f4-97be242c8f20": {  # Sleep Settings
            "29f6c1db-86da-48c5-9fdb-f2b67b1f44da": {"ac": 180, "dc": 180}, # Sleep after (corrigé)
            "9d7815a6-7ee4-497e-8888-515a05f02364": {"ac": 3600, "dc": 1800}, # Hibernate timeout
            "94ac6d29-73ce-41a6-809f-6363ba21b47e": {"ac": 0, "dc": 0},     # Hybrid sleep
            "bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d": {"ac": 0, "dc": 0}      # Allow wake timers (corrigé)
        },
        "501a4d13-42af-4429-9fd1-a8218c268e20": {  # PCI Express (corrigé)
            "ee12f906-d277-404b-b6da-e5fa1a576df5": {"ac": 2, "dc": 2}      # Link State Power Management
        },
        "e276e160-7cb0-43c6-b20b-73f5dce39954": {  # Switchable Dynamic Graphics
            "a1662ab2-9d34-4e53-ba8b-2639b9e20857": {"ac": 0, "dc": 0}      # Force power-saving graphics
        },
        "de830923-a562-41af-a086-e3a2c6bad2da": {  # Energy Saver settings
            "13d09884-f74e-474a-a852-b6bde8ad03a8": {"ac": 30, "dc": 30},   # Display brightness weight
            "5c5bb349-ad29-4ee2-9d0b-2b25270f7a81": {"ac": 1, "dc": 1},     # Energy Saver Policy (1 = Aggressive)
            "e69653ca-cf7f-4f05-aa73-cb833fa90ad4": {"ac": 100, "dc": 100}  # Charge level
        },
        "2a737441-1930-4402-8d77-b2bebba308a3": {  # USB Power Management (corrigé)
            "48e6b7a6-50f5-4782-a5d4-53bb8f07e226": {"ac": 0, "dc": 1},     # USB selective suspend (corrigé)
            "0853a681-27c8-4100-a2fd-82013e970683": {"ac": 50, "dc": 50}    # Hub Selective Suspend Timeout
        },
        "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e": {  # AMD Power Slider
            "38cab4d5-db09-449f-9db5-1c91c909b6d4": {"ac": 1, "dc": 1},     # PMF Controller - Battery saver (corrigé)
            "7ec1751b-60ed-4588-afb5-9819d3d77d90": {"ac": 1, "dc": 1}      # Overlay - Battery saver (corrigé)
        },
        "0012ee47-9041-4b5d-9b77-535fba8b1442": {  # Hard disk settings
            "6738e2c4-e8a5-4a42-b16a-e040e769756e": {"ac": 30, "dc": 30},   # Turn off hard disk after (seconds)
            "d639518a-e56d-4345-8af2-b9f32fb26109": {"ac": 100, "dc": 100}  # Primary NVMe Idle Timeout (milliseconds)
        },
        "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1": {  # Wireless Adapter Settings
            "12bbebe6-58d6-4636-95bb-3217ef867c1a": {"ac": 2, "dc": 3}      # Power Saving Mode (Medium/Maximum)
        },
        "9596fb26-9850-41fd-ac3e-f7c3c00afd4b": {  # Multimedia settings
            "10778347-1370-4ee0-8bbd-33bdacaade49": {"ac": 0, "dc": 0},     # Video playback quality bias (Power saving)
            "34c7b99f-9a6d-4b3c-8dc7-b6693b78cef4": {"ac": 2, "dc": 2}      # When playing video (Optimize power savings)
        },
        "5fb4938d-1ee8-4b0f-9a3c-5036b0ab995c": {  # Graphics settings
            "dd848b2a-8a5d-4451-9ae2-39cd41658f6c": {"ac": 1, "dc": 1}      # GPU preference policy (Low Power)
        }
    }
    
    # Paramètres pour le plan Balanced (utilisation quotidienne)
    BALANCED_SETTINGS = {
        "54533251-82be-4824-96c1-47b60b740d00": {  # Processor Power Management
            "893dee8e-2bef-41e0-89c6-b55d0929964c": {"ac": 10, "dc": 10},   # Minimum processor state
            "bc5038f7-23e0-4960-96da-33abaf5935ec": {"ac": 99, "dc": 99},   # Maximum processor state
            "be337238-0d82-4146-a960-4f3749d470c7": {"ac": 1, "dc": 1},     # Performance boost mode (Enabled)
            "45bcc044-d885-43e2-8605-ee0ec6e96b59": {"ac": 50, "dc": 50},   # Performance boost policy (Balanced)
            "94d3a615-a899-4ac5-ae2b-e4d8f634367f": {"ac": 1, "dc": 1},     # System cooling policy (Active)
            "4b92d758-5a24-4851-a470-815d78aee119": {"ac": 20, "dc": 20},   # Processor idle demote threshold
            "7b224883-b3cc-4d79-819f-8374152cbe7c": {"ac": 40, "dc": 40}    # Processor idle promote threshold
        },
        "7516b95f-f776-4464-8c53-06167f40cc99": {  # Display
            "aded5e82-b909-4619-9949-f5d71dac0bcb": {"ac": 70, "dc": 50},   # Display brightness
            "f1fbfde2-a960-4165-9f88-50667911ce96": {"ac": 40, "dc": 30},   # Dimmed display brightness
            "17aaa29b-8b43-4b94-aafe-35f64daaf1ee": {"ac": 300, "dc": 180}, # Dim display after (seconds)
            "3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e": {"ac": 600, "dc": 300}, # Turn off display after
            "90959d22-d6a1-49b9-af93-bce885ad335b": {"ac": 1, "dc": 1},     # Adaptive display (On)
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 1, "dc": 1},     # Enable adaptive brightness (On)
            "a9ceb8da-cd46-44fb-a98b-02af69de4623": {"ac": 1, "dc": 1}      # Allow display required policy
        },
        "238c9fa8-0aad-41ed-83f4-97be242c8f20": {  # Sleep Settings
            "29f6c1db-86da-48c5-9fad-628d2a5290dc": {"ac": 3600, "dc": 600}, # Sleep idle timeout
            "9d7815a6-7ee4-497e-8888-515a05f02364": {"ac": 14400, "dc": 3600}, # Hibernate timeout
            "94ac6d29-73ce-41a6-809f-6363ba21b47e": {"ac": 0, "dc": 0},     # Hybrid sleep
            "bd3b718a-0d82-4146-a960-4f3749d470c7": {"ac": 1, "dc": 1}      # Allow wake timers (Enable)
        },
        "501a4d13-42af-4429-9fd1-a8218c2682e0": {  # PCI Express
            "ee12f906-d277-404b-b6da-e5fa1a576df5": {"ac": 1, "dc": 1}      # Link State Power Management (Moderate)
        },
        "e276e160-7cb0-43c6-b20b-73f5dce39954": {  # Switchable Dynamic Graphics
            "a1662ab2-9d34-4e53-ba8b-2639b9e20857": {"ac": 2, "dc": 1}      # Optimize performance (AC) / Optimize power savings (DC)
        },
        "de830923-a562-41af-a086-e3a2c6bad2da": {  # Energy Saver settings
            "13d09884-f74e-474a-a852-b6bde8ad03a8": {"ac": 70, "dc": 50},   # Display brightness weight
            "5c5bb349-ad29-4ee2-9d0b-2b25270f7a81": {"ac": 0, "dc": 1},     # Energy Saver Policy (Off for AC, On for DC)
            "e69653ca-cf7f-4f05-aa73-cb833fa90ad4": {"ac": 100, "dc": 100}  # Charge level
        },
        "2a737441-1930-4402-8d77-b2bebba308a": {  # USB Power Management
            "48e6b7a6-50f5-4782-a5d4-53bb80f7e226": {"ac": 1, "dc": 1},     # USB selective suspend - Minimum power savings
            "0853a681-27c8-4100-a2fd-82013e970683": {"ac": 100, "dc": 100}  # Hub Selective Suspend Timeout (milliseconds)
        },
        "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e": {  # AMD Power Slider
            "38cab4d5-db09-449f-9db5-1c91c909b6d4": {"ac": 2, "dc": 1},     # PMF Controller - Better performance/Better battery
            "7ec1751b-60ed-4588-afb5-9819d3d77d90": {"ac": 2, "dc": 1}      # Overlay - Better performance/Better battery
        },
        "0012ee47-9041-4b5d-9b77-535fba8b1442": {  # Hard disk settings
            "6738e2c4-e8a5-4a42-b16a-e040e769756e": {"ac": 600, "dc": 300}, # Turn off hard disk after (seconds)
            "d639518a-e56d-4345-8af2-b9f32fb26109": {"ac": 300, "dc": 300}  # Primary NVMe Idle Timeout (milliseconds)
        },
        "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1": {  # Wireless Adapter Settings
            "12bbebe6-58d6-4636-95bb-3217ef867c1a": {"ac": 1, "dc": 2}      # Power Saving Mode (Low/Medium)
        },
        "9596fb26-9850-41fd-ac3e-f7c3c00afd4b": {  # Multimedia settings
            "10778347-1370-4ee0-8bbd-33bdacaade49": {"ac": 1, "dc": 0},     # Video playback quality bias (Performance/Power saving)
            "34c7b99f-9a6d-4b3c-8dc7-b6693b78cef4": {"ac": 1, "dc": 1}      # When playing video (Balanced)
        },
        "5fb4938d-1ee8-4b0f-9a3c-5036b0ab995c": {  # Graphics settings
            "dd848b2a-8a5d-4451-9ae2-39cd41658f6c": {"ac": 0, "dc": 1}      # GPU preference policy (None/Low Power)
        }
    }
    
    # Paramètres pour le plan Boost (performances maximales)
    BOOST_SETTINGS = {
        "54533251-82be-4824-96c1-47b60b740d00": {  # Processor Power Management
            "893dee8e-2bef-41e0-89c6-b55d0929964c": {"ac": 100, "dc": 100}, # Minimum processor state
            "bc5038f7-23e0-4960-96da-33abaf5935ec": {"ac": 100, "dc": 100}, # Maximum processor state
            "be337238-0d82-4146-a960-4f3749d470c7": {"ac": 2, "dc": 2},     # Performance boost mode (Aggressive)
            "45bcc044-d885-43e2-8605-ee0ec6e96b59": {"ac": 100, "dc": 100}, # Performance boost policy (Maximum)
            "94d3a615-a899-4ac5-ae2b-e4d8f634367f": {"ac": 1, "dc": 1},     # System cooling policy (Active)
            "4b92d758-5a24-4851-a470-815d78aee119": {"ac": 10, "dc": 10},   # Processor idle demote threshold
            "7b224883-b3cc-4d79-819f-8374152cbe7c": {"ac": 20, "dc": 20}    # Processor idle promote threshold
        },
        "7516b95f-f776-4464-8c53-06167f40cc99": {  # Display
            "aded5e82-b909-4619-9949-f5d71dac0bcb": {"ac": 100, "dc": 100}, # Display brightness
            "f1fbfde2-a960-4165-9f88-50667911ce96": {"ac": 100, "dc": 100}, # Dimmed display brightness
            "17aaa29b-8b43-4b94-aafe-35f64daaf1ee": {"ac": 0, "dc": 0},     # Dim display after (Never)
            "3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e": {"ac": 0, "dc": 0},     # Turn off display after (Never)
            "90959d22-d6a1-49b9-af93-bce885ad335b": {"ac": 0, "dc": 0},     # Adaptive display (Off)
            "fbd9aa66-9553-4097-ba44-ed6e9d65eab8": {"ac": 0, "dc": 0},     # Enable adaptive brightness (Off)
            "a9ceb8da-cd46-44fb-a98b-02af69de4623": {"ac": 1, "dc": 1}      # Allow display required policy
        },
        "238c9fa8-0aad-41ed-83f4-97be242c8f20": {  # Sleep Settings
            "29f6c1db-86da-48c5-9fad-628d2a5290dc": {"ac": 0, "dc": 0},     # Sleep idle timeout (Never)
            "9d7815a6-7ee4-497e-8888-515a05f02364": {"ac": 0, "dc": 0},     # Hibernate timeout (Never)
            "94ac6d29-73ce-41a6-809f-6363ba21b47e": {"ac": 0, "dc": 0},     # Hybrid sleep (Off)
            "bd3b718a-0d82-4146-a960-4f3749d470c7": {"ac": 1, "dc": 1}      # Allow wake timers (Enable)
        },
        "501a4d13-42af-4429-9fd1-a8218c2682e0": {  # PCI Express
            "ee12f906-d277-404b-b6da-e5fa1a576df5": {"ac": 0, "dc": 0}      # Link State Power Management (Off)
        },
        "e276e160-7cb0-43c6-b20b-73f5dce39954": {  # Switchable Dynamic Graphics
            "a1662ab2-9d34-4e53-ba8b-2639b9e20857": {"ac": 3, "dc": 3}      # Maximize performance
        },
        "de830923-a562-41af-a086-e3a2c6bad2da": {  # Energy Saver settings
            "13d09884-f74e-474a-a852-b6bde8ad03a8": {"ac": 100, "dc": 100}, # Display brightness weight
            "5c5bb349-ad29-4ee2-9d0b-2b25270f7a81": {"ac": 0, "dc": 0},     # Energy Saver Policy (Off)
            "e69653ca-cf7f-4f05-aa73-cb833fa90ad4": {"ac": 100, "dc": 100}  # Charge level
        },
        "2a737441-1930-4402-8d77-b2bebba308a": {  # USB Power Management
            "48e6b7a6-50f5-4782-a5d4-53bb80f7e226": {"ac": 0, "dc": 0},     # USB selective suspend (Off)
            "0853a681-27c8-4100-a2fd-82013e970683": {"ac": 0, "dc": 0}      # Hub Selective Suspend Timeout (Off)
        },
        "c763b4ec-0e50-4b6b-9bed-2b92a6ee884e": {  # AMD Power Slider
            "38cab4d5-db09-449f-9db5-1c91c909b6d4": {"ac": 3, "dc": 3},     # PMF Controller - Best performance
            "7ec1751b-60ed-4588-afb5-9819d3d77d90": {"ac": 3, "dc": 3}      # Overlay - Best performance
        },
        "0012ee47-9041-4b5d-9b77-535fba8b1442": {  # Hard disk settings
            "6738e2c4-e8a5-4a42-b16a-e040e769756e": {"ac": 0, "dc": 0},     # Turn off hard disk after (Never)
            "d639518a-e56d-4345-8af2-b9f32fb26109": {"ac": 0, "dc": 0}      # Primary NVMe Idle Timeout (Never)
        },
        "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1": {  # Wireless Adapter Settings
            "12bbebe6-58d6-4636-95bb-3217ef867c1a": {"ac": 0, "dc": 0}      # Power Saving Mode (Maximum Performance)
        },
        "9596fb26-9850-41fd-ac3e-f7c3c00afd4b": {  # Multimedia settings
            "10778347-1370-4ee0-8bbd-33bdacaade49": {"ac": 1, "dc": 1},     # Video playback quality bias (Performance)
            "34c7b99f-9a6d-4b3c-8dc7-b6693b78cef4": {"ac": 0, "dc": 0}      # When playing video (Optimize quality)
        },
        "5fb4938d-1ee8-4b0f-9a3c-5036b0ab995c": {  # Graphics settings
            "dd848b2a-8a5d-4451-9ae2-39cd41658f6c": {"ac": 0, "dc": 0}      # GPU preference policy (None)
        }
    }
    
    def __init__(self):
        """Initialize power plan manager."""
        self.current_plan = None
        
        # Vérifier les privilèges administrateur
        if not self._check_admin_privileges():
            raise RuntimeError("Cette application nécessite des privilèges administrateur")
        
        # Vérifier la compatibilité avant de continuer
        if not self._verify_windows_compatibility():
            raise RuntimeError("Système non compatible avec les paramètres d'alimentation")
            
        self._ensure_power_plans_exist()
    
    def _run_powercfg(self, args: List[str]) -> Tuple[int, str, str]:
        """Execute une commande powercfg avec les privilèges administrateur."""
        try:
            # Créer les infos de démarrage pour masquer la fenêtre
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Préparer la commande avec runas pour les privilèges admin
            command = ["powercfg"] + args
            
            # Exécuter avec les privilèges élevés
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.HIGH_PRIORITY_CLASS,
                # Utiliser shell=True pour hériter des privilèges admin du processus parent
                shell=True
            )
            
            stdout = process.stdout if process.stdout else ""
            stderr = process.stderr if process.stderr else ""
            
            # Vérifier si l'erreur est liée aux privilèges
            if process.returncode != 0 and "Access is denied" in stderr:
                logger.error("Privilèges administrateur requis pour powercfg")
                logger.error("Assurez-vous de lancer l'application en tant qu'administrateur")
                return 1, "", "Privilèges administrateur requis"
            
            return process.returncode, stdout, stderr
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de powercfg: {e}")
            return 1, "", str(e)
    
    def _configure_power_settings(self, guid: str, settings: dict, subgroup: str) -> None:
        """Configure both AC and DC power settings for a subgroup."""
        try:
            # Vérifier d'abord si le sous-groupe existe
            returncode, stdout, stderr = self._run_powercfg(["/query", guid, subgroup])
            if returncode != 0:
                logger.warning(f"Sous-groupe {subgroup} non trouvé, ignoré")
                return

            for setting, value in settings.items():
                # Vérifier si le paramètre existe
                returncode, stdout, stderr = self._run_powercfg(["/query", guid, subgroup, setting])
                if returncode != 0:
                    logger.warning(f"Paramètre {setting} non trouvé dans {subgroup}, ignoré")
                    continue

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
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du sous-groupe {subgroup}: {e}")

    def _verify_power_settings(self, guid: str) -> None:
        """Vérifie les paramètres d'alimentation disponibles."""
        try:
            # Obtenir tous les paramètres disponibles
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode != 0:
                logger.error(f"Impossible de lire les paramètres du plan {guid}")
                return

            # Analyser la sortie pour trouver les GUIDs valides
            valid_guids = {}
            current_subgroup = None
            
            for line in stdout.split('\n'):
                if "Subgroup GUID:" in line:
                    current_subgroup = line.split(':')[1].strip()
                elif "Power Setting GUID:" in line and current_subgroup:
                    setting_guid = line.split(':')[1].strip()
                    if current_subgroup not in valid_guids:
                        valid_guids[current_subgroup] = []
                    valid_guids[current_subgroup].append(setting_guid)

            logger.info("GUIDs valides trouvés:")
            for subgroup, settings in valid_guids.items():
                logger.info(f"Sous-groupe: {subgroup}")
                for setting in settings:
                    logger.info(f"  - Paramètre: {setting}")

            return valid_guids
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des paramètres: {e}")
            return None

    def _ensure_power_plans_exist(self) -> None:
        """Ensure all required power plans exist."""
        try:
            # Vérifier et créer les plans si nécessaire
            for name, guid in self.POWER_PLANS.items():
                returncode, stdout, stderr = self._run_powercfg(["/query", guid])
                
                if returncode != 0:
                    # Le plan n'existe pas, le créer à partir du plan équilibré
                    logger.info(f"Création du plan {name}...")
                    returncode, stdout, stderr = self._run_powercfg(["/duplicatescheme", self.POWER_PLANS["Balanced"], guid])
                    
                    if returncode == 0:
                        # Renommer le plan
                        self._run_powercfg(["/changename", guid, name])
                        logger.info(f"✓ Plan {name} créé")
                    else:
                        logger.error(f"✗ Échec création plan {name}: {stderr}")
                else:
                    logger.info(f"✓ Plan {name} existe déjà")
                    
                # Vérifier les paramètres disponibles
                self._verify_power_settings(guid)
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des plans: {e}")
            raise
    
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
        """Nettoyer les ressources."""
        if hasattr(self, 'windows_power'):
            self.windows_power.cleanup() 

    def _verify_windows_compatibility(self) -> bool:
        """Vérifie la compatibilité avec Windows 11 et l'existence des GUIDs."""
        try:
            logger.info("Vérification de la compatibilité Windows 11...")
            
            # Vérifier la version de Windows
            if sys.platform != 'win32':
                logger.error("Ce script nécessite Windows")
                return False
                
            win_ver = sys.getwindowsversion()
            if win_ver.major < 10 or (win_ver.major == 10 and win_ver.build < 22000):
                logger.error("Ce script nécessite Windows 11 (build 22000 ou supérieur)")
                return False
            
            logger.info(f"Version Windows détectée: {win_ver.major}.{win_ver.build}")
            
            # Vérifier l'existence des plans d'alimentation
            logger.info("Vérification des plans d'alimentation...")
            for plan_name, guid in self.POWER_PLANS.items():
                returncode, stdout, stderr = self._run_powercfg(["/query", guid])
                if returncode != 0:
                    logger.error(f"Plan {plan_name} (GUID: {guid}) non trouvé")
                    return False
                logger.info(f"✓ Plan {plan_name} vérifié")
            
            # Vérifier les sous-groupes essentiels
            essential_subgroups = [
                "54533251-82be-4824-96c1-47b60b740d00",  # Processor
                "7516b95f-f776-4464-8c53-06167f40cc99",  # Display
                "238c9fa8-0aad-41ed-83f4-97be242c8f20",  # Sleep
                "e276e160-7cb0-43c6-b20b-73f5dce39954"   # Graphics
            ]
            
            logger.info("Vérification des sous-groupes essentiels...")
            for subgroup in essential_subgroups:
                returncode, stdout, stderr = self._run_powercfg(["/query", self.POWER_PLANS["Balanced"], subgroup])
                if returncode != 0:
                    logger.error(f"Sous-groupe {subgroup} non trouvé")
                    return False
                logger.info(f"✓ Sous-groupe {subgroup} vérifié")
            
            logger.info("✓ Système compatible avec tous les paramètres")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de compatibilité: {e}")
            return False

    def _check_admin_privileges(self) -> bool:
        """Vérifie si le processus a les privilèges administrateur."""
        try:
            # Tester une commande powercfg qui nécessite des privilèges admin
            returncode, stdout, stderr = self._run_powercfg(["/query"])
            if returncode == 0:
                logger.info("✓ Privilèges administrateur vérifiés")
                return True
            else:
                logger.error("✗ Privilèges administrateur manquants")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des privilèges: {e}")
            return False

    def _configure_balanced_plan(self, guid: str) -> None:
        """Configure balanced settings for daily use."""
        try:
            logger.info("=== Configuration du profil Balanced ===")
            
            # Configurer chaque groupe de paramètres
            for subgroup, settings in self.BALANCED_SETTINGS.items():
                self._configure_power_settings(guid, settings, subgroup)
                
            # Appliquer les changements
            logger.info("Application des changements...")
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Plan Balanced activé")
            else:
                logger.error(f"✗ Échec activation: {stderr}")
            
            # Forcer le rechargement
            self._run_powercfg(["/s", guid])
            
        except Exception as e:
            logger.error(f"Erreur configuration Balanced: {e}")
            raise
            
    def _configure_boost_plan(self, guid: str) -> None:
        """Configure maximum performance settings for Boost plan."""
        try:
            logger.info("=== Configuration du profil Boost ===")
            
            # Configurer chaque groupe de paramètres
            for subgroup, settings in self.BOOST_SETTINGS.items():
                self._configure_power_settings(guid, settings, subgroup)
                
            # Appliquer les changements
            logger.info("Application des changements...")
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Plan Boost activé")
            else:
                logger.error(f"✗ Échec activation: {stderr}")
            
            # Forcer le rechargement
            self._run_powercfg(["/s", guid])
            
        except Exception as e:
            logger.error(f"Erreur configuration Boost: {e}")
            raise
            
    def _configure_silent_plan(self, guid: str) -> None:
        """Configure maximum power saving settings for Silent plan."""
        try:
            logger.info("=== Configuration du profil Silent ===")
            
            # Configurer chaque groupe de paramètres
            for subgroup, settings in self.SILENT_SETTINGS.items():
                self._configure_power_settings(guid, settings, subgroup)
                
            # Appliquer les changements
            logger.info("Application des changements...")
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Plan Silent activé")
            else:
                logger.error(f"✗ Échec activation: {stderr}")
            
            # Forcer le rechargement
            self._run_powercfg(["/s", guid])
            
        except Exception as e:
            logger.error(f"Erreur configuration Silent: {e}")
            raise

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