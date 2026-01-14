# Test devices data for OGB Dev Environment

# Global environment state for simulation
ENVIRONMENT = {
    "air_temperature": 23.5,
    "air_humidity": 60.0,
    "soil_temperature": 22.0,
    "co2_level": 950.0,
    "water_level": 75.0,
    "water_temperature": 18.0,
}

TEST_DEVICES = {
    "light_main": {
        "name": "DevMainLight",
        "type": "Light",
        "labels": ["Light"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {
            "intensity": {"min": 0, "max": 100, "unit": "%", "default": 0}
        },
        "state": {
            "power": False,
            "intensity": 20
        },
        "sensors": [
            {"name": "intensity", "unit": "%", "icon": "mdi:brightness-6"},
            {"name": "par", "unit": "µmol/m²/s", "icon": "mdi:white-balance-sunny"},
            {"name": "duty", "unit": "%", "icon": "mdi:lightbulb"}
        ]
    },
    "dumb_light": {
        "name": "DevDumbLight",
        "type": "Light",
        "labels": ["Light"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []
    },
    "light_ir": {
        "name": "DevFarRedLight",
        "type": "Light",
        "labels": ["FarRedLight"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
    },
    "light_red": {
        "name": "DevRedLight",
        "type": "Light",
        "labels": ["redLight"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
    },
    "light_blue": {
        "name": "DevBlueLight",
        "type": "Light",
        "labels": ["redLight"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
    },
    "light_uv": {
        "name": "DevUVLight",
        "type": "Light",
        "labels": ["UVLight"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
    },
    "sensor_main": {
        "name": "DevSoilSensor",
        "type": "Sensor",
        "labels": ["Sensor"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "moisture", "unit": "%", "value": 55.0},
            {"name": "conductivity", "unit": "µS/cm", "value": 1200.0},
            {"name": "ph", "unit": "", "value": 6.2},
            {"name": "temperature", "unit": "°C", "value": 22.0}
        ]
    },
    "heater": {
        "name": "DevHeater",
        "type": "Heater",
        "labels": ["Heater"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []  # No sensors for heater
    },
    "cooler": {
        "name": "DevCooler",
        "type": "Cooler",
        "labels": ["Cooler"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []  # No sensors for cooler
    },
    "humidifier": {
        "name": "DevHumidifier",
        "type": "Humidifier",
        "labels": ["Humidifier"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []  # No sensors for humidifier
    },
    "dehumidifier": {
        "name": "DevDehumidifier",
        "type": "Dehumidifier",
        "labels": ["Dehumidifier"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []  # No sensors for dehumidifier
    },
    "exhaust": {
        "name": "DevExhaustFan",
        "type": "Exhaust",
        "labels": ["Exhaust"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "duty", "unit": "%", "icon": "mdi:fan"}
        ]
    },
    "intake": {
        "name": "DevIntakeFan",
        "type": "Intake",
        "labels": ["Intake"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "duty", "unit": "%", "icon": "mdi:fan"}
        ]
    },
    "ventilation_switch": {
        "name": "DevVentilationSwitch",
        "type": "Ventilation",
        "labels": ["Ventilation"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []
    },
    "ventilation_fan": {
        "name": "DevVentilationFan",
        "type": "Ventilation",
        "labels": ["Ventilation"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "duty", "unit": "%", "icon": "mdi:fan"}
        ]
    },
    "co2": {
        "name": "DevCO2System",
        "type": "CO2",
        "labels": ["CO2"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "co2", "unit": "ppm", "value": 950.0}
        ]
    },
    "dumb_exhaust": {
        "name": "DevDumbExhaustFan",
        "type": "Dumb Exhaust",
        "labels": ["Fan"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []
    },
    "dumb_intake": {
        "name": "DevDumbIntakeFan",
        "type": "Dumb Intake",
        "labels": ["Fan"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []
    },
    "air_sensor": {
        "name": "DevSensor1",
        "type": "Air Sensor",
        "labels": ["Sensor"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "temperature", "unit": "°C", "value": 23.5},
            {"name": "humidity", "unit": "%", "value": 60.0}
        ]
    },
    "air_sensor_2": {
        "name": "DevSensor2",
        "type": "Air Sensor",
        "labels": ["Sensor"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "temperature", "unit": "°C", "value": 23.5},
            {"name": "humidity", "unit": "%", "value": 60.0}
        ]
    },
    "air_sensor_3": {
        "name": "DevSensor3",
        "type": "Air Sensor",
        "labels": ["Sensor"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "temperature", "unit": "°C", "value": 23.5},
            {"name": "humidity", "unit": "%", "value": 60.0}
        ]
    },
    "water_pump": {
        "name": "DevWaterPump",
        "type": "Water Pump",
        "labels": ["Pump"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": [
            {"name": "level", "unit": "%", "value": 75.0},
            {"name": "temperature", "unit": "°C", "value": 18.0}
        ]
    },
    "ph_doser": {
        "name": "DevPhDoser",
        "type": "pH Doser",
        "labels": ["Pump"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []
    },
    "ec_doser": {
        "name": "DevECDoser",
        "type": "EC Doser",
        "labels": ["Pump"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "power": False
        },
        "sensors": []
    },
    "feed": {
        "name": "DevFeedSystem",
        "type": "Feed",
        "labels": ["Feed"],
        "manufacturer": "OpenGrowBox",
        "model": "Dev OGB Environment",
        "setters": {},
        "state": {
            "feedpump_a": False,
            "feedpump_b": False,
            "feedpump_c": False,
            "feedpump_w": False,
            "feedpump_x": False,
            "feedpump_y": False,
            "feedpump_pp": False,
            "feedpump_pm": False
        },
        "sensors": []
    }
}