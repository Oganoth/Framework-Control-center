"""Framework Control Center package."""

from .models import SystemConfig, PowerProfile, LaptopModel
from .power_plan import PowerPlanManager
from .power import PowerManager
from .utils import get_resource_path

__all__ = [
    'SystemConfig',
    'PowerProfile',
    'LaptopModel',
    'PowerPlanManager',
    'PowerManager',
    'get_resource_path'
] 