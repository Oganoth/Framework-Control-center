"""Module de gestion des plans d'alimentation Windows."""

import subprocess
from typing import Optional, List, Tuple
from .logger import logger

class PowerPlanManager:
    """Gestionnaire des plans d'alimentation Windows."""
    
    # GUIDs des plans d'alimentation Windows
    POWER_PLANS = {
        "Silent": "a1841308-3541-4fab-bc81-f71556f20b4a",    # Power saver
        "Balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",  # Balanced
        "Boost": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"     # High performance
    }
    
    def __init__(self) -> None:
        """Initialize power plan manager."""
        self.current_profile = None
        self._ensure_power_plans_exist()
    
    def _ensure_power_plans_exist(self) -> None:
        """Ensure all required power plans exist."""
        try:
            # Get list of available power schemes
            returncode, stdout, stderr = self._run_powercfg(["-list"])
            if returncode != 0 or not stdout:
                logger.error(f"Failed to list power schemes: {stderr}")
                return
            
            # Convert stdout to lowercase for case-insensitive comparison
            available_plans = stdout.lower() if stdout else ""
            
            # Check each required plan
            for profile, guid in self.POWER_PLANS.items():
                if guid.lower() not in available_plans:
                    logger.warning(f"Power plan {profile} ({guid}) not found")
                    # Try to restore the default plan
                    restore_code, _, restore_err = self._run_powercfg(["-restoredefaultschemes"])
                    if restore_code != 0:
                        logger.error(f"Failed to restore default power schemes: {restore_err}")
                    else:
                        logger.info("Successfully restored default power schemes")
                    break
            
        except Exception as e:
            logger.error(f"Error checking power plans: {e}")
    
    def _run_powercfg(self, args: List[str]) -> Tuple[int, str, str]:
        """Run powercfg command."""
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
            
            # Ensure stdout and stderr are strings, even if None
            stdout = process.stdout if process.stdout else ""
            stderr = process.stderr if process.stderr else ""
            
            return process.returncode, stdout, stderr
            
        except Exception as e:
            logger.error(f"Error running powercfg: {e}")
            return 1, "", str(e)
    
    def apply_profile(self, profile: str) -> bool:
        """Appliquer un profil de puissance."""
        try:
            if profile not in self.POWER_PLANS:
                logger.error(f"Invalid profile: {profile}")
                return False
            
            # Activer le plan d'alimentation correspondant
            guid = self.POWER_PLANS[profile]
            returncode, stdout, stderr = self._run_powercfg(["-setactive", guid])
            
            if returncode != 0:
                logger.error(f"Failed to set active power scheme: {stderr}")
                return False
            
            self.current_profile = profile
            logger.info(f"Successfully applied power plan for profile: {profile}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying power profile: {e}")
            return False
    
    def cleanup(self) -> None:
        """Nettoyer les plans d'alimentation."""
        # Rien à nettoyer car nous utilisons les plans Windows par défaut
        pass 