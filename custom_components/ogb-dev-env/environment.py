"""OGB Dev Environment Simulation."""
from random import uniform


class EnvironmentSimulator:
    """Simulates grow box environment with seasonal variations."""

    def __init__(self):
        self.season = "spring"
        self.environment = {
            "air_temperature": 23.5,
            "air_humidity": 60.0,
            "soil_temperature": 22.0,
            "co2_level": 950.0,
            "water_level": 75.0,
            "water_temperature": 18.0,
        }

    def set_season(self, season):
        """Set the current season."""
        self.season = season

    def update_environment(self, device_states):
        """Update environment based on device states and season."""
        # Seasonal multipliers for device effectiveness
        season_multipliers = {
            "spring": {"heater": 1.0, "cooler": 1.0, "light": 1.0, "humidifier": 1.0, "dehumidifier": 1.0, "co2": 1.0, "fan": 1.0},
            "summer": {"heater": 0.8, "cooler": 1.2, "light": 0.9, "humidifier": 0.8, "dehumidifier": 1.2, "co2": 1.0, "fan": 1.1},
            "fall": {"heater": 1.0, "cooler": 1.0, "light": 1.0, "humidifier": 1.0, "dehumidifier": 1.0, "co2": 1.0, "fan": 1.0},
            "winter": {"heater": 1.5, "cooler": 0.8, "light": 1.3, "humidifier": 1.2, "dehumidifier": 0.8, "co2": 1.0, "fan": 0.7},
        }
        mult = season_multipliers.get(self.season, season_multipliers["spring"])

        # Apply continuous effects based on device states, with seasonal multipliers
        delta_temp = 0.0
        delta_hum = 0.0
        delta_co2 = 0.0

        # Heater (heating + air drying)
        if device_states.get("heater", {}).get("power", False):
            delta_temp += 0.02 * mult["heater"]  # ~2.4°C/hour * multiplier
            delta_hum -= 0.01 * mult["heater"]  # Heating reduces relative humidity

        # Cooler (enhanced cooling + dehumidification)
        if device_states.get("cooler", {}).get("power", False):
            delta_temp -= 0.05 * mult["cooler"]  # Stronger cooling
            delta_hum -= 0.02 * mult["cooler"]  # Dehumidification effect

        # Humidifier (humidification + slight cooling)
        if device_states.get("humidifier", {}).get("power", False):
            delta_hum += 0.033 * mult["humidifier"]  # ~1%/hour * multiplier
            delta_temp -= 0.005 * mult["humidifier"]  # Evaporative cooling

        # Dehumidifier
        if device_states.get("dehumidifier", {}).get("power", False):
            delta_hum -= 0.033 * mult["dehumidifier"]
            delta_temp += 0.015 * mult["dehumidifier"]  # Dehumidifiers generate heat

        # CO2 (CO2 injection + fan-enhanced dispersion)
        if device_states.get("co2", {}).get("power", False):
            base_co2_increase = 1.67 * mult["co2"]  # ~50 ppm/hour * multiplier
            # Fans enhance CO2 dispersion
            fan_boost = sum(
                (device_states.get(fan_key, {}).get("speed", 0) / 10) * 0.2
                for fan_key in ["exhaust", "intake", "ventilation"]
                if device_states.get(fan_key, {}).get("power", False)
            )
            delta_co2 += base_co2_increase * (1 + fan_boost)

        # Light (enhanced heating + photosynthesis CO2 depletion)
        for light_key in ["light_main", "dumb_light"]:
            light_state = device_states.get(light_key, {})
            is_on = light_state.get("power", False)
            if light_key == "dumb_light":
                intensity = 100 if is_on else 0  # Dumb light at full intensity when on
            else:
                intensity = light_state.get("intensity", 0) if is_on else 0

            if intensity > 0:
                intensity_factor = intensity / 100
                delta_temp += intensity_factor * 0.025 * mult["light"]  # Enhanced heating like heater
                delta_hum -= intensity_factor * 0.017 * mult["humidifier"]  # Evaporation
                delta_co2 -= intensity_factor * 0.3 * mult["light"]  # Photosynthesis CO2 depletion

        # Fans (cooling + air exchange + CO2 dilution)
        fan_keys = ["exhaust", "intake", "ventilation", "dumb_exhaust", "dumb_intake"]
        for fan_key in fan_keys:
            fan_state = device_states.get(fan_key, {})
            is_on = fan_state.get("power", False)
            if fan_key in ["dumb_exhaust", "dumb_intake"]:
                speed = 10 if is_on else 0  # Dumb fans at full speed
            else:
                speed = fan_state.get("speed", 0) if is_on else 0

            if speed > 0:
                speed_factor = speed / 10
                delta_temp -= speed_factor * 0.005 * mult["fan"]  # Cooling
                delta_hum -= speed_factor * 0.01 * mult["fan"]  # Air drying
                delta_co2 -= speed_factor * 0.05 * mult["fan"]  # CO2 dilution from fresh air

        # Apply deltas
        self.environment["air_temperature"] += delta_temp
        self.environment["air_humidity"] += delta_hum
        self.environment["co2_level"] += delta_co2

        # Add small randomness for realism (no directional drift)
        self.environment["air_temperature"] += uniform(-0.02, 0.02)
        self.environment["air_humidity"] += uniform(-0.1, 0.1)
        self.environment["co2_level"] += uniform(-0.5, 0.5)

        # Clamp values
        self.environment["air_temperature"] = max(5, min(40, self.environment["air_temperature"]))
        self.environment["air_humidity"] = max(30, min(95, self.environment["air_humidity"]))
        self.environment["co2_level"] = max(300, min(2000, self.environment["co2_level"]))

        return self.environment.copy()