"""Framework Control Center package."""

from .gui import FrameworkControlCenter
from .models import SystemConfig, PowerProfile, LaptopModel, HardwareMetrics
from .power_plan import PowerManager
from .hardware import HardwareMonitor
from .display import DisplayManager
from .detector import ModelDetector
from .logger import logger, check_and_rotate_log
from .translations import get_text, language_names
from .admin import is_admin, run_as_admin

__version__ = "1.0.0" 