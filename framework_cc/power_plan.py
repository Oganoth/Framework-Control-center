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
    
    # Paramètres de performance maximale pour le mode Boost
    BOOST_SETTINGS = {
        "SUB_PROCESSOR": {
            "PROCTHROTTLEMIN": 100,             # Fréquence minimale du processeur à 100%
            "PROCTHROTTLEMAX": 100,             # Fréquence maximale du processeur à 100%
            "PERFBOOSTMODE": 2,                 # Mode Boost agressif
            "PERFBOOSTPOL": 100                 # Politique de boost maximale
        }
    }
    
    # Paramètres équilibrés pour le mode Balanced
    BALANCED_SETTINGS = {
        "SUB_PROCESSOR": {
            "PROCTHROTTLEMIN": 30,              # Fréquence minimale du processeur à 30%
            "PROCTHROTTLEMAX": 95,              # Fréquence maximale du processeur à 95%
            "PERFBOOSTMODE": 1,                 # Mode Boost modéré
            "PERFBOOSTPOL": 50                  # Politique de boost équilibrée
        }
    }
    
    # Paramètres d'économie d'énergie pour le mode Silent
    SILENT_SETTINGS = {
        "SUB_PROCESSOR": {
            "PROCTHROTTLEMIN": 5,               # Fréquence minimale du processeur à 5%
            "PROCTHROTTLEMAX": 50,              # Fréquence maximale du processeur à 50%
            "PERFBOOSTMODE": 0,                 # Mode Boost désactivé
            "PERFBOOSTPOL": 0                   # Politique de boost désactivée
        },
        "SUB_SLEEP": {
            "STANDBYIDLE": 300,                 # Mise en veille après 5 minutes d'inactivité
            "HYBRIDSLEEP": 1,                   # Active la mise en veille hybride
            "HIBERNATEIDLE": 900                # Hibernation après 15 minutes
        },
        "SUB_VIDEO": {
            "VIDEOIDLE": 60,                    # Éteint l'écran après 1 minute
            "ADAPTBRIGHT": 1                    # Active la luminosité adaptative
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
                startupinfo=startupinfo
            )
            
            stdout = process.stdout if process.stdout else ""
            stderr = process.stderr if process.stderr else ""
            
            return process.returncode, stdout, stderr
            
        except Exception as e:
            logger.error(f"Error running powercfg: {e}")
            return 1, "", str(e)
    
    def _configure_boost_plan(self, guid: str) -> None:
        """Configure les paramètres de performance maximale pour le plan Boost."""
        try:
            logger.info("=== Configuration du plan Boost pour performances maximales ===")
            logger.info(f"GUID du plan: {guid}")
            
            # Configurer les paramètres du processeur
            logger.info("Configuration des paramètres du processeur...")
            for setting, value in self.BOOST_SETTINGS["SUB_PROCESSOR"].items():
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, "SUB_PROCESSOR", setting, str(value)])
                if returncode == 0:
                    logger.info(f"✓ {setting} configuré à {value}")
                else:
                    logger.error(f"✗ Échec configuration {setting}: {stderr}")
            
            # Vérifier les paramètres appliqués
            logger.info("Vérification des paramètres appliqués...")
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode == 0:
                logger.info("Configuration actuelle du plan Boost:")
                logger.info(stdout)
            else:
                logger.error(f"Échec de la vérification: {stderr}")
            
            # Appliquer les changements
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Plan Boost activé avec succès")
            else:
                logger.error(f"✗ Échec activation du plan: {stderr}")
            
            logger.info("=== Configuration du plan Boost terminée ===")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du plan Boost: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _configure_balanced_plan(self, guid: str) -> None:
        """Configure les paramètres équilibrés pour le plan Balanced."""
        try:
            logger.info("=== Configuration du plan Balanced pour utilisation quotidienne ===")
            logger.info(f"GUID du plan: {guid}")
            
            # Configurer les paramètres du processeur
            logger.info("Configuration des paramètres du processeur...")
            for setting, value in self.BALANCED_SETTINGS["SUB_PROCESSOR"].items():
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, "SUB_PROCESSOR", setting, str(value)])
                if returncode == 0:
                    logger.info(f"✓ {setting} configuré à {value}")
                else:
                    logger.error(f"✗ Échec configuration {setting}: {stderr}")
            
            # Vérifier les paramètres appliqués
            logger.info("Vérification des paramètres appliqués...")
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode == 0:
                logger.info("Configuration actuelle du plan Balanced:")
                logger.info(stdout)
            else:
                logger.error(f"Échec de la vérification: {stderr}")
            
            # Appliquer les changements
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Plan Balanced activé avec succès")
            else:
                logger.error(f"✗ Échec activation du plan: {stderr}")
            
            logger.info("=== Configuration du plan Balanced terminée ===")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du plan Balanced: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _configure_silent_plan(self, guid: str) -> None:
        """Configure les paramètres d'économie d'énergie maximale pour le plan Silent."""
        try:
            logger.info("=== Configuration du plan Silent pour économie d'énergie maximale ===")
            logger.info(f"GUID du plan: {guid}")
            
            # Configurer les paramètres du processeur
            logger.info("Configuration des paramètres du processeur...")
            for setting, value in self.SILENT_SETTINGS["SUB_PROCESSOR"].items():
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, "SUB_PROCESSOR", setting, str(value)])
                if returncode == 0:
                    logger.info(f"✓ {setting} configuré à {value}")
                else:
                    logger.error(f"✗ Échec configuration {setting}: {stderr}")
            
            # Configurer les paramètres de mise en veille
            logger.info("Configuration des paramètres de mise en veille...")
            for setting, value in self.SILENT_SETTINGS["SUB_SLEEP"].items():
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, "SUB_SLEEP", setting, str(value)])
                if returncode == 0:
                    logger.info(f"✓ {setting} configuré à {value}")
                else:
                    logger.error(f"✗ Échec configuration {setting}: {stderr}")
            
            # Configurer les paramètres d'affichage
            logger.info("Configuration des paramètres d'affichage...")
            for setting, value in self.SILENT_SETTINGS["SUB_VIDEO"].items():
                returncode, stdout, stderr = self._run_powercfg(["/setacvalueindex", guid, "SUB_VIDEO", setting, str(value)])
                if returncode == 0:
                    logger.info(f"✓ {setting} configuré à {value}")
                else:
                    logger.error(f"✗ Échec configuration {setting}: {stderr}")
            
            # Vérifier les paramètres appliqués
            logger.info("Vérification des paramètres appliqués...")
            returncode, stdout, stderr = self._run_powercfg(["/query", guid])
            if returncode == 0:
                logger.info("Configuration actuelle du plan Silent:")
                logger.info(stdout)
            else:
                logger.error(f"Échec de la vérification: {stderr}")
            
            # Appliquer les changements
            returncode, stdout, stderr = self._run_powercfg(["/setactive", guid])
            if returncode == 0:
                logger.info("✓ Plan Silent activé avec succès")
            else:
                logger.error(f"✗ Échec activation du plan: {stderr}")
            
            logger.info("=== Configuration du plan Silent terminée ===")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du plan Silent: {e}")
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
        """Applique un profil complet incluant le plan d'alimentation Windows."""
        try:
            # Applique d'abord le plan d'alimentation Windows
            if not self.windows_power.apply_power_plan(profile.name):
                logger.error(f"Failed to apply Windows power plan for profile: {profile.name}")
                return False

            # Applique les paramètres spécifiques au modèle
            if "AMD" in self.model.name and self.ryzenadj:
                success = await self._apply_ryzenadj_profile(profile)
                if not success:
                    logger.error("Failed to apply RyzenAdj profile")
                    return False
            elif "INTEL" in self.model.name:
                await self._apply_throttlestop_profile(profile)
            
            self.current_profile = profile
            logger.info(f"Successfully applied complete power profile: {profile.name}")
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