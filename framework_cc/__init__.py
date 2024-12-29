"""Framework Control Center package."""

from .logger import logger
from .models import SystemConfig, PowerProfile, LaptopModel
from .power_plan import PowerManager, WindowsPowerPlanManager
from .hardware import HardwareMonitor
from .display import DisplayManager
from .detector import ModelDetector
from .admin import is_admin, run_as_admin
from .tweaks import WindowsTweaks

__version__ = "1.0.0" 