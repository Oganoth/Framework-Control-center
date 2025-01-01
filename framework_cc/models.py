"""Models for Framework Control Center."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import json
from dataclasses import dataclass

@dataclass
class AttributeScheme:
    """Classe générique pour gérer les attributs du thème."""
    def __init__(self, data_dict: Dict[str, Any]):
        for key, value in data_dict.items():
            if isinstance(value, dict):
                setattr(self, key, AttributeScheme(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

@dataclass
class ThemeConfig:
    """Configuration du thème."""
    name: str
    colors: AttributeScheme
    fonts: AttributeScheme
    spacing: AttributeScheme
    radius: AttributeScheme

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeConfig':
        return cls(
            name=data['name'],
            colors=AttributeScheme(data['colors']),
            fonts=AttributeScheme(data.get('fonts', {'main': {'family': 'Roboto', 'size': {'normal': 11}}})),
            spacing=AttributeScheme(data.get('spacing', {'normal': 10})),
            radius=AttributeScheme(data.get('radius', {'normal': 10}))
        )

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

class FontSize(BaseModel):
    """Font size configuration."""
    small: int = 10
    normal: int = 11
    large: int = 12
    title: int = 14

class FontConfig(BaseModel):
    """Font configuration."""
    family: str
    size: FontSize

class FontsConfig(BaseModel):
    """Fonts configuration."""
    main: FontConfig
    monospace: FontConfig

class BackgroundColors(BaseModel):
    """Background colors configuration."""
    main: str
    secondary: str
    tertiary: str
    header: str
    input: str

class TextColors(BaseModel):
    """Text colors configuration."""
    primary: str
    secondary: str
    disabled: str
    accent: str

class BorderColors(BaseModel):
    """Border colors configuration."""
    active: str
    inactive: str
    input: str

class ButtonColors(BaseModel):
    """Button colors configuration."""
    primary: str
    secondary: str
    disabled: str
    danger: str
    success: str
    warning: str

class ProgressColors(BaseModel):
    """Progress colors configuration."""
    background: str
    bar: str
    cpu: str
    gpu: str
    ram: str
    temp: str

class StatusColors(BaseModel):
    """Status colors configuration."""
    error: str
    warning: str
    success: str
    info: str

class ScrollbarColors(BaseModel):
    """Scrollbar colors configuration."""
    background: str
    thumb: str
    hover: str

class ThemeColors(BaseModel):
    """Theme colors configuration."""
    primary: str
    hover: str
    background: BackgroundColors
    text: TextColors
    border: BorderColors
    button: ButtonColors
    progress: ProgressColors
    status: StatusColors
    separator: str
    scrollbar: ScrollbarColors

class Theme(BaseModel):
    """Theme configuration."""
    name: str
    colors: ThemeColors
    fonts: FontsConfig
    spacing: dict[str, int]
    radius: dict[str, int]

class SystemConfig(BaseModel):
    """Configuration système."""
    language: str = "en"
    current_theme: str = "default_theme"
    minimize_to_tray: bool = True
    start_minimized: bool = False
    start_with_windows: bool = False
    monitoring_interval: int = 1000
    current_profile: str = "Balanced"
    refresh_rate_mode: str = "Auto"
    window_position: dict = {"x": 0, "y": 0}  # Position de la fenêtre

    def load_theme(self) -> ThemeConfig:
        """Charger le thème actuel."""
        try:
            theme_path = Path("configs") / f"{self.current_theme}.json"
            if not theme_path.exists():
                theme_path = Path("configs") / "default_theme.json"
            
            with open(theme_path, encoding="utf-8") as f:
                theme_data = json.load(f)
            
            return ThemeConfig.from_dict(theme_data)
        except Exception as e:
            import logging
            logging.error(f"Error loading theme: {e}")
            # Retourner un thème par défaut en cas d'erreur
            return ThemeConfig.from_dict({
                "name": "Default Dark",
                "colors": {
                    "primary": "#FF7043",
                    "hover": "#F4511E",
                    "background": {
                        "main": "#1E1E1E",
                        "secondary": "#2D2D2D",
                        "tertiary": "#383838",
                        "header": "#1E1E1E",
                        "input": "#2D2D2D"
                    },
                    "text": {
                        "primary": "#FFFFFF",
                        "secondary": "#E0E0E0",
                        "disabled": "#A0A0A0",
                        "accent": "#FF7043"
                    },
                    "button": {
                        "primary": "#FF7043",
                        "secondary": "#2D2D2D",
                        "disabled": "#404040",
                        "danger": "#FF4444",
                        "success": "#4CAF50",
                        "warning": "#FFC107"
                    },
                    "border": {
                        "active": "#FFFFFF",
                        "inactive": "#404040",
                        "input": "#FF7043"
                    },
                    "progress": {
                        "background": "#2D2D2D",
                        "bar": "#FF7043",
                        "cpu": "#FF7043",
                        "gpu": "#00BCD4",
                        "ram": "#4CAF50",
                        "temp": "#FFC107"
                    },
                    "status": {
                        "error": "#FF4444",
                        "warning": "#FFC107",
                        "success": "#4CAF50",
                        "info": "#2196F3"
                    }
                },
                "fonts": {
                    "main": {
                        "family": "Roboto",
                        "size": {
                            "small": 10,
                            "normal": 11,
                            "large": 12,
                            "title": 14
                        }
                    },
                    "monospace": {
                        "family": "Consolas",
                        "size": {
                            "small": 10,
                            "normal": 11,
                            "large": 12,
                            "title": 14
                        }
                    }
                },
                "spacing": {
                    "small": 5,
                    "normal": 10,
                    "large": 20
                },
                "radius": {
                    "small": 5,
                    "normal": 10,
                    "large": 15
                }
            })

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            # Add custom encoders if needed
        }
        populate_by_name = True
        validate_assignment = True
        extra = "ignore"  # Ignore extra fields when loading from JSON