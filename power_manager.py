import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import json
import os
import ctypes
import winreg

logger = logging.getLogger(__name__)

class PowerManager:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.current_profile = settings.get("ryzenadj_profile", "Balanced")
        self.profiles = settings.get("power_profiles", {})
        
        # Vérifier et extraire RyzenADJ si nécessaire
        self.ryzenadj_path = self._ensure_ryzenadj()
        if not self.ryzenadj_path:
            raise RuntimeError("Impossible de trouver ou d'extraire RyzenADJ")
        
    def _ensure_ryzenadj(self) -> Optional[str]:
        """Vérifie et prépare RyzenADJ"""
        try:
            # 1. Vérifier dans le dossier de l'application
            app_path = Path(__file__).parent
            ryzenadj_dir = app_path / "ryzenadj"
            ryzenadj_exe = ryzenadj_dir / "ryzenadj.exe"
            
            if not ryzenadj_dir.exists():
                ryzenadj_dir.mkdir(exist_ok=True)
            
            # 2. Vérifier si RyzenADJ existe déjà
            if ryzenadj_exe.exists():
                logger.info(f"RyzenADJ trouvé à {ryzenadj_exe}")
                return str(ryzenadj_exe)
            
            # 3. Chercher dans le dossier Framework
            framework_path = Path("C:/Program Files/Framework/FrameworkService/ryzenadj.exe")
            if framework_path.exists():
                logger.info(f"RyzenADJ trouvé à {framework_path}")
                return str(framework_path)
            
            # 4. Extraire RyzenADJ depuis les ressources
            resources_dir = app_path / "resources"
            ryzenadj_zip = resources_dir / "ryzenadj.zip"
            
            if ryzenadj_zip.exists():
                logger.info("Extraction de RyzenADJ depuis les ressources...")
                import zipfile
                with zipfile.ZipFile(ryzenadj_zip, 'r') as zip_ref:
                    zip_ref.extractall(ryzenadj_dir)
                
                if ryzenadj_exe.exists():
                    logger.info(f"RyzenADJ extrait avec succès vers {ryzenadj_exe}")
                    return str(ryzenadj_exe)
                
            # 5. Télécharger RyzenADJ si nécessaire
            logger.info("Téléchargement de RyzenADJ...")
            import requests
            ryzenadj_url = "https://github.com/FlyGoat/RyzenAdj/releases/download/v0.13.0/ryzenadj-win64.zip"
            
            response = requests.get(ryzenadj_url)
            if response.status_code == 200:
                # Sauvegarder le zip
                resources_dir.mkdir(exist_ok=True)
                ryzenadj_zip.write_bytes(response.content)
                
                # Extraire
                with zipfile.ZipFile(ryzenadj_zip, 'r') as zip_ref:
                    zip_ref.extractall(ryzenadj_dir)
                
                if ryzenadj_exe.exists():
                    logger.info(f"RyzenADJ téléchargé et extrait avec succès vers {ryzenadj_exe}")
                    return str(ryzenadj_exe)
                
            logger.error("Impossible de trouver ou d'installer RyzenADJ")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la préparation de RyzenADJ: {e}")
            return None
        
    def get_profile_settings(self, profile_name: str, model: str) -> Dict[str, Any]:
        """Retourne les paramètres pour un profil donné"""
        if model == "Framework 13 AMD":
            profiles = {
                "Silent": {
                    "tdp": 15,
                    "fast_limit": 20,
                    "slow_limit": 15,
                    "boost_enabled": False,
                    "current_limit": 150,
                    "temp_limit": 85,
                    "skin_temp": 40,
                    "win_power": 0
                },
                "Balanced": {
                    "tdp": 30,
                    "fast_limit": 35,
                    "slow_limit": 30,
                    "boost_enabled": True,
                    "current_limit": 180,
                    "temp_limit": 90,
                    "skin_temp": 45,
                    "win_power": 1
                },
                "Boost": {
                    "tdp": 60,
                    "fast_limit": 70,
                    "slow_limit": 60,
                    "boost_enabled": True,
                    "current_limit": 200,
                    "temp_limit": 95,
                    "skin_temp": 50,
                    "win_power": 2
                }
            }
        else:  # Framework 16 AMD
            profiles = {
                "Silent": {
                    "tdp": 30,
                    "fast_limit": 35,
                    "slow_limit": 30,
                    "boost_enabled": False,
                    "current_limit": 180,
                    "temp_limit": 95,
                    "skin_temp": 45,
                    "win_power": 0
                },
                "Balanced": {
                    "tdp": 95,
                    "fast_limit": 95,
                    "slow_limit": 95,
                    "boost_enabled": True,
                    "current_limit": 180,
                    "temp_limit": 95,
                    "skin_temp": 50,
                    "win_power": 1
                },
                "Boost": {
                    "tdp": 120,
                    "fast_limit": 140,
                    "slow_limit": 120,
                    "boost_enabled": True,
                    "current_limit": 200,
                    "temp_limit": 100,
                    "skin_temp": 50,
                    "win_power": 2
                }
            }
        
        return profiles.get(profile_name, profiles["Balanced"])
        
    def apply_profile(self, profile_name: str, model: str, test_mode: bool = False) -> bool:
        """Applique un profil de puissance"""
        try:
            # Obtenir les paramètres du profil
            profile = self.get_profile_settings(profile_name, model)
            
            # Construire la commande RyzenADJ
            ryzenadj_path = self.get_ryzenadj_path()
            if not os.path.exists(ryzenadj_path):
                logger.error(f"RyzenADJ non trouvé à {ryzenadj_path}")
                return False
            
            cmd = [
                ryzenadj_path,
                f"--tctl-temp={profile['temp_limit']}",
                f"--stapm-limit={profile['tdp']}000",
                f"--fast-limit={profile['fast_limit']}000",
                f"--slow-limit={profile['slow_limit']}000",
                f"--vrm-current={profile['current_limit']}000",
                f"--skin-temp-limit={profile['skin_temp']}"
            ]
            
            if not profile.get('boost_enabled', True):
                cmd.append("--power-saving")
            
            # En mode test, juste vérifier que la commande peut s'exécuter
            if test_mode:
                cmd.append("--info")
            
            # Créer startupinfo pour cacher la fenêtre
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=5
            )
            
            # Logger la sortie
            if result.stdout:
                logger.info(f"Sortie RyzenADJ: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"Erreur RyzenADJ: {result.stderr.strip()}")
            
            # En mode test, vérifier seulement que la commande s'exécute sans erreur
            if test_mode:
                return result.returncode == 0
            
            # En mode normal, sauvegarder le profil si succès
            if result.returncode == 0:
                self.settings["ryzenadj_profile"] = profile_name
                self.save_settings()
                logger.info(f"Profil {profile_name} appliqué avec succès")
                return True
            else:
                logger.error(f"Échec de l'application du profil {profile_name}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de l'application du profil")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'application du profil: {e}")
            return False
            
    def get_ryzenadj_path(self) -> str:
        """Retourne le chemin vers RyzenADJ"""
        if not self.ryzenadj_path:
            self.ryzenadj_path = self._ensure_ryzenadj()
        return self.ryzenadj_path or "ryzenadj.exe"
        
    def save_settings(self) -> None:
        """Sauvegarde les paramètres"""
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres: {e}")
            
    def get_windows_power_guid(self, power_level: int) -> str:
        """Retourne le GUID du plan d'alimentation Windows"""
        power_guids = {
            0: "a1841308-3541-4fab-bc81-f71556f20b4a",  # Économie d'énergie
            1: "381b4222-f694-41f0-9685-ff5bb260df2e",  # Équilibré
            2: "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"   # Haute performance
        }
        return power_guids.get(power_level, power_guids[1])  # Par défaut: Équilibré 

    def apply_power_profile(self, profile_name: str, model: str) -> None:
        """Applique un profil de puissance"""
        try:
            if profile_name not in self.profiles:
                logger.error(f"Profil {profile_name} non trouvé")
                return
                
            profile = self.profiles[profile_name]
            logger.info(f"Application du profil {profile_name} pour le modèle {model}")
            
            # Appliquer les paramètres RyzenADJ
            self._apply_ryzenadj_settings(profile)
            
            # Appliquer les paramètres Windows
            self._set_windows_power_settings(profile)
            
            # Mettre à jour le profil actuel
            self.current_profile = profile_name
            self.settings["ryzenadj_profile"] = profile_name
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application du profil: {e}")
            
    def _apply_ryzenadj_settings(self, profile: Dict[str, Any]) -> None:
        """Applique les paramètres RyzenADJ"""
        try:
            # Construire la commande RyzenADJ
            cmd = [
                self.ryzenadj_path,
                f"--stapm-limit={profile['tdp']}",
                f"--fast-limit={profile['fast_limit']}",
                f"--slow-limit={profile['slow_limit']}",
                f"--tctl-temp={profile['temp_limit']}",
                f"--apu-skin-temp={profile['skin_temp']}",
                f"--vrm-current={profile['current_limit'] * 1000}"  # Conversion en mA
            ]
            
            # Exécuter la commande
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"RyzenADJ error: {result.stderr}")
                
            logger.info(f"Paramètres RyzenADJ appliqués: {cmd}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des paramètres RyzenADJ: {e}")
            
    def _set_windows_power_settings(self, profile: Dict[str, Any]) -> None:
        """Configure les paramètres d'alimentation Windows"""
        try:
            # Configurer le boost CPU
            self._set_cpu_boost(profile.get('boost_enabled', True))
            
            # Configurer le thème Windows si nécessaire
            if profile.get('change_theme', False):
                self._set_dark_theme(profile.get('dark_theme', True))
                
            logger.info(f"Paramètres Windows appliqués pour le profil")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration des paramètres Windows: {e}")

    def _set_battery_saver(self, enable: bool) -> None:
        """Active ou désactive le mode économie de batterie"""
        try:
            logger.info(f"🔋 Tentative de {'activation' if enable else 'désactivation'} du mode batterie")
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Battery"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "BatterySaverEnabled", 0, winreg.REG_DWORD, 1 if enable else 0)
            logger.info("✅ Mode batterie configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification du mode batterie: {e}")

    def _set_brightness(self, level: int) -> None:
        """Définit la luminosité de l'écran"""
        try:
            logger.info(f"💡 Tentative de réglage de la luminosité à {level}%")
            subprocess.run([
                "powershell",
                "-Command",
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"
            ], check=True)
            logger.info("✅ Luminosité réglée avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors du changement de luminosité: {e}")

    def _set_refresh_rate(self, rate: int) -> None:
        """Définit le taux de rafraîchissement de l'écran"""
        try:
            logger.info(f"🔄 Tentative de réglage du taux de rafraîchissement à {rate}Hz")
            subprocess.run([
                "powershell",
                "-Command",
                f"Set-DisplayResolution -Frequency {rate}"
            ], check=True)
            logger.info("✅ Taux de rafraîchissement configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors du changement du taux de rafraîchissement: {e}")

    def _set_power_plan(self, plan_index: int) -> None:
        """Définit le plan d'alimentation"""
        try:
            logger.info(f"⚡ Tentative de changement du plan d'alimentation vers {['Économie', 'Équilibré', 'Performance'][plan_index]}")
            guid = self.get_windows_power_guid(plan_index)
            subprocess.run([
                "powercfg",
                "/setactive",
                guid
            ], check=True)
            logger.info("✅ Plan d'alimentation configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors du changement de plan d'alimentation: {e}")

    def _set_bluetooth(self, enable: bool) -> None:
        """Active ou désactive le Bluetooth"""
        try:
            logger.info(f"📶 Tentative de {'activation' if enable else 'désactivation'} du Bluetooth")
            action = "enable" if enable else "disable"
            subprocess.run([
                "powershell",
                "-Command",
                f"Set-Service -Name 'bthserv' -StartupType {action}"
            ], check=True)
            logger.info("✅ Bluetooth configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification du Bluetooth: {e}")

    def _set_location(self, enable: bool) -> None:
        """Active ou d��sactive la localisation"""
        try:
            logger.info(f"📍 Tentative de {'activation' if enable else 'désactivation'} de la localisation")
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Allow" if enable else "Deny")
            logger.info("✅ Localisation configurée avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification de la localisation: {e}")

    def _set_background_apps(self, enable: bool) -> None:
        """Active ou désactive les applications en arrière-plan"""
        try:
            logger.info(f"🔄 Tentative de {'activation' if enable else 'désactivation'} des apps en arrière-plan")
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "GlobalUserDisabled", 0, winreg.REG_DWORD, 0 if enable else 1)
            logger.info("✅ Apps en arrière-plan configurées avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification des apps en arrière-plan: {e}")

    def _set_power_timeouts(self, screen_timeout: int, sleep_timeout: int) -> None:
        """Définit les délais d'extinction d'écran et de mise en veille"""
        try:
            logger.info(f"⏰ Tentative de configuration des délais - écran: {screen_timeout}min, veille: {sleep_timeout}min")
            # Convertir les minutes en secondes
            screen_seconds = screen_timeout * 60
            sleep_seconds = sleep_timeout * 60
            
            # Appliquer pour batterie et secteur
            subprocess.run(["powercfg", "/change", "monitor-timeout-ac", str(screen_timeout)], check=True)
            subprocess.run(["powercfg", "/change", "monitor-timeout-dc", str(screen_timeout)], check=True)
            subprocess.run(["powercfg", "/change", "standby-timeout-ac", str(sleep_timeout)], check=True)
            subprocess.run(["powercfg", "/change", "standby-timeout-dc", str(sleep_timeout)], check=True)
            logger.info("✅ Délais configurés avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification des délais: {e}")

    def _set_dark_mode(self, enable: bool) -> bool:
        """Active ou désactive le mode sombre"""
        try:
            logger.info(f"🌓 Tentative de {'activation' if enable else 'désactivation'} du mode sombre")
            
            # Registre pour le thème des applications
            apps_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, apps_key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0 if enable else 1)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0 if enable else 1)
            
            # Registre pour le thème système
            system_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, system_key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0 if enable else 1)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0 if enable else 1)
            
            logger.info("✅ Mode sombre configuré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification du mode sombre: {e}")
            return False

    def _set_cpu_boost(self, enable: bool, aggressive: bool = False) -> None:
        """Configure le CPU boost"""
        try:
            logger.info(f"⚡ Tentative de configuration du CPU boost - {'activé' if enable else 'désactivé'}{' (agressif)' if aggressive else ''}")
            # Obtenir le GUID du plan actif
            result = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True)
            guid = result.stdout.split()[3]
            
            # Définir le mode boost
            mode = "2" if aggressive else ("1" if enable else "0")
            subprocess.run([
                "powercfg",
                "/setacvalueindex",
                guid,
                "54533251-82be-4824-96c1-47b60b740d00",
                "be337238-0d82-4146-a960-4f3749d470c7",
                mode
            ], check=True)
            
            # Appliquer les modifications
            subprocess.run(["powercfg", "/setactive", guid], check=True)
            logger.info("✅ CPU boost configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification du CPU boost: {e}")

    def _set_processor_states(self, min_state: int, max_state: int) -> None:
        """Configure les états minimum et maximum du processeur"""
        try:
            logger.info(f"💻 Tentative de configuration des états processeur - min: {min_state}%, max: {max_state}%")
            # Obtenir le GUID du plan actif
            result = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True)
            guid = result.stdout.split()[3]
            
            # Définir l'état minimum
            subprocess.run([
                "powercfg",
                "/setacvalueindex",
                guid,
                "54533251-82be-4824-96c1-47b60b740d00",
                "893dee8e-2bef-41e0-89c6-b55d0929964c",
                str(min_state)
            ], check=True)
            
            # Définir l'état maximum
            subprocess.run([
                "powercfg",
                "/setacvalueindex",
                guid,
                "54533251-82be-4824-96c1-47b60b740d00",
                "bc5038f7-23e0-4960-96da-33abaf5935ec",
                str(max_state)
            ], check=True)
            
            # Appliquer les modifications
            subprocess.run(["powercfg", "/setactive", guid], check=True)
            logger.info("✅ États processeur configurés avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la modification des états du processeur: {e}")

    def load_profiles(self, profiles: Dict[str, Any]) -> None:
        """Charge les profils de puissance"""
        try:
            logger.info(f"Chargement des profils: {profiles}")
            self.profiles = profiles
            self.settings["power_profiles"] = profiles
            
            # Appliquer le profil actuel
            current_model = self.settings.get("laptop_model", "model_13_amd")
            self.apply_power_profile(self.current_profile, current_model)
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des profils: {e}")

    def _set_dark_theme(self, enable: bool) -> None:
        """Active ou désactive le thème sombre de Windows"""
        try:
            logger.info(f"🎨 {'Activation' if enable else 'Désactivation'} du thème sombre")
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0 if enable else 1)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0 if enable else 1)
            logger.info("✅ Thème Windows configuré avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors du changement de thème: {e}")