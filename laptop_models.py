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
            "tdp": 15,
            "boost_enabled": False,
            "current_limit": 65,
            "temp_limit": 90,
            "skin_temp": 40
        },
        "balanced": {
            "tdp": 20,
            "boost_enabled": True,
            "current_limit": 80,
            "temp_limit": 95,
            "skin_temp": 45
        },
        "performance": {
            "tdp": 28,
            "boost_enabled": True,
            "current_limit": 95,
            "temp_limit": 95,
            "skin_temp": 45
        }
    },
    "model_13_amd": {
        "silent": {
            "tdp": 15,
            "fast_limit": 20,
            "slow_limit": 15,
            "boost_enabled": False,
            "current_limit": 150,
            "temp_limit": 85,
            "skin_temp": 40,
            "win_power": 0
        },
        "balanced": {
            "tdp": 30,
            "fast_limit": 35,
            "slow_limit": 30,
            "boost_enabled": True,
            "current_limit": 180,
            "temp_limit": 90,
            "skin_temp": 45,
            "win_power": 1
        },
        "performance": {
            "tdp": 60,
            "fast_limit": 70,
            "slow_limit": 60,
            "boost_enabled": True,
            "current_limit": 200,
            "temp_limit": 95,
            "skin_temp": 50,
            "win_power": 2
        }
    },
    "model_16": {
        "silent": {
            "tdp": 30,
            "boost_enabled": False,
            "current_limit": 180,
            "temp_limit": 95,
            "skin_temp": 45,
            "fast_limit": 35,
            "slow_limit": 30,
            "win_power": 0
        },
        "balanced": {
            "tdp": 95,
            "boost_enabled": True,
            "current_limit": 180,
            "temp_limit": 95,
            "skin_temp": 50,
            "fast_limit": 95,
            "slow_limit": 95,
            "win_power": 1
        },
        "performance": {
            "tdp": 120,
            "boost_enabled": True,
            "current_limit": 200,
            "temp_limit": 100,
            "skin_temp": 50,
            "fast_limit": 140,
            "slow_limit": 120,
            "win_power": 2
        }
    }
} 