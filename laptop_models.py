"""
Framework Laptop model configurations and specifications
"""

LAPTOP_MODELS = {
    "model_13_intel": {
        "name": "Framework Laptop 13 (Gen 13)",
        "processors": ["Intel Core i5-1340P", "Intel Core i7-1360P"],
        "display": {
            "size": 13.5,
            "resolution": "2256x1504",
            "aspect_ratio": "3:2"
        },
        "ram": {
            "max_capacity": 64,
            "type": "DDR4",
            "speed": 3200
        },
        "storage": {
            "slots": 2,
            "type": "NVMe Gen4"
        },
        "expansion_ports": 4,
        "battery": 55,
        "tdp": {
            "min": 20,
            "max": 28
        },
        "has_dgpu": False
    },
    "model_13_amd": {
        "name": "Framework Laptop 13 (AMD)",
        "processors": ["AMD Ryzen 7 7840U", "AMD Ryzen 5 7640U"],
        "display": {
            "size": 13.5,
            "resolution": "2256x1504",
            "aspect_ratio": "3:2"
        },
        "ram": {
            "max_capacity": 64,
            "type": "DDR5",
            "speed": 5600
        },
        "storage": {
            "slots": 2,
            "type": "NVMe Gen4"
        },
        "expansion_ports": 4,
        "battery": 55,
        "tdp": {
            "min": 15,
            "max": 28
        },
        "has_dgpu": False
    },
    "model_16": {
        "name": "Framework Laptop 16",
        "processors": ["AMD Ryzen 7 7840HS", "AMD Ryzen 9 7940HS"],
        "display": {
            "size": 16,
            "resolution": "2560x1600",
            "aspect_ratio": "16:10"
        },
        "ram": {
            "max_capacity": 64,
            "type": "DDR5",
            "speed": 5600
        },
        "storage": {
            "slots": 2,
            "type": "NVMe Gen4"
        },
        "expansion_ports": 6,
        "battery": 85,
        "tdp": {
            "min": 35,
            "max": 54
        },
        "has_dgpu": True,
        "gpu": "AMD Radeon RX 7700S"
    }
}

# Power profile configurations per model
POWER_PROFILES = {
    "model_13_intel": {
        "silent": {
            "tdp": 20,
            "boost_enabled": False
        },
        "balanced": {
            "tdp": 24,
            "boost_enabled": True
        },
        "performance": {
            "tdp": 28,
            "boost_enabled": True
        }
    },
    "model_13_amd": {
        "silent": {
            "tdp": 15,
            "boost_enabled": False
        },
        "balanced": {
            "tdp": 22,
            "boost_enabled": True
        },
        "performance": {
            "tdp": 28,
            "boost_enabled": True
        }
    },
    "model_16": {
        "silent": {
            "tdp": 35,
            "boost_enabled": False
        },
        "balanced": {
            "tdp": 45,
            "boost_enabled": True
        },
        "performance": {
            "tdp": 54,
            "boost_enabled": True
        }
    }
} 