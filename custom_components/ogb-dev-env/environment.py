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
            "soil_temperature": 20.0,
            "co2_level": 600.0,
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
        """
        Main update function - calculates new environment values based on:
        - Seasonal ambient conditions (target values)
        - Device states (active devices modify targets)
        - Outside weather (if available from Home Assistant)
        - Passive approach (gradual movement toward targets)
        """
        mult = self._get_season_multipliers()

        # Get seasonal base values with small random variation
        self.ambient_temperature = self._update_ambient_temp()
        # Get outside weather (from HA or seasonal defaults)
        self.outside_temp, self.outside_hum, self.outside_co2 = self._update_outside_weather(weather_data)

        # Current environment state
        current_temp = self.environment["air_temperature"]
        current_hum = self.environment["air_humidity"]

        # Calculate how active devices affect environment
        device_effects = self._calculate_device_effects(device_states, mult)

        # Start with seasonal ambient as base target
        target_temp = self.ambient_temperature + device_effects["temp_offset"]
        target_hum = self.ambient_bases[self.season]["hum"]

        # Light: Major heat source in grow boxes
        # Heat from lamps raises temperature (reduces relative humidity naturally)
        # All lights contribute heat when on - spectrum lights count as 100% when on
        light_state = device_states.get("light_main", {})
        dumb_light_state = device_states.get("dumb_light", {})
        light_ir_state = device_states.get("light_ir", {})
        light_red_state = device_states.get("light_red", {})
        light_blue_state = device_states.get("light_blue", {})
        light_uv_state = device_states.get("light_uv", {})

        any_light_on = (
            light_state.get("power", False) or
            dumb_light_state.get("power", False) or
            light_ir_state.get("power", False) or
            light_red_state.get("power", False) or
            light_blue_state.get("power", False) or
            light_uv_state.get("power", False)
        )

        light_heat = 0.0
        if any_light_on:
            # Main light intensity
            main_intensity = light_state.get("intensity", 100) if light_state.get("power", False) else 0

            # Additional lights add to total heat (each counts as 100% when on)
            additional_lights = 0.0
            if dumb_light_state.get("power", False):
                additional_lights += 100.0
            if light_ir_state.get("power", False):
                additional_lights += 100.0
            if light_red_state.get("power", False):
                additional_lights += 100.0
            if light_blue_state.get("power", False):
                additional_lights += 100.0
            if light_uv_state.get("power", False):
                additional_lights += 100.0

            # Calculate total effective intensity
            total_intensity = main_intensity + additional_lights
            intensity_factor = min(2.0, total_intensity / 100.0)

            # Light heat - applies to both current and target temperature
            light_heat = 0.8 * intensity_factor * mult["light"]
            target_temp += light_heat

        # Exhaust Fan: Pulls ambient air OUT of the grow box
        # This reduces the influence of the target, moving toward current box conditions
        # Dumb exhaust: if power is True, treat as 100%
        exhaust_state = device_states.get("exhaust", {})
        dumb_exhaust_state = device_states.get("dumb_exhaust", {})
        exhaust_power = exhaust_state.get("power", False) or dumb_exhaust_state.get("power", False)
        if exhaust_power:
            exhaust_pct = exhaust_state.get("percentage") if exhaust_state.get("percentage") else 100
            exhaust_factor = (exhaust_pct / 100) * 0.3
            target_temp = target_temp * (1 - exhaust_factor) + current_temp * exhaust_factor
            target_hum = target_hum * (1 - exhaust_factor) + current_hum * exhaust_factor

        # Intake Fan: Pulls OUTSIDE air INTO the grow box
        # This brings in external temperature and humidity
        # Dumb intake: if power is True, treat as 100%
        intake_state = device_states.get("intake", {})
        dumb_intake_state = device_states.get("dumb_intake", {})
        intake_power = intake_state.get("power", False) or dumb_intake_state.get("power", False)
        if intake_power:
            intake_pct = intake_state.get("percentage") if intake_state.get("percentage") else 100
            intake_factor = (intake_pct / 100) * 0.4
            target_temp = target_temp * (1 - intake_factor) + self.outside_temp * intake_factor
            target_hum = target_hum * (1 - intake_factor) + self.outside_hum * intake_factor

        # Internal Ventilation Fan: Circulates air WITHIN the grow box
        # At 50%+ speed, it averages target with current (mixing effect)
        vent_state = device_states.get("ventilation_fan", {})
        if vent_state.get("power", False):
            vent_pct = vent_state.get("percentage", 100)
            if vent_pct >= 50:
                target_temp = (target_temp + current_temp) / 2
                target_hum = (target_hum + current_hum) / 2

        # Approach rate: how fast environment moves toward target
        # Active devices make the environment more responsive
        approach_rate = 0.03 + device_effects["approach_rate_bonus"]

        # Apply gradual approach toward targets
        self.environment["air_temperature"] += (target_temp - current_temp) * approach_rate
        self.environment["air_humidity"] += (target_hum - current_hum) * approach_rate

        # Update CO2 level (photosynthesis vs supplementation)
        self.environment["co2_level"] = self._update_co2_level(device_states, mult)

        # Add small random noise and clamp to valid ranges
        self.environment["air_temperature"] = max(5, min(45, self.environment["air_temperature"] + uniform(-0.02, 0.02)))
        self.environment["air_humidity"] = max(20, min(98, self.environment["air_humidity"] + uniform(-0.1, 0.1)))

        return self.environment.copy()

    def _get_season_multipliers(self):
        """
        Returns seasonal efficiency multipliers for climate devices.
        These adjust how effective each device type is in different seasons.
        Base multipliers + dry/wet variants adjust humidifier/dehumidifier effectiveness.
        """
        base_season = self.season.split('_')[0]
        variant = self.season.split('_')[1] if '_' in self.season else None

        base_mults = {
            "spring": {"heater": 1.0, "cooler": 1.0, "humidifier": 1.0, "dehumidifier": 1.0, "fan": 1.0, "light": 1.0, "co2": 1.0},
            "summer": {"heater": 0.8, "cooler": 1.2, "humidifier": 0.8, "dehumidifier": 1.2, "fan": 1.1, "light": 0.9, "co2": 1.1},
            "fall": {"heater": 1.0, "cooler": 1.0, "humidifier": 1.0, "dehumidifier": 1.0, "fan": 1.0, "light": 1.0, "co2": 1.0},
            "winter": {"heater": 1.5, "cooler": 0.8, "humidifier": 1.2, "dehumidifier": 0.8, "fan": 0.7, "light": 1.3, "co2": 0.9},
        }

        mults = base_mults[base_season].copy()

        if variant == "dry":
            # Dry air: humidifier less needed, dehumidifier more effective
            mults["humidifier"] *= 0.7
            mults["dehumidifier"] *= 1.3
        elif variant == "wet":
            # Wet air: humidifier more effective, dehumidifier less needed
            mults["humidifier"] *= 1.3
            mults["dehumidifier"] *= 0.7

        return mults

    def _update_ambient_temp(self):
        """
        Calculates the seasonal ambient temperature inside the grow box.
        Returns base seasonal temp plus small random variation.
        """
        base = self.ambient_bases.get(self.season, self.ambient_bases["summer"])
        return base["temp"] + uniform(-1.0, 1.0)

    def _update_outside_weather(self, weather_data):
        """
        Gets the current outside weather conditions.
        Uses Home Assistant weather entity if available, otherwise falls back to
        seasonal defaults with random variation.
        """
        # If HA weather entity is available, use its data
        if weather_data and weather_data.get("temp") is not None:
            temp = weather_data["temp"] + uniform(-2.0, 2.0)
            hum = max(0, min(100, weather_data.get("hum", 50) + uniform(-5.0, 5.0)))
            return temp, hum, 400.0

        # Otherwise use seasonal base values (e.g., "summer_dry" -> "summer")
        base_season = self.season.split('_')[0]
        base = self.outside_bases.get(base_season, self.outside_bases["summer"])
        return (
            base["temp"] + uniform(-5.0, 5.0),
            max(0, min(100, base["hum"] + uniform(-10.0, 10.0))),
            base["co2"]
        )

    def _calculate_device_effects(self, device_states, mult):
        """
        Calculates how active devices affect the environment:
        - Heater/Cooler: Direct temperature changes
        - Light: Heat from lamps + CO2 consumption by plants
        - Humidifier/Dehumidifier: Faster humidity equilibration
        """
        effects = {"temp_offset": 0, "approach_rate_bonus": 0, "co2_consumption": 0}

        # Heater: Adds heat to the environment
        heater_state = device_states.get("heater", {})
        if heater_state.get("power", False):
            heater_power = heater_state.get("power", 1.0) if isinstance(heater_state.get("power"), (int, float)) else 1.0
            effects["temp_offset"] += 1.0 * heater_power * mult["heater"]
            effects["approach_rate_bonus"] += 0.02

        # Cooler: Removes heat from the environment
        cooler_state = device_states.get("cooler", {})
        if cooler_state.get("power", False):
            cooler_power = cooler_state.get("power", 1.0) if isinstance(cooler_state.get("power"), (int, float)) else 1.0
            effects["temp_offset"] -= 0.20 * cooler_power * mult["cooler"]
            effects["approach_rate_bonus"] += 0.02

        # Note: Light heat is now calculated directly in update_environment()
        # (not here) to avoid double-counting with temp_offset

        # Light CO2 consumption (plants photosynthesize when light is on)
        light_state = device_states.get("light_main", {})
        dumb_light_state = device_states.get("dumb_light", {})
        light_ir_state = device_states.get("light_ir", {})
        light_red_state = device_states.get("light_red", {})
        light_blue_state = device_states.get("light_blue", {})
        light_uv_state = device_states.get("light_uv", {})

        any_light_on = (
            light_state.get("power", False) or
            dumb_light_state.get("power", False) or
            light_ir_state.get("power", False) or
            light_red_state.get("power", False) or
            light_blue_state.get("power", False) or
            light_uv_state.get("power", False)
        )

        if any_light_on:
            main_intensity = light_state.get("intensity", 100) if light_state.get("power", False) else 0
            additional_lights = 0.0
            if dumb_light_state.get("power", False):
                additional_lights += 100.0
            if light_ir_state.get("power", False):
                additional_lights += 100.0
            if light_red_state.get("power", False):
                additional_lights += 100.0
            if light_blue_state.get("power", False):
                additional_lights += 100.0
            if light_uv_state.get("power", False):
                additional_lights += 100.0

            total_intensity = main_intensity + additional_lights
            intensity_factor = min(2.0, total_intensity / 100.0)

            # Plants consume CO2 during photosynthesis
            effects["co2_consumption"] += 30 * intensity_factor * mult["co2"]
            effects["approach_rate_bonus"] += 0.025

        # CO2 Device: Adds CO2 to the environment when active
        co2_device_state = device_states.get("co2", {})
        if co2_device_state.get("co2", False):
            effects["co2_consumption"] -= 30  # CO2 supplement adds ~30 ppm per update

        # Humidifier: Adds moisture (faster humidity equilibration)
        humidifier_state = device_states.get("humidifier", {})
        if humidifier_state.get("power", False):
            effects["approach_rate_bonus"] += 0.015

        # Dehumidifier: Removes moisture (faster humidity equilibration)
        dehumidifier_state = device_states.get("dehumidifier", {})
        if dehumidifier_state.get("power", False):
            effects["approach_rate_bonus"] += 0.015

        return effects

    def _update_co2_level(self, device_states, mult):
        """
        Updates CO2 level based on:
        - Plant photosynthesis (consumes CO2 when light is on)
        - CO2 supplementation device (adds CO2)
        - Intake fan: brings in outside air (~400 ppm)
        - Exhaust fan: pulls out box air (removes accumulated CO2)
        - Natural equilibration with outside air (400 ppm baseline)
        """
        current_co2 = self.environment["co2_level"]
        effects = self._calculate_device_effects(device_states, mult)

        # Start with natural approach to outside CO2 (400 ppm)
        outside_co2 = 400.0

        # Intake Fan: Brings in outside air with ~400 ppm CO2
        # This dilutes box CO2 toward ambient levels
        # Dumb intake: if power is True, treat as 100%
        intake_state = device_states.get("intake", {})
        dumb_intake_state = device_states.get("dumb_intake", {})
        intake_power = intake_state.get("power", False) or dumb_intake_state.get("power", False)
        if intake_power:
            intake_pct = intake_state.get("percentage") if intake_state.get("percentage") else 100
            intake_factor = (intake_pct / 100) * 0.4
            target_co2 = current_co2 * (1 - intake_factor) + outside_co2 * intake_factor
            current_co2 = current_co2 + (target_co2 - current_co2) * 0.1

        # Exhaust Fan: Pulls box air OUT
        # This removes CO2 from the box (important during photosynthesis)
        # Dumb exhaust: if power is True, treat as 100%
        exhaust_state = device_states.get("exhaust", {})
        dumb_exhaust_state = device_states.get("dumb_exhaust", {})
        exhaust_power = exhaust_state.get("power", False) or dumb_exhaust_state.get("power", False)
        if exhaust_power:
            exhaust_pct = exhaust_state.get("percentage") if exhaust_state.get("percentage") else 100
            exhaust_factor = (exhaust_pct / 100) * 0.3
            current_co2 -= (current_co2 - outside_co2) * exhaust_factor * 0.1

        # Internal ventilation: circulates air, helps equalize CO2 pockets
        vent_state = device_states.get("ventilation_fan", {})
        if vent_state.get("power", False):
            vent_pct = vent_state.get("percentage", 100)
            if vent_pct >= 50:
                # Mild averaging effect
                current_co2 = current_co2 * 0.95 + outside_co2 * 0.05

        # Apply plant consumption / CO2 device
        net_change = - (effects["co2_consumption"] * 0.1)

        new_co2 = current_co2 + net_change
        new_co2 = max(300, min(2000, new_co2 + uniform(-1, 1)))

        return new_co2