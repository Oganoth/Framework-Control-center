import json
import wmi
import os
import sys
from pathlib import Path
from typing import Optional

from .models import LaptopModel
from .logger import logger

def get_resource_path(relative_path):
    """Get absolute path to resource for PyInstaller bundled app."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ModelDetector:
    def __init__(self):
        self.wmi = wmi.WMI()
        self.config_path = Path(get_resource_path("configs/defaults.json"))
        self.models = self._load_models()
        logger.info("Model detector initialized with %d models", len(self.models))

    def _load_models(self) -> dict:
        """Load model configurations from defaults.json."""
        try:
            if not self.config_path.exists():
                logger.error("defaults.json not found at %s", self.config_path)
                # Try alternate path
                alt_path = Path("configs/defaults.json")
                if alt_path.exists():
                    self.config_path = alt_path
                else:
                    raise FileNotFoundError(f"defaults.json not found at {self.config_path} or {alt_path}")
            
            with open(self.config_path) as f:
                config = json.load(f)
                logger.debug("Loaded model configurations: %s", list(config["models"].keys()))
                return config["models"]
        except Exception as e:
            logger.error("Error loading defaults.json: %s", str(e))
            raise

    def detect_model(self) -> Optional[LaptopModel]:
        """Detect the Framework laptop model."""
        # Get CPU information
        cpu = self.wmi.Win32_Processor()[0]
        logger.info("Detected CPU: %s", cpu.Name)
        
        # Get GPU information
        gpus = self.wmi.Win32_VideoController()
        gpu_names = [gpu.Name for gpu in gpus]
        has_dgpu = any("Radeon" in gpu.Name for gpu in gpus)
        logger.info("Detected GPUs: %s", gpu_names)
        logger.debug("Has dedicated GPU: %s", has_dgpu)
        
        # Check each model's specifications
        for model_id, specs in self.models.items():
            logger.debug("Checking model %s", model_id)
            # Check if CPU matches
            if any(proc.lower() in cpu.Name.lower() for proc in specs["processors"]):
                logger.debug("CPU matches model %s", model_id)
                # For AMD models
                if "AMD" in cpu.Name:
                    if has_dgpu and "16_AMD" in model_id:
                        logger.info("Detected Framework 16 AMD with dGPU")
                        return LaptopModel(**specs)
                    elif not has_dgpu and "13_AMD" in model_id:
                        logger.info("Detected Framework 13 AMD")
                        return LaptopModel(**specs)
                # For Intel models
                elif "Intel" in cpu.Name and "13_INTEL" in model_id:
                    logger.info("Detected Framework 13 Intel")
                    return LaptopModel(**specs)
        
        logger.warning("Could not detect Framework laptop model")
        return None

    def get_model_by_id(self, model_id: str) -> Optional[LaptopModel]:
        """Get model by ID if automatic detection fails."""
        if model_id in self.models:
            logger.info("Using specified model: %s", model_id)
            return LaptopModel(**self.models[model_id])
        logger.error("Invalid model ID: %s", model_id)
        return None 