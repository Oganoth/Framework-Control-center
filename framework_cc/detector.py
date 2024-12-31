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
        cpu_name = cpu.Name.strip()
        logger.info("Detected CPU: %s", cpu_name)
        
        # Get GPU information
        gpus = self.wmi.Win32_VideoController()
        gpu_names = [gpu.Name.strip() for gpu in gpus]
        # Vérification plus précise des GPUs
        has_dgpu = any("RX" in gpu.Name and "7700S" in gpu.Name for gpu in gpus)
        has_760m = any("760M" in gpu.Name and "Radeon" in gpu.Name for gpu in gpus)
        has_780m = any("780M" in gpu.Name and "Radeon" in gpu.Name for gpu in gpus)
        has_igpu = has_760m or has_780m
        logger.info("Detected GPUs: %s", gpu_names)
        logger.debug("Has dedicated GPU: %s, Has integrated GPU: %s (760M: %s, 780M: %s)", 
                    has_dgpu, has_igpu, has_760m, has_780m)
        
        # Check each model's specifications
        for model_id, specs in self.models.items():
            logger.debug("Checking model %s", model_id)
            # Vérification plus précise du CPU
            if any(proc in cpu_name for proc in specs["processors"]):
                logger.debug("CPU matches model %s", model_id)
                # Pour les modèles AMD
                if "AMD" in cpu_name:
                    if has_dgpu and "16_AMD" in model_id:
                        logger.info("Detected Framework 16 AMD with dGPU")
                        return LaptopModel(**specs)
                    elif has_igpu and not has_dgpu and "13_AMD" in model_id:
                        igpu_type = "780M" if has_780m else "760M"
                        logger.info(f"Detected Framework 13 AMD with {igpu_type}")
                        return LaptopModel(**specs)
                # Pour les modèles Intel
                elif "Intel" in cpu_name and "13_INTEL" in model_id:
                    logger.info("Detected Framework 13 Intel")
                    return LaptopModel(**specs)
        
        # Si aucun modèle n'est détecté mais que nous avons un CPU AMD connu
        if "7640U" in cpu_name and has_igpu and not has_dgpu:
            logger.info("Forcing Framework 13 AMD detection based on 7640U CPU")
            return LaptopModel(**self.models["13_AMD"])
        elif "7840HS" in cpu_name and has_dgpu:
            logger.info("Forcing Framework 16 AMD detection based on 7840HS CPU")
            return LaptopModel(**self.models["16_AMD"])
            
        logger.warning("Could not detect Framework laptop model")
        logger.debug("CPU: %s, GPUs: %s", cpu_name, gpu_names)
        return None

    def get_model_by_id(self, model_id: str) -> Optional[LaptopModel]:
        """Get model by ID if automatic detection fails."""
        if model_id in self.models:
            logger.info("Using specified model: %s", model_id)
            return LaptopModel(**self.models[model_id])
        logger.error("Invalid model ID: %s", model_id)
        return None 