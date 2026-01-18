"""OGB Dev Environment Simulation."""
from random import uniform


class EnvironmentSimulator:
    """Simulates grow box environment with realistic physics."""

    def __init__(self):
        # Room temperature and humidity (baseline where tent is located)
        # This is NOT outside temperature - it's indoor room conditions
        self.room_temp = 20.0
        self.room_hum = 50.0

        # Environment state
        self.environment = {
            "air_temperature": 20.0,
            "air_humidity": 50.0,
            "soil_temperature": 20.0,
            "co2_level": 600.0,
            "water_level": 75.0,
            "water_temperature": 18.0,
        }

    def set_room_conditions(self, temp, hum):
        """Set room baseline conditions."""
        self.room_temp = temp
        self.room_hum = hum

    def update_environment(self, device_states, weather_data=None):
        """
        Main update function - calculates new environment values based on:
        - Room temperature as baseline (where the tent is located)
        - Device heat input (light, heater) accumulates over time
        - Heat loss through insulation and fan air exchange
        """
        if weather_data and weather_data.get("temp") is not None:
            self.room_temp = weather_data["temp"] + uniform(-2.0, 2.0)
            self.room_hum = max(20, min(80, weather_data.get("hum", 50) + uniform(-5.0, 5.0)))

        current_temp = self.environment["air_temperature"]
        current_hum = self.environment["air_humidity"]

        # === HEAT INPUT ===
        light_heat = self._calculate_light_heat(device_states)
        heater_heat = self._calculate_heater_heat(device_states)
        cooler_heat = self._calculate_cooler_heat(device_states)

        total_heat_input = light_heat + heater_heat + cooler_heat

        # === HEAT LOSS ===
        insulation_loss = self._calculate_insulation_loss(current_temp, self.room_temp)
        fan_loss = self._calculate_fan_loss(device_states, current_temp, self.room_temp)

        # === TEMPERATURE UPDATE ===
        # new_temp = current + heat_input - heat_loss
        new_temp = current_temp + total_heat_input - insulation_loss - fan_loss

        # === HUMIDITY UPDATE ===
        # Heat reduces relative humidity (warm air holds more moisture)
        # Also affected by intake fan bringing in room air
        new_hum = current_hum - (total_heat_input * 0.8)
        new_hum = new_hum - (fan_loss * 0.5)

        # Clamp temperature to reasonable range
        new_temp = max(10, min(45, new_temp + uniform(-0.1, 0.1)))
        new_hum = max(20, min(98, new_hum + uniform(-0.2, 0.2)))

        # Update environment
        self.environment["air_temperature"] = new_temp
        self.environment["air_humidity"] = new_hum

        # Update CO2
        self.environment["co2_level"] = self._update_co2_level(device_states)

        return self.environment.copy()

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

        # Main light intensity
        main_intensity = light_state.get("intensity", 100) if light_state.get("power", False) else 0

        # Additional lights (each counts as 100% when on)
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

        # Light heat: 300W at 100% = 0.5°C per 30s update
        # Full spectrum + all extra lights at 200% = 1.0°C per update
        return 0.5 * intensity_factor

    def _calculate_heater_heat(self, device_states):
        """Calculate heat input from heater."""
        heater_state = device_states.get("heater", {})
        if not heater_state.get("power", False):
            return 0.0

        heater_power = heater_state.get("power", 1.0)
        if isinstance(heater_power, bool):
            heater_power = 1.0 if heater_power else 0.0

        # Heater: 100W at 100% = 0.3°C per 30s update
        return 0.3 * heater_power

    def _calculate_cooler_heat(self, device_states):
        """Calculate cooling from cooler."""
        cooler_state = device_states.get("cooler", {})
        if not cooler_state.get("power", False):
            return 0.0

        cooler_power = cooler_state.get("power", 1.0)
        if isinstance(cooler_power, bool):
            cooler_power = 1.0 if cooler_power else 0.0

        # Cooler removes heat: 0.25°C per update
        return -0.25 * cooler_power

    def _calculate_insulation_loss(self, current_temp, room_temp):
        """Calculate heat loss through tent insulation."""
        diff = current_temp - room_temp
        if diff <= 0:
            return 0.0
        # Heat loss proportional to temperature difference
        # 10% of difference per 30s update
        return diff * 0.1

    def _calculate_fan_loss(self, device_states, current_temp, room_temp):
        """Calculate heat loss from exhaust/intake fans."""
        exhaust_state = device_states.get("exhaust", {})
        dumb_exhaust_state = device_states.get("dumb_exhaust", {})
        exhaust_power = exhaust_state.get("power", False) or dumb_exhaust_state.get("power", False)

        intake_state = device_states.get("intake", {})
        dumb_intake_state = device_states.get("dumb_intake", {})
        intake_power = intake_state.get("power", False) or dumb_intake_state.get("power", False)

        total_fan_loss = 0.0

        # Exhaust pulls warm air out, bringing in room air
        if exhaust_power:
            exhaust_pct = exhaust_state.get("percentage") if exhaust_state.get("percentage") else 100
            exhaust_factor = (exhaust_pct / 100) * 0.2
            diff = current_temp - room_temp
            total_fan_loss += diff * exhaust_factor

        # Intake brings in room air (similar effect as exhaust)
        if intake_power:
            intake_pct = intake_state.get("percentage") if intake_state.get("percentage") else 100
            intake_factor = (intake_pct / 100) * 0.25
            diff = current_temp - room_temp
            total_fan_loss += diff * intake_factor

        return total_fan_loss

    def _update_co2_level(self, device_states):
        """Update CO2 level based on plants and devices."""
        current_co2 = self.environment["co2_level"]
        outside_co2 = 400.0

        light_state = device_states.get("light_main", {})
        any_light_on = light_state.get("power", False)

        # Plants consume CO2 during photosynthesis
        if any_light_on:
            main_intensity = light_state.get("intensity", 100)
            intensity_factor = main_intensity / 100.0
            current_co2 -= 5 * intensity_factor

        # CO2 device adds CO2
        co2_device_state = device_states.get("co2", {})
        if co2_device_state.get("co2", False):
            current_co2 += 15

        # Intake brings in outside air (400 ppm)
        intake_state = device_states.get("intake", {})
        dumb_intake_state = device_states.get("dumb_intake", {})
        intake_power = intake_state.get("power", False) or dumb_intake_state.get("power", False)
        if intake_power:
            intake_pct = intake_state.get("percentage") if intake_state.get("percentage") else 100
            intake_factor = (intake_pct / 100) * 0.15
            current_co2 = current_co2 * (1 - intake_factor) + outside_co2 * intake_factor

        # Natural equilibration toward outside CO2
        current_co2 = current_co2 * 0.99 + outside_co2 * 0.01

        return max(300, min(2000, current_co2 + uniform(-1, 1)))
