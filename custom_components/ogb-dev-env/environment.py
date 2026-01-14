"""OGB Dev Environment Simulation."""
from random import uniform


class EnvironmentSimulator:
    """Simulates grow box environment with seasonal variations."""

    def __init__(self):
        # Ambient temperature and humidity base values by season
        self.ambient_bases = {
            "spring": {"temp": 20.0, "hum": 65.0},
            "spring_dry": {"temp": 23.0, "hum": 35.0},
            "spring_wet": {"temp": 17.0, "hum": 90.0},
            "summer": {"temp": 25.0, "hum": 60.0},
            "summer_dry": {"temp": 28.0, "hum": 30.0},
            "summer_wet": {"temp": 22.0, "hum": 85.0},
            "fall": {"temp": 18.0, "hum": 70.0},
            "fall_dry": {"temp": 21.0, "hum": 40.0},
            "fall_wet": {"temp": 15.0, "hum": 95.0},
            "winter": {"temp": 10.0, "hum": 75.0},
            "winter_dry": {"temp": 11.0, "hum": 40.0},
            "winter_wet": {"temp": 7.0, "hum": 100.0},
        }
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
            base_season = self.season.split('_')[0]  # e.g., winter_dry -> winter
            base = self.outside_bases.get(base_season, self.outside_bases["summer"])
            self.outside_temp = base["temp"] + uniform(-5.0, 5.0)
            self.outside_hum = max(0, min(100, base["hum"] + uniform(-10.0, 10.0)))
            self.outside_co2 = base["co2"]

        # Asymptotic approach for temperature (passive, only ambient + outside)
        target_temp = self.ambient_temperature
        if weather_data and weather_data.get("temp") is not None:
            # Outside influence if intake-like, but passive
            target_temp += (weather_data["temp"] - self.ambient_temperature) * 0.05  # Small outside blend
        approach_rate = 0.05
        delta_temp = (target_temp - self.environment["air_temperature"]) * approach_rate

        # Asymptotic approach for humidity (passive, only season base + outside)
        season_data = self.ambient_bases.get(self.season, {"temp": 25.0, "hum": 60.0})
        target_hum = season_data["hum"]
        if weather_data and weather_data.get("hum") is not None:
            target_hum += (weather_data["hum"] - season_data["hum"]) * 0.05  # Small outside blend
        delta_hum = (target_hum - self.environment["air_humidity"]) * approach_rate

        # CO2 (passive, only outside)
        target_co2 = self.outside_co2
        delta_co2 = (target_co2 - self.environment["co2_level"]) * approach_rate

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