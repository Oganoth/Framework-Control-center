"""Model detection module for Framework laptops."""

import json
import wmi
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
import re
import traceback

from .models import LaptopModel
from .logger import logger

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource for PyInstaller bundled app."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ModelDetector:
    """Framework laptop model detector."""
    
    # CPU model patterns for each laptop series
    CPU_PATTERNS: Dict[str, List[str]] = {
        "16_AMD": [
            r"AMD Ryzen\s*7\s*7840HS",
            r"AMD Ryzen\s*7\s*PRO\s*7840HS",
            r"AMD Ryzen 7 7840HS with Radeon Graphics",
            r"AMD Ryzen 7 7840HS w/ Radeon (780M|Graphics)"
        ],
        "13_AMD": [
            r"AMD Ryzen\s*7\s*7840U",
            r"AMD Ryzen\s*7\s*7640U",
            r"AMD Ryzen\s*5\s*7640U"
        ],
        "13_INTEL": [
            r"13th Gen Intel Core i[357]-13",
            r"Intel\(R\) Core\(TM\) i[357]-13"
        ]
    }
    
    # GPU patterns for model verification
    GPU_PATTERNS: Dict[str, List[str]] = {
        "RX_7700S": [
            r"AMD Radeon\s*RX\s*7700S",
            r"AMD Radeon\(TM\) RX 7700S"
        ],
        "780M": [
            r"AMD Radeon\s*780M",
            r"AMD Radeon\(TM\)\s*780M",
            r"AMD Radeon Graphics"
        ],
        "760M": [
            r"AMD Radeon\s*760M",
            r"AMD Radeon\(TM\)\s*760M"
        ]
    }

    def __init__(self):
        """Initialize model detector."""
        try:
            self.wmi = wmi.WMI()
        except Exception as e:
            logger.error(f"Failed to initialize WMI: {e}")
            raise RuntimeError("WMI initialization failed")
            
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
            
            with open(self.config_path, encoding='utf-8') as f:
                config = json.load(f)
                if "models" not in config:
                    raise KeyError("No 'models' section in defaults.json")
                logger.debug("Loaded model configurations: %s", list(config["models"].keys()))
                return config["models"]
        except json.JSONDecodeError as e:
            logger.error("Error parsing defaults.json: %s", str(e))
            raise
        except Exception as e:
            logger.error("Error loading defaults.json: %s", str(e))
            raise

    def _match_pattern(self, text: str, patterns: List[str]) -> bool:
        """Match text against a list of regex patterns."""
        if not isinstance(patterns, (list, tuple)):
            logger.error(f"Invalid patterns type: {type(patterns)}")
            return False
        if not text:
            return False
        try:
            return any(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in patterns)
        except Exception as e:
            logger.error(f"Error matching pattern: {e}")
            return False

    def detect_model(self) -> Optional[LaptopModel]:
        """Detect the Framework laptop model."""
        try:
            # Get CPU information
            cpu = self.wmi.Win32_Processor()[0]
            cpu_name = cpu.Name.strip()
            logger.info("Detected CPU: %s", cpu_name)
            
            # Get GPU information
            gpus = self.wmi.Win32_VideoController()
            gpu_names = [gpu.Name.strip() for gpu in gpus]
            logger.info("Detected GPUs: %s", gpu_names)
            
            # Check for dedicated GPU (7700S)
            has_dgpu = False
            has_780m = False
            has_760m = False
            
            for gpu in gpus:
                gpu_name = gpu.Name.strip()
                # Check for dGPU
                for pattern in self.GPU_PATTERNS["RX_7700S"]:
                    if re.search(pattern, gpu_name, re.IGNORECASE):
                        has_dgpu = True
                        break
                # Check for 780M
                for pattern in self.GPU_PATTERNS["780M"]:
                    if re.search(pattern, gpu_name, re.IGNORECASE):
                        has_780m = True
                        break
                # Check for 760M
                for pattern in self.GPU_PATTERNS["760M"]:
                    if re.search(pattern, gpu_name, re.IGNORECASE):
                        has_760m = True
                        break
            
            has_igpu = has_780m or has_760m
            
            logger.debug("GPU detection: dGPU=%s, iGPU=%s (780M=%s, 760M=%s)", 
                        has_dgpu, has_igpu, has_780m, has_760m)
            
            # First, try to detect Framework 16 AMD
            for pattern in self.CPU_PATTERNS["16_AMD"]:
                if re.search(pattern, cpu_name, re.IGNORECASE):
                    logger.info("CPU matches Framework 16 AMD")
                    if has_dgpu:
                        logger.info("Detected Framework 16 AMD with dGPU")
                        return LaptopModel(**self.models["16_AMD"])
                    else:
                        logger.debug("Framework 16 AMD CPU detected but missing dGPU")
                    break
            
            # Then try Framework 13 AMD
            for pattern in self.CPU_PATTERNS["13_AMD"]:
                if re.search(pattern, cpu_name, re.IGNORECASE):
                    logger.info("CPU matches Framework 13 AMD")
                    if has_igpu and not has_dgpu:
                        igpu_type = "780M" if has_780m else "760M"
                        logger.info(f"Detected Framework 13 AMD with {igpu_type}")
                        return LaptopModel(**self.models["13_AMD"])
                    else:
                        logger.debug("Framework 13 AMD CPU detected but incorrect GPU configuration")
                    break
            
            # Finally try Framework 13 Intel
            for pattern in self.CPU_PATTERNS["13_INTEL"]:
                if re.search(pattern, cpu_name, re.IGNORECASE):
                    logger.info("Detected Framework 13 Intel")
                    return LaptopModel(**self.models["13_INTEL"])
            
            # Fallback detection for edge cases
            if "7840HS" in cpu_name:
                logger.info("Fallback: Framework 16 AMD detected based on 7840HS CPU")
                return LaptopModel(**self.models["16_AMD"])
            elif "7640U" in cpu_name and has_igpu and not has_dgpu:
                logger.info("Fallback: Framework 13 AMD detected based on 7640U CPU")
                return LaptopModel(**self.models["13_AMD"])
            
            logger.warning("Could not detect Framework laptop model")
            logger.debug("CPU: %s, GPUs: %s", cpu_name, gpu_names)
            return None
            
        except Exception as e:
            logger.error("Error detecting model: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            return None

    def get_model_by_id(self, model_id: str) -> Optional[LaptopModel]:
        """Get model by ID with validation."""
        if not isinstance(model_id, str):
            logger.error("Invalid model_id type: %s", type(model_id))
            return None
            
        if model_id in self.models:
            logger.info("Using specified model: %s", model_id)
            return LaptopModel(**self.models[model_id])
            
        logger.error("Invalid model ID: %s", model_id)
        return None 