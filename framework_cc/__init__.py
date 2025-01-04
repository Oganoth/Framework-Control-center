"""Framework Control Center package."""

from .logger import logger, check_and_rotate_log
from .models import SystemConfig, PowerProfile, LaptopModel
from .power_plan import PowerPlanManager
from .hardware import HardwareMonitor
from .display import DisplayManager
from .detector import ModelDetector
from .admin import is_admin, run_as_admin
from .translations import get_text, language_names

__version__ = "1.0.0" 