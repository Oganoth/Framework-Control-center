"""Power management module for Framework laptops."""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

import requests
from zipfile import ZipFile
from io import BytesIO

from .models import PowerProfile, LaptopModel
from .logger import logger
from .power_plan import PowerPlanManager
from .utils import get_resource_path
from .constants import RYZENADJ_PARAMS, RYZENADJ_DOWNLOAD_URL, REQUIRED_DLLS

class PowerManager:
    """Power management for Framework laptops."""
    def __init__(self, model: LaptopModel) -> None:
        """Initialize power manager."""
        self.model = model
        self.ryzenadj = False
        self.power_plan = PowerPlanManager()
        
        # Setup RyzenAdj if AMD model
        if "AMD" in model.name:
            self._setup_ryzenadj()

    async def apply_profile(self, profile: PowerProfile) -> bool:
        """Apply power profile."""
        try:
            # Apply Windows power plan
            success = self.power_plan.apply_profile(profile.name)
            if not success:
                logger.error("Failed to apply Windows power plan")
                return False
            
            # Apply additional settings based on model
            if "AMD" in self.model.name and self.ryzenadj:
                success = await self._apply_ryzenadj_profile(profile)
                if not success:
                    logger.error("Failed to apply RyzenAdj profile")
                    return False
            elif "INTEL" in self.model.name:
                await self._apply_throttlestop_profile(profile)
            
            logger.info(f"Successfully applied profile: {profile.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying power profile: {e}")
            return False

    def _setup_ryzenadj(self) -> None:
        """Setup RyzenAdj."""
        try:
            ryzenadj_path = get_resource_path("libs/ryzenadj.exe")
            if not Path(ryzenadj_path).exists():
                logger.info("RyzenAdj not found, downloading...")
                self._download_ryzenadj()
            
            # Verify RyzenAdj exists after potential download
            if not Path(ryzenadj_path).exists():
                logger.error("RyzenAdj not found and download failed")
                return
            
            self.ryzenadj = True
            logger.info("RyzenAdj setup complete")
        except Exception as e:
            logger.error(f"Error setting up RyzenAdj: {e}")
            self.ryzenadj = False

    async def _apply_ryzenadj_profile(self, profile: PowerProfile) -> bool:
        """Apply profile using RyzenAdj."""
        try:
            # Load AMD profiles
            profiles_path = get_resource_path("configs/profiles.json")
            if not Path(profiles_path).exists():
                logger.error("Profiles configuration file not found")
                return False

            with open(profiles_path) as f:
                import json
                profiles_config = json.load(f)
                model_key = "16_AMD" if "16" in self.model.name else "13_AMD"
                amd_profiles = profiles_config["amd_profiles"][model_key]
                profile_name = profile.name.lower()
                if profile_name not in amd_profiles:
                    logger.error(f"Profile {profile.name} not found in AMD profiles")
                    return False
                profile_settings = amd_profiles[profile_name]
            
            # Log profile settings
            logger.info("Applying RyzenAdj profile with settings:")
            for key, value in profile_settings.items():
                if key != "name":
                    logger.info("  %s: %s", key, value)
            
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
            
            # Log the full command
            logger.debug(f"Executing command: {' '.join(powershell_cmd)}")
            
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
                cwd=str(Path(ryzenadj_path).parent)  # Set working directory to libs folder
            )
            stdout_bytes, stderr_bytes = await process.communicate()
            
            # Decode output with error handling
            try:
                stdout = stdout_bytes.decode('utf-8') if stdout_bytes else ""
                stderr = stderr_bytes.decode('utf-8') if stderr_bytes else ""
            except UnicodeDecodeError:
                stdout = stdout_bytes.decode('cp1252', errors='replace') if stdout_bytes else ""
                stderr = stderr_bytes.decode('cp1252', errors='replace') if stderr_bytes else ""
            
            # Log command output
            if stdout:
                logger.debug(f"Command stdout: {stdout}")
            if stderr:
                logger.debug(f"Command stderr: {stderr}")
            
            if process.returncode != 0:
                logger.error(f"Command failed with return code {process.returncode}")
                if stderr:
                    logger.error(f"Command error output: {stderr}")
                return False
            
            logger.info("RyzenAdj profile applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error applying RyzenAdj profile: {e}")
            return False

    async def _apply_throttlestop_profile(self, profile: PowerProfile) -> None:
        """Apply profile using ThrottleStop."""
        # Load Intel profiles
        try:
            profiles_path = get_resource_path("configs/profiles.json")
            if not Path(profiles_path).exists():
                logger.error("Profiles configuration file not found")
                return

            with open(profiles_path) as f:
                import json
                profiles_config = json.load(f)
                intel_profiles = profiles_config["intel_profiles"]["13_INTEL"]
                if profile.name.lower() not in intel_profiles:
                    logger.error(f"Profile {profile.name} not found in Intel profiles")
                    return
                profile_settings = intel_profiles[profile.name.lower()]
                
            # ThrottleStop implementation will be added later
            logger.warning("ThrottleStop support not implemented yet")
        except Exception as e:
            logger.error(f"Error loading Intel profiles: {e}")
            raise 

    def _download_ryzenadj(self) -> None:
        """Download and extract RyzenAdj files."""
        try:
            logger.info(f"Downloading RyzenAdj from {RYZENADJ_DOWNLOAD_URL}")
            response = requests.get(RYZENADJ_DOWNLOAD_URL)
            response.raise_for_status()
            
            libs_dir = Path("libs")
            libs_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract and verify each file
            extracted_files = set()
            with ZipFile(BytesIO(response.content)) as zip_file:
                # List all files in ZIP
                files_in_zip = zip_file.namelist()
                logger.debug(f"Files in ZIP: {files_in_zip}")
                
                # Extract files
                for file_info in zip_file.filelist:
                    filename = Path(file_info.filename).name.lower()
                    if filename in {f.lower() for f in REQUIRED_DLLS + ['ryzenadj.exe']}:
                        target_path = libs_dir / Path(file_info.filename).name
                        logger.debug(f"Extracting {file_info.filename} to {target_path}")
                        with zip_file.open(file_info.filename) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                        extracted_files.add(filename)
            
            # Check for missing files
            required_files = {f.lower() for f in REQUIRED_DLLS + ['ryzenadj.exe']}
            missing_files = required_files - extracted_files
            if missing_files:
                logger.error(f"Missing files after extraction: {missing_files}")
                raise FileNotFoundError(f"Missing required files: {missing_files}")
            
            logger.info("RyzenAdj downloaded and extracted successfully")
            
        except Exception as e:
            logger.error(f"Failed to download RyzenAdj: {e}")
            raise 