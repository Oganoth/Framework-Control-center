import ctypes
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import json
import threading
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ADLXError(Exception):
    """Base exception for ADLX errors."""
    pass

class ADLXInitError(ADLXError):
    """Exception raised when ADLX initialization fails."""
    pass

class ADLXSettingsError(ADLXError):
    """Exception raised when applying settings fails."""
    pass

class ADLXValidationError(ADLXError):
    """Exception raised when settings validation fails."""
    pass

class TuningMode(Enum):
    """Enum for tuning modes."""
    DEFAULT = auto()
    AUTO = auto()
    UNDERVOLT = auto()
    OVERCLOCK = auto()
    SILENT = auto()
    BALANCED = auto()
    PERFORMANCE = auto()
    EFFICIENCY = auto()

class QualityMode(Enum):
    """Enum for quality modes."""
    OFF = auto()
    PERFORMANCE = auto()
    QUALITY = auto()

@dataclass
class DisplaySettings:
    """Display settings validation."""
    brightness: int
    contrast: int
    saturation: int
    refresh_rate: int

    def __post_init__(self):
        """Validate settings after initialization."""
        if not 0 <= self.brightness <= 100:
            raise ADLXValidationError(f"Brightness must be between 0 and 100, got {self.brightness}")
        if not 0 <= self.contrast <= 100:
            raise ADLXValidationError(f"Contrast must be between 0 and 100, got {self.contrast}")
        if not 0 <= self.saturation <= 100:
            raise ADLXValidationError(f"Saturation must be between 0 and 100, got {self.saturation}")
        if self.refresh_rate not in [60, 120, 165]:
            raise ADLXValidationError(f"Refresh rate must be 60, 120, or 165, got {self.refresh_rate}")

@dataclass
class ThreeDSettings:
    """3D settings validation."""
    anti_aliasing: QualityMode
    anisotropic_filtering: QualityMode
    image_sharpening: int
    radeon_boost: bool
    radeon_chill: bool
    frame_rate_target: int

    def __post_init__(self):
        """Validate settings after initialization."""
        if not isinstance(self.anti_aliasing, QualityMode):
            raise ADLXValidationError(f"Invalid anti-aliasing mode: {self.anti_aliasing}")
        if not isinstance(self.anisotropic_filtering, QualityMode):
            raise ADLXValidationError(f"Invalid anisotropic filtering mode: {self.anisotropic_filtering}")
        if not 0 <= self.image_sharpening <= 100:
            raise ADLXValidationError(f"Image sharpening must be between 0 and 100, got {self.image_sharpening}")
        if not isinstance(self.radeon_boost, bool):
            raise ADLXValidationError(f"Radeon boost must be a boolean, got {self.radeon_boost}")
        if not isinstance(self.radeon_chill, bool):
            raise ADLXValidationError(f"Radeon chill must be a boolean, got {self.radeon_chill}")
        if not 30 <= self.frame_rate_target <= 165:
            raise ADLXValidationError(f"Frame rate target must be between 30 and 165, got {self.frame_rate_target}")

@dataclass
class AutoTuningSettings:
    """Auto tuning settings validation."""
    gpu_tuning: TuningMode
    memory_tuning: TuningMode
    fan_tuning: TuningMode
    power_tuning: TuningMode

    def __post_init__(self):
        """Validate settings after initialization."""
        if not isinstance(self.gpu_tuning, TuningMode):
            raise ADLXValidationError(f"Invalid GPU tuning mode: {self.gpu_tuning}")
        if not isinstance(self.memory_tuning, TuningMode):
            raise ADLXValidationError(f"Invalid memory tuning mode: {self.memory_tuning}")
        if not isinstance(self.fan_tuning, TuningMode):
            raise ADLXValidationError(f"Invalid fan tuning mode: {self.fan_tuning}")
        if not isinstance(self.power_tuning, TuningMode):
            raise ADLXValidationError(f"Invalid power tuning mode: {self.power_tuning}")

@dataclass
class ProfileSettings:
    """Profile settings validation."""
    display: DisplaySettings
    three_d: ThreeDSettings
    auto_tuning: AutoTuningSettings
    last_applied: Optional[datetime] = None

class ADLXWrapper:
    """Wrapper for ADLX SDK functionality."""
    
    def __init__(self):
        """Initialize ADLX wrapper."""
        self.display_lib = None
        self.perf_metrics_lib = None
        self.settings_3d_lib = None
        self.auto_tuning_lib = None
        self.current_profile = None
        self.settings_lock = threading.Lock()
        self.profile_settings = {}
        
        try:
            # Load saved settings
            self._load_saved_settings()
            
            # Load the DLLs
            dll_path = Path("libs/ADLX_SDK_Wrapper/Debug/net6.0").resolve()
            logger.info(f"Looking for ADLX DLLs in: {dll_path.absolute()}")
            if not dll_path.exists():
                raise ADLXInitError(f"ADLX SDK wrapper directory not found: {dll_path}")
            
            # Add DLL directory to path
            os.add_dll_directory(str(dll_path))
            
            dll_files = {
                "display": "ADLX_DisplaySettings.dll",
                "perf": "ADLX_PerformanceMetrics.dll",
                "3d": "ADLX_3DSettings.dll",
                "tuning": "ADLX_AutoTuning.dll"
            }
            
            # Load DLLs
            self.display_lib = self._load_dll(dll_path / dll_files["display"])
            self.perf_metrics_lib = self._load_dll(dll_path / dll_files["perf"])
            self.settings_3d_lib = self._load_dll(dll_path / dll_files["3d"])
            self.auto_tuning_lib = self._load_dll(dll_path / dll_files["tuning"])
            
            # Set up function prototypes
            self._setup_function_prototypes()
            
            logger.info("Successfully loaded ADLX SDK wrapper DLLs")
            
        except Exception as e:
            logger.error(f"Failed to load ADLX SDK wrapper DLLs: {e}", exc_info=True)
            raise ADLXInitError(f"Failed to initialize ADLX: {e}")
            
    def _load_dll(self, dll_path: Path) -> ctypes.CDLL:
        """Load a DLL and return the handle."""
        try:
            logger.debug(f"Loading DLL: {dll_path}")
            return ctypes.CDLL(str(dll_path))
        except Exception as e:
            logger.error(f"Failed to load {dll_path.name}: {e}")
            raise
            
    def _setup_function_prototypes(self):
        """Set up function prototypes for the loaded DLLs."""
        if self.display_lib:
            # Display settings functions
            self.display_lib.GetDisplaySettings.argtypes = []
            self.display_lib.GetDisplaySettings.restype = ctypes.c_int
            self.display_lib.SetDisplaySettings.argtypes = [
                ctypes.c_int,  # brightness
                ctypes.c_int,  # contrast
                ctypes.c_int,  # saturation
                ctypes.c_int   # refresh_rate
            ]
            self.display_lib.SetDisplaySettings.restype = ctypes.c_bool
            
        if self.perf_metrics_lib:
            # Performance metrics functions
            self.perf_metrics_lib.GetGPUMetrics.argtypes = []
            self.perf_metrics_lib.GetGPUMetrics.restype = ctypes.c_int
            
        if self.settings_3d_lib:
            # 3D settings functions
            self.settings_3d_lib.Get3DSettings.argtypes = []
            self.settings_3d_lib.Get3DSettings.restype = ctypes.c_int
            self.settings_3d_lib.Set3DSettings.argtypes = [
                ctypes.c_int,  # anti_aliasing
                ctypes.c_int,  # anisotropic_filtering
                ctypes.c_int,  # image_sharpening
                ctypes.c_bool, # radeon_boost
                ctypes.c_bool, # radeon_chill
                ctypes.c_int   # frame_rate_target
            ]
            self.settings_3d_lib.Set3DSettings.restype = ctypes.c_bool
            
        if self.auto_tuning_lib:
            # Auto tuning functions
            self.auto_tuning_lib.GetAutoTuningSettings.argtypes = []
            self.auto_tuning_lib.GetAutoTuningSettings.restype = ctypes.c_int
            self.auto_tuning_lib.SetAutoTuningSettings.argtypes = [
                ctypes.c_int,  # gpu_tuning
                ctypes.c_int,  # memory_tuning
                ctypes.c_int,  # fan_tuning
                ctypes.c_int   # power_tuning
            ]
            self.auto_tuning_lib.SetAutoTuningSettings.restype = ctypes.c_bool

    def get_display_settings(self) -> Dict[str, int]:
        """Get current display settings."""
        settings = {}
        try:
            if self.display_lib:
                settings = self.display_lib.GetDisplaySettings()
                logger.debug(f"Got display settings: {settings}")
                    
        except Exception as e:
            logger.error(f"Error getting display settings: {e}")
            
        return settings

    def get_performance_metrics(self) -> Dict[str, int]:
        """Get current performance metrics."""
        metrics = {}
        try:
            if self.perf_metrics_lib:
                metrics = self.perf_metrics_lib.GetGPUMetrics()
                logger.debug(f"Got GPU metrics: {metrics}")
                    
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            
        return metrics

    def get_3d_settings(self) -> Dict[str, Any]:
        """Get current 3D settings."""
        settings = {}
        try:
            if self.settings_3d_lib:
                settings = self.settings_3d_lib.Get3DSettings()
                logger.debug(f"Got 3D settings: {settings}")
                    
        except Exception as e:
            logger.error(f"Error getting 3D settings: {e}")
            
        return settings

    def get_auto_tuning_settings(self) -> Dict[str, int]:
        """Get current auto tuning settings."""
        settings = {}
        try:
            if self.auto_tuning_lib:
                settings = self.auto_tuning_lib.GetAutoTuningSettings()
                logger.debug(f"Got auto tuning settings: {settings}")
                    
        except Exception as e:
            logger.error(f"Error getting auto tuning settings: {e}")
            
        return settings

    def cleanup(self):
        """Clean up ADLX resources."""
        try:
            # Clean up managed resources
            if self.display_lib:
                self.display_lib.Dispose()
            if self.perf_metrics_lib:
                self.perf_metrics_lib.Dispose()
            if self.settings_3d_lib:
                self.settings_3d_lib.Dispose()
            if self.auto_tuning_lib:
                self.auto_tuning_lib.Dispose()
                
            logger.info("ADLX resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up ADLX resources: {e}")
            
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 

    def _load_saved_settings(self) -> None:
        """Load saved settings from file."""
        try:
            settings_path = Path("configs/amd_settings.json")
            if settings_path.exists():
                with open(settings_path, "r") as f:
                    saved_settings = json.load(f)
                    
                # Convert saved settings to proper types
                for profile, settings in saved_settings.items():
                    try:
                        # Convert string values to enums for 3D settings
                        three_d_settings = settings.get("3d", {})
                        if "anti_aliasing" in three_d_settings:
                            three_d_settings["anti_aliasing"] = getattr(QualityMode, three_d_settings["anti_aliasing"])
                        if "anisotropic_filtering" in three_d_settings:
                            three_d_settings["anisotropic_filtering"] = getattr(QualityMode, three_d_settings["anisotropic_filtering"])
                        
                        # Convert string values to enums for auto tuning settings
                        auto_tuning_settings = settings.get("auto_tuning", {})
                        if "gpu_tuning" in auto_tuning_settings:
                            auto_tuning_settings["gpu_tuning"] = getattr(TuningMode, auto_tuning_settings["gpu_tuning"])
                        if "memory_tuning" in auto_tuning_settings:
                            auto_tuning_settings["memory_tuning"] = getattr(TuningMode, auto_tuning_settings["memory_tuning"])
                        if "fan_tuning" in auto_tuning_settings:
                            auto_tuning_settings["fan_tuning"] = getattr(TuningMode, auto_tuning_settings["fan_tuning"])
                        if "power_tuning" in auto_tuning_settings:
                            auto_tuning_settings["power_tuning"] = getattr(TuningMode, auto_tuning_settings["power_tuning"])
                        
                        # Create settings objects
                        display = DisplaySettings(**settings.get("display", {}))
                        three_d = ThreeDSettings(**three_d_settings)
                        auto_tuning = AutoTuningSettings(**auto_tuning_settings)
                        
                        self.profile_settings[profile] = ProfileSettings(
                            display=display,
                            three_d=three_d,
                            auto_tuning=auto_tuning
                        )
                        logger.debug(f"Loaded settings for profile: {profile}")
                    except Exception as e:
                        logger.error(f"Error loading settings for profile {profile}: {e}")
                        continue
                        
                logger.info(f"Successfully loaded settings for {len(self.profile_settings)} profiles")
            else:
                logger.warning("No saved settings found, using defaults")
                
        except Exception as e:
            logger.error(f"Error loading saved settings: {e}")

    def _save_settings(self) -> None:
        """Save current settings to file."""
        try:
            settings_path = Path("configs/amd_settings.json")
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert settings to JSON-serializable format
            settings_dict = {}
            for profile, settings in self.profile_settings.items():
                settings_dict[profile] = {
                    "display": {
                        "brightness": settings.display.brightness,
                        "contrast": settings.display.contrast,
                        "saturation": settings.display.saturation,
                        "refresh_rate": settings.display.refresh_rate
                    },
                    "3d": {
                        "anti_aliasing": settings.three_d.anti_aliasing.name,
                        "anisotropic_filtering": settings.three_d.anisotropic_filtering.name,
                        "image_sharpening": settings.three_d.image_sharpening,
                        "radeon_boost": settings.three_d.radeon_boost,
                        "radeon_chill": settings.three_d.radeon_chill,
                        "frame_rate_target": settings.three_d.frame_rate_target
                    },
                    "auto_tuning": {
                        "gpu_tuning": settings.auto_tuning.gpu_tuning.name,
                        "memory_tuning": settings.auto_tuning.memory_tuning.name,
                        "fan_tuning": settings.auto_tuning.fan_tuning.name,
                        "power_tuning": settings.auto_tuning.power_tuning.name
                    }
                }
            
            with open(settings_path, "w") as f:
                json.dump(settings_dict, f, indent=4)
                
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def switch_profile(self, profile: str) -> bool:
        """Switch to a different profile and apply its settings."""
        try:
            with self.settings_lock:
                if profile not in self.profile_settings:
                    logger.error(f"Profile not found: {profile}")
                    return False
                
                # Get profile settings
                settings = self.profile_settings[profile]
                
                # Apply settings
                success = self.apply_profile_settings(profile, {
                    "display": settings.display.__dict__,
                    "3d": settings.three_d.__dict__,
                    "auto_tuning": settings.auto_tuning.__dict__
                })
                
                if success:
                    # Update current profile and last applied time
                    self.current_profile = profile
                    settings.last_applied = datetime.now()
                    # Save settings to persist last applied time
                    self._save_settings()
                    logger.info(f"Successfully switched to profile: {profile}")
                    return True
                else:
                    logger.error(f"Failed to switch to profile: {profile}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error switching profile: {e}")
            return False

    def get_current_profile(self) -> Optional[str]:
        """Get the name of the currently active profile."""
        return self.current_profile

    def get_profile_settings(self, profile: str) -> Optional[ProfileSettings]:
        """Get settings for a specific profile."""
        return self.profile_settings.get(profile)

    def update_profile_settings(self, profile: str, settings: Dict[str, Any]) -> bool:
        """Update settings for a specific profile."""
        try:
            with self.settings_lock:
                # Validate new settings
                display = DisplaySettings(**settings.get("display", {}))
                three_d = ThreeDSettings(**settings.get("3d", {}))
                auto_tuning = AutoTuningSettings(**settings.get("auto_tuning", {}))
                
                # Create or update profile settings
                self.profile_settings[profile] = ProfileSettings(
                    display=display,
                    three_d=three_d,
                    auto_tuning=auto_tuning
                )
                
                # Save settings to file
                self._save_settings()
                
                # If this is the current profile, apply settings immediately
                if profile == self.current_profile:
                    return self.switch_profile(profile)
                    
                return True
                
        except Exception as e:
            logger.error(f"Error updating profile settings: {e}")
            return False

    def apply_profile_settings(self, profile: str, settings: Dict[str, Any]) -> bool:
        """Apply profile-specific settings."""
        try:
            if not all([self.display_lib, self.settings_3d_lib, self.auto_tuning_lib]):
                raise ADLXInitError("Not all required ADLX libraries are loaded")

            with self.settings_lock:
                # Validate settings
                try:
                    display_settings = DisplaySettings(**settings.get("display", {}))
                    three_d_settings = ThreeDSettings(**settings.get("3d", {}))
                    auto_tuning_settings = AutoTuningSettings(**settings.get("auto_tuning", {}))
                    profile_settings = ProfileSettings(
                        display=display_settings,
                        three_d=three_d_settings,
                        auto_tuning=auto_tuning_settings
                    )
                except (TypeError, ValueError) as e:
                    raise ADLXValidationError(f"Invalid settings format: {e}")

                # Apply display settings
                self.display_lib.SetDisplaySettings(
                    profile_settings.display.brightness,
                    profile_settings.display.contrast,
                    profile_settings.display.saturation,
                    profile_settings.display.refresh_rate
                )

                # Apply 3D settings
                self.settings_3d_lib.Set3DSettings(
                    profile_settings.three_d.anti_aliasing.value,
                    profile_settings.three_d.anisotropic_filtering.value,
                    profile_settings.three_d.image_sharpening,
                    profile_settings.three_d.radeon_boost,
                    profile_settings.three_d.radeon_chill,
                    profile_settings.three_d.frame_rate_target
                )

                # Apply auto tuning settings
                self.auto_tuning_lib.SetAutoTuningSettings(
                    profile_settings.auto_tuning.gpu_tuning.value,
                    profile_settings.auto_tuning.memory_tuning.value,
                    profile_settings.auto_tuning.fan_tuning.value,
                    profile_settings.auto_tuning.power_tuning.value
                )

                logger.info(f"Successfully applied all settings for {profile} profile")
                # Update profile settings with current values
                self.profile_settings[profile] = profile_settings
                self.profile_settings[profile].last_applied = datetime.now()
                # Save settings to file
                self._save_settings()
                    
                return True

        except Exception as e:
            logger.error(f"Error applying profile settings: {e}")
            return False 