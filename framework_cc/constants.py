"""Constants for Framework Control Center."""

from pathlib import Path
from typing import Dict, Any

# Directories
LIBS_DIR = Path("libs")
CONFIGS_DIR = Path("configs")
LOGS_DIR = Path("logs")
ASSETS_DIR = Path("assets")

# Files
RYZENADJ_EXECUTABLE = LIBS_DIR / "ryzenadj.exe"
HARDWARE_DLL_PATH = LIBS_DIR / "LibreHardwareMonitorLib.dll"
PROFILES_CONFIG = CONFIGS_DIR / "profiles.json"
SETTINGS_CONFIG = CONFIGS_DIR / "settings.json"

# URLs
RYZENADJ_DOWNLOAD_URL = "https://github.com/FlyGoat/RyzenAdj/releases/download/v0.13.0/ryzenadj-win64.zip"
LHM_DOWNLOAD_URL = "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v0.9.4/LibreHardwareMonitor-net472.zip"

# Hardware monitoring settings
METRICS_CACHE_TTL = 1.0  # Temps de cache des métriques en secondes

SENSOR_IDS = {
    # CPU
    'cpu_temp': ('Cpu', 'Temperature', 'Core (Tctl/Tdie)'),
    'cpu_load': ('Cpu', 'Load', 'CPU Total'),
    
    # RAM
    'ram_load': ('Memory', 'Load', 'Memory'),
    
    # iGPU (AMD 760M/780M)
    'igpu_temp': ('GpuAmd', 'Temperature', 'GPU VR SoC'),
    'igpu_load': ('GpuAmd', 'Load', 'D3D 3D'),
    
    # dGPU (RX 7700S)
    'dgpu_temp': ('GpuAmd', 'Temperature', 'GPU Core'),
    'dgpu_load': ('GpuAmd', 'Load', 'D3D 3D')
}

# RyzenAdj configuration
RYZENADJ_PARAMS = [
    ("stapm-limit", "stapm_limit"),
    ("fast-limit", "fast_limit"),
    ("slow-limit", "slow_limit"),
    ("stapm-time", "stapm_time"),
    ("slow-time", "slow_time"),
    ("tctl-temp", "tctl_temp"),
    ("vrmmax-current", "vrmmax_current"),
    ("vrmgfx-current", "vrmgfx_current")
]

# Required DLLs
REQUIRED_DLLS = [
    'libryzenadj.dll',
    'WinRing0x64.dll',
    'WinRing0x64.sys',
    'inpoutx64.dll'
]

# Cache configuration
METRICS_CACHE_TTL = 1.0  # seconds
PROFILE_CACHE_TTL = 300  # 5 minutes

# UI Colors
COLORS = {
    "primary": "#FF7043",
    "hover": "#F4511E",
    "background": "#262626",
    "text": "#FFFFFF"
}

# Supported laptop models
SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
    "13_AMD": {
        "name": "13_AMD",
        "display_name": "Framework 13 AMD",
        "processors": ["AMD Ryzen 7 7840U", "AMD Ryzen 5 7640U"],
        "tdp": {
            "min": 15,
            "max": 28
        },
        "has_dgpu": False,
        "max_refresh_rate": 60
    },
    "13_INTEL": {
        "name": "13_INTEL",
        "display_name": "Framework 13 Intel",
        "processors": ["Intel Core i7-1370P", "Intel Core i5-1340P"],
        "tdp": {
            "min": 15,
            "max": 28
        },
        "has_dgpu": False,
        "max_refresh_rate": 60
    },
    "16_AMD": {
        "name": "16_AMD",
        "display_name": "Framework 16 AMD",
        "processors": ["AMD Ryzen 7 7840HS", "AMD Ryzen 9 7940HS"],
        "tdp": {
            "min": 35,
            "max": 65
        },
        "has_dgpu": True,
        "gpu": "AMD Radeon RX 7700S",
        "max_refresh_rate": 165
    }
} 