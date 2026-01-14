"""OGB Dev Environment Simulation."""
from random import uniform


class EnvironmentSimulator:
    """Simulates grow box environment with seasonal variations."""

    def __init__(self):
        self.season = "summer"
        season_data = self.ambient_bases[self.season]
        self.environment = {
            "air_temperature": season_data["temp"],
            "air_humidity": season_data["hum"],
            "soil_temperature": 22.0,
            "co2_level": 950.0,
            "water_level": 75.0,
            "water_temperature": 18.0,
        }
        # Ambient temperature and humidity base values by season
        self.ambient_bases = {
            "spring": {"temp": 20.0, "hum": 65.0},
            "spring_dry": {"temp": 23.0, "hum": 45.0},
            "spring_wet": {"temp": 17.0, "hum": 85.0},
            "summer": {"temp": 25.0, "hum": 60.0},
            "summer_dry": {"temp": 28.0, "hum": 40.0},
            "summer_wet": {"temp": 22.0, "hum": 80.0},
            "fall": {"temp": 18.0, "hum": 70.0},
            "fall_dry": {"temp": 21.0, "hum": 50.0},
            "fall_wet": {"temp": 15.0, "hum": 90.0},
            "winter": {"temp": 10.0, "hum": 75.0},
            "winter_dry": {"temp": 13.0, "hum": 55.0},
            "winter_wet": {"temp": 7.0, "hum": 95.0},
        }
        self.ambient_temperature = self.ambient_bases[self.season]

        # Outside weather base values by season
        self.outside_bases = {
            "spring": {"temp": 15.0, "hum": 65.0, "co2": 400.0},
            "summer": {"temp": 25.0, "hum": 50.0, "co2": 400.0},
            "fall": {"temp": 10.0, "hum": 70.0, "co2": 400.0},
            "winter": {"temp": 5.0, "hum": 80.0, "co2": 400.0},
        }
        self.outside_temp = self.outside_bases[self.season]["temp"]
        self.outside_hum = self.outside_bases[self.season]["hum"]
        self.outside_co2 = self.outside_bases[self.season]["co2"]

    def set_season(self, season):
        """Set the current season."""
        self.season = season

    def update_environment(self, device_states, weather_data=None):
        """Update environment based on device states and season."""
        # Seasonal multipliers for device effectiveness
        season_multipliers = {
            "spring": {"heater": 1.0, "cooler": 1.0, "light": 1.0, "humidifier": 1.0, "dehumidifier": 1.0, "co2": 1.0, "fan": 1.0},
            "summer": {"heater": 0.8, "cooler": 1.2, "light": 0.9, "humidifier": 0.8, "dehumidifier": 1.2, "co2": 1.0, "fan": 1.1},
            "fall": {"heater": 1.0, "cooler": 1.0, "light": 1.0, "humidifier": 1.0, "dehumidifier": 1.0, "co2": 1.0, "fan": 1.0},
            "winter": {"heater": 1.5, "cooler": 0.8, "light": 1.3, "humidifier": 1.2, "dehumidifier": 0.8, "co2": 1.0, "fan": 0.7},
        }
        mult = season_multipliers.get(self.season, season_multipliers["spring"])

        # Update ambient temperature with seasonal base and random variation
        season_data = self.ambient_bases.get(self.season, {"temp": 25.0, "hum": 60.0})
        self.ambient_temperature = season_data["temp"] + uniform(-1.0, 1.0)

        # Update outside weather
        if weather_data and weather_data.get("temp") is not None:
            self.outside_temp = weather_data["temp"] + uniform(-2.0, 2.0)
            self.outside_hum = max(0, min(100, weather_data.get("hum", 50) + uniform(-5.0, 5.0)))
            self.outside_co2 = 400.0
        else:
            base = self.outside_bases[self.season]
            self.outside_temp = base["temp"] + uniform(-5.0, 5.0)
            self.outside_hum = max(0, min(100, base["hum"] + uniform(-10.0, 10.0)))
            self.outside_co2 = base["co2"]

        # Calculate device contributions to target temperature
        temp_contribution = 0.0

        # Heater
        if device_states.get("heater", {}).get("power", False):
            temp_contribution += 3.0 * mult["heater"]  # +3°C offset

        # Cooler
        if device_states.get("cooler", {}).get("power", False):
            temp_contribution -= 3.0 * mult["cooler"]  # -3°C offset

        # Light
        for light_key in ["light_main", "dumb_light"]:
            light_state = device_states.get(light_key, {})
            is_on = light_state.get("power", False)
            if light_key == "dumb_light":
                intensity = 100 if is_on else 0
            else:
                intensity = light_state.get("intensity", 0) if is_on else 0
            if intensity > 0:
                intensity_factor = intensity / 100
                temp_contribution += intensity_factor * 3.0 * mult["light"]  # Up to +3°C

        # Fans (cooling from air circulation)
        fan_keys = ["exhaust", "intake", "ventilation_fan"]
        fan_speed_sum = sum(
            device_states.get(fan_key, {}).get("speed", 0) if device_states.get(fan_key, {}).get("power", False) else 0
            for fan_key in fan_keys
        )
        if fan_speed_sum > 0:
            temp_contribution -= (fan_speed_sum / 50) * 0.3 * mult["fan"]  # Max -0.3°C

        # Asymptotic approach for thermal lag
        target_temp = self.ambient_temperature + temp_contribution
        approach_rate = 0.05  # 5% toward target per update
        delta_temp = (target_temp - self.environment["air_temperature"]) * approach_rate

        # Other environment deltas (humidity, CO2)
        delta_hum = 0.0
        delta_co2 = 0.0

        # Heater (air drying)
        if device_states.get("heater", {}).get("power", False):
            delta_hum -= 0.01 * mult["heater"]

        # Cooler (dehumidification)
        if device_states.get("cooler", {}).get("power", False):
            delta_hum -= 0.02 * mult["cooler"]

        # Humidifier
        if device_states.get("humidifier", {}).get("power", False):
            delta_hum += 0.033 * mult["humidifier"]
            delta_temp += 0.01 * mult["humidifier"]  # Slight heating

        # Dehumidifier
        if device_states.get("dehumidifier", {}).get("power", False):
            delta_hum -= 0.033 * mult["dehumidifier"]
            delta_temp += 0.1 * mult["dehumidifier"]  # Heat generation from hot air output

        # CO2
        if device_states.get("co2", {}).get("power", False):
            base_co2_increase = 1.67 * mult["co2"]
            fan_boost = sum(
                0.2 if device_states.get(fan_key, {}).get("power", False) else 0
                for fan_key in ["exhaust", "intake", "ventilation_fan"]
            )
            delta_co2 += base_co2_increase * (1 + fan_boost)

        # Light (photosynthesis CO2 depletion)
        for light_key in ["light_main", "dumb_light"]:
            light_state = device_states.get(light_key, {})
            is_on = light_state.get("power", False)
            if light_key == "dumb_light":
                intensity = 100 if is_on else 0
            else:
                intensity = light_state.get("intensity", 0) if is_on else 0
            if intensity > 0:
                intensity_factor = intensity / 100
                delta_co2 -= intensity_factor * 0.3 * mult["light"]

        # Fans (air drying, CO2 dilution)
        for fan_key in fan_keys:
            fan_state = device_states.get(fan_key, {})
            is_on = fan_state.get("power", False)
            if fan_key in ["dumb_exhaust", "dumb_intake"]:
                speed = 10 if is_on else 0
            else:
                speed = fan_state.get("speed", 0) if is_on else 0
            if speed > 0:
                speed_factor = speed / 10
                delta_hum -= speed_factor * 0.015 * mult["fan"]
                delta_co2 -= speed_factor * 0.05 * mult["fan"]

        # Intake fan air exchange with outside
        intake_state = device_states.get("intake", {})
        if intake_state.get("power", False):
            intake_speed = intake_state.get("speed", 10)
            exchange_rate = 0.05 * (intake_speed / 10)
            delta_temp += (self.outside_temp - self.environment["air_temperature"]) * exchange_rate
            delta_hum += (self.outside_hum - self.environment["air_humidity"]) * exchange_rate
            delta_co2 += (self.outside_co2 - self.environment["co2_level"]) * exchange_rate

        # RH decreases as temperature increases (VPD effect)
        delta_hum -= delta_temp * 0.3

        # Apply deltas
        self.environment["air_temperature"] += delta_temp
        self.environment["air_humidity"] += delta_hum
        self.environment["co2_level"] += delta_co2

        # Add small randomness
        self.environment["air_temperature"] += uniform(-0.02, 0.02)
        self.environment["air_humidity"] += uniform(-0.1, 0.1)
        self.environment["co2_level"] += uniform(-0.5, 0.5)

        # Clamp values
        self.environment["air_temperature"] = max(5, min(40, self.environment["air_temperature"]))
        self.environment["air_humidity"] = max(30, min(95, self.environment["air_humidity"]))
        self.environment["co2_level"] = max(300, min(2000, self.environment["co2_level"]))

        return self.environment.copy()