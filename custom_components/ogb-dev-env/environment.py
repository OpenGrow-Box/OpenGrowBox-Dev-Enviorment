"""OGB Dev Environment Simulation."""
from random import uniform


class EnvironmentSimulator:
    """Simulates grow box environment with realistic physics."""

    SEASONS = {
        "spring": {"room_temp": 20.0, "room_hum": 65.0, "outside_temp": 15.0, "outside_hum": 65.0},
        "spring_dry": {"room_temp": 23.0, "room_hum": 35.0, "outside_temp": 15.0, "outside_hum": 40.0},
        "spring_wet": {"room_temp": 17.0, "room_hum": 90.0, "outside_temp": 12.0, "outside_hum": 90.0},
        "summer": {"room_temp": 25.0, "room_hum": 60.0, "outside_temp": 25.0, "outside_hum": 50.0},
        "summer_dry": {"room_temp": 28.0, "room_hum": 30.0, "outside_temp": 28.0, "outside_hum": 30.0},
        "summer_wet": {"room_temp": 22.0, "room_hum": 85.0, "outside_temp": 22.0, "outside_hum": 85.0},
        "fall": {"room_temp": 18.0, "room_hum": 70.0, "outside_temp": 10.0, "outside_hum": 70.0},
        "fall_dry": {"room_temp": 21.0, "room_hum": 40.0, "outside_temp": 12.0, "outside_hum": 40.0},
        "fall_wet": {"room_temp": 15.0, "room_hum": 95.0, "outside_temp": 8.0, "outside_hum": 95.0},
        "winter": {"room_temp": 18.0, "room_hum": 75.0, "outside_temp": 5.0, "outside_hum": 80.0},
        "winter_dry": {"room_temp": 20.0, "room_hum": 40.0, "outside_temp": 7.0, "outside_hum": 40.0},
        "winter_wet": {"room_temp": 15.0, "room_hum": 100.0, "outside_temp": 3.0, "outside_hum": 100.0},
    }

    def __init__(self):
        self.season = "summer"
        self._apply_season()

        self.environment = {
            "air_temperature": self.room_temp,
            "air_humidity": self.room_hum,
            "soil_temperature": self.room_temp,
            "co2_level": 600.0,
            "water_level": 75.0,
            "water_temperature": 18.0,
        }

    def _apply_season(self):
        """Apply season settings."""
        data = self.SEASONS.get(self.season, self.SEASONS["summer"])
        self.room_temp = data["room_temp"]
        self.room_hum = data["room_hum"]
        self.outside_temp = data["outside_temp"]
        self.outside_hum = data["outside_hum"]

    def set_season(self, season):
        """Set the current season."""
        self.season = season
        self._apply_season()

    def update_environment(self, device_states, weather_data=None):
        """
        Main update function - calculates new environment values based on:
        - Room temperature (where the tent is located)
        - Outside temperature (what intake fan brings in)
        - Device heat input (light, heater) accumulates over time
        - Heat loss through insulation and fan air exchange
        """
        if weather_data and weather_data.get("temp") is not None:
            self.outside_temp = weather_data["temp"] + uniform(-2.0, 2.0)
            self.outside_hum = max(20, min(100, weather_data.get("hum", 50) + uniform(-5.0, 5.0)))

        current_temp = self.environment["air_temperature"]
        current_hum = self.environment["air_humidity"]

        light_heat = self._calculate_light_heat(device_states)
        heater_heat = self._calculate_heater_heat(device_states)
        cooler_heat = self._calculate_cooler_heat(device_states)

        total_heat_input = light_heat + heater_heat + cooler_heat

        insulation_loss = self._calculate_insulation_loss(current_temp)
        exhaust_loss = self._calculate_exhaust_loss(device_states, current_temp)
        intake_loss = self._calculate_intake_loss(device_states, current_temp)

        new_temp = current_temp + total_heat_input - insulation_loss - exhaust_loss - intake_loss
        new_hum = current_hum + self._calculate_humidity_effects(device_states, total_heat_input, exhaust_loss, intake_loss)

        self._apply_ventilation_mixing(device_states, current_temp, new_hum)

        new_temp = max(5, min(50, new_temp + uniform(-0.1, 0.1)))
        new_hum = max(20, min(98, new_hum + uniform(-0.2, 0.2)))

        self.environment["air_temperature"] = new_temp
        self.environment["air_humidity"] = new_hum
        self.environment["co2_level"] = self._update_co2_level(device_states)

        return self.environment.copy()

    def _calculate_humidity_effects(self, device_states, heat_input, exhaust_loss, intake_loss):
        """Calculate humidity changes from devices."""
        hum_change = 0.0

        hum_change -= heat_input * 0.2
        hum_change -= exhaust_loss * 0.15
        hum_change += intake_loss * 0.1

        humidifier_state = device_states.get("humidifier", {})
        if humidifier_state.get("power", False):
            hum_change += 1.5

        dehumidifier_state = device_states.get("dehumidifier", {})
        if dehumidifier_state.get("power", False):
            hum_change -= 1.2

        return hum_change

    def _calculate_light_heat(self, device_states):
        """Calculate heat input from lights."""
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

        if not any_light_on:
            return 0.0

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

        return 0.3 * intensity_factor

    def _calculate_heater_heat(self, device_states):
        """Calculate heat input from heater."""
        heater_state = device_states.get("heater", {})
        if not heater_state.get("power", False):
            return 0.0

        heater_power = heater_state.get("power", 1.0)
        if isinstance(heater_power, bool):
            heater_power = 1.0 if heater_power else 0.0

        return 0.3 * heater_power

    def _calculate_cooler_heat(self, device_states):
        """Calculate cooling from cooler."""
        cooler_state = device_states.get("cooler", {})
        if not cooler_state.get("power", False):
            return 0.0

        cooler_power = cooler_state.get("power", 1.0)
        if isinstance(cooler_power, bool):
            cooler_power = 1.0 if cooler_power else 0.0

        return -0.25 * cooler_power

    def _calculate_insulation_loss(self, current_temp):
        """Calculate heat loss through tent insulation (to room)."""
        diff = current_temp - self.room_temp
        if diff <= 0:
            return 0.0
        return diff * 0.05

    def _calculate_exhaust_loss(self, device_states, current_temp):
        """Calculate heat loss from exhaust fan (pulls air out to room)."""
        exhaust_state = device_states.get("exhaust", {})
        dumb_exhaust_state = device_states.get("dumb_exhaust", {})
        exhaust_power = exhaust_state.get("power", False) or dumb_exhaust_state.get("power", False)

        if not exhaust_power:
            return 0.0

        exhaust_pct = exhaust_state.get("percentage") if exhaust_state.get("percentage") else 100
        exhaust_factor = (exhaust_pct / 100) * 0.12
        diff = current_temp - self.room_temp
        return diff * exhaust_factor

    def _calculate_intake_loss(self, device_states, current_temp):
        """Calculate heat loss from intake fan (brings in outside air)."""
        intake_state = device_states.get("intake", {})
        dumb_intake_state = device_states.get("dumb_intake", {})
        intake_power = intake_state.get("power", False) or dumb_intake_state.get("power", False)

        if not intake_power:
            return 0.0

        intake_pct = intake_state.get("percentage") if intake_state.get("percentage") else 100
        intake_factor = (intake_pct / 100) * 0.15
        diff = current_temp - self.outside_temp
        return diff * intake_factor

    def _apply_ventilation_mixing(self, device_states, current_temp, current_hum):
        """Ventilation fan mixes air within tent - no heat loss, just even distribution."""
        vent_state = device_states.get("ventilation_fan", {})
        if not vent_state.get("power", False):
            return

        vent_pct = vent_state.get("percentage", 100)
        if vent_pct >= 50:
            self.environment["air_temperature"] = (self.environment["air_temperature"] + current_temp) / 2
            self.environment["air_humidity"] = (self.environment["air_humidity"] + current_hum) / 2

    def _update_co2_level(self, device_states):
        """Update CO2 level based on plants and devices."""
        current_co2 = self.environment["co2_level"]
        outside_co2 = 400.0

        light_state = device_states.get("light_main", {})
        any_light_on = light_state.get("power", False)

        if any_light_on:
            main_intensity = light_state.get("intensity", 100)
            intensity_factor = main_intensity / 100.0
            current_co2 -= 5 * intensity_factor

        co2_device_state = device_states.get("co2", {})
        if co2_device_state.get("co2", False):
            current_co2 += 15

        intake_state = device_states.get("intake", {})
        dumb_intake_state = device_states.get("dumb_intake", {})
        intake_power = intake_state.get("power", False) or dumb_intake_state.get("power", False)
        if intake_power:
            intake_pct = intake_state.get("percentage") if intake_state.get("percentage") else 100
            intake_factor = (intake_pct / 100) * 0.15
            current_co2 = current_co2 * (1 - intake_factor) + outside_co2 * intake_factor

        current_co2 = current_co2 * 0.99 + outside_co2 * 0.01

        return max(300, min(2000, current_co2 + uniform(-1, 1)))
