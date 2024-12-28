"""Models for Framework Control Center."""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class LaptopModel(BaseModel):
    """Framework laptop model configuration."""
    name: str
    processors: List[str]
    has_dgpu: bool = False

class PowerProfile(BaseModel):
    """Power profile configuration."""
    name: str
    description: str = "Default power profile"
    power_limit: int = 25000  # Default power limit for balanced profile
    boost_enabled: bool = True
    platform_profile: str = "balanced"
    # AMD-specific fields
    tctl_temp: Optional[int] = None
    stapm_limit: Optional[int] = None
    fast_limit: Optional[int] = None
    slow_limit: Optional[int] = None
    vrm_current: Optional[int] = None
    vrmmax_current: Optional[int] = None
    vrmsoc_current: Optional[int] = None
    vrmsocmax_current: Optional[int] = None
    # Intel-specific fields
    pl1: Optional[int] = None
    pl2: Optional[int] = None
    tau: Optional[int] = None
    cpu_core_offset: Optional[int] = None
    gpu_core_offset: Optional[int] = None
    max_frequency: Optional[str] = None

class HardwareMetrics(BaseModel):
    """Hardware metrics data."""
    cpu_load: float = 0.0
    cpu_temp: float = 0.0
    ram_usage: float = 0.0
    igpu_load: float = 0.0
    igpu_temp: float = 0.0
    dgpu_load: float = 0.0
    dgpu_temp: float = 0.0
    battery_percentage: float = 0.0
    battery_time_remaining: float = 0.0
    is_charging: bool = False

class SystemConfig(BaseModel):
    """System configuration model."""
    theme: str = "dark"
    language: str = "en"
    minimize_to_tray: bool = True
    start_minimized: bool = False
    monitoring_interval: int = 1000
    current_profile: str = "Balanced"
    start_with_windows: bool = False
    refresh_rate_mode: str = "Auto"

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            # Add custom encoders if needed
        }
        populate_by_name = True
        validate_assignment = True
        extra = "ignore"  # Ignore extra fields when loading from JSON