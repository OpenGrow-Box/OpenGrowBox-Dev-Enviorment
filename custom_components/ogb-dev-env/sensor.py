"""Sensor platform for OGB Dev Environment."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from random import uniform
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__ + ".debug")

# Import test devices
from .devices import TEST_DEVICES


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev sensors."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        if "sensors" in device_config:
            for sensor_config in device_config["sensors"]:
                sensor = OGBDevSensor(
                    hass=hass,
                    entry=entry,
                    device_config=device_config,
                    sensor_config=sensor_config,
                    device_key=device_key
                )
                entities.append(sensor)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev sensors."""
    return True


class OGBDevSensor(SensorEntity):
    """OGB Dev sensor."""

    def __init__(self, hass, entry, device_config, sensor_config, device_key):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._sensor_config = sensor_config
        self._device_key = device_key
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]

        # Entity properties
        self._attr_unique_id = f"{device_config['device_id']}_{sensor_config['name'].lower().replace(' ', '_')}"
        self._attr_name = f"{device_config['name']} {sensor_config['name']}"

        # Sensor properties
        if sensor_config.get("unit"):
            self._attr_unit_of_measurement = sensor_config["unit"]

        # Special unique_ids
        self._attr_unique_id = f"{device_config['device_id']}_{sensor_config['name'].lower().replace(' ', '_')}"

        if device_config['device_id'] == "sensor_main":
            if sensor_config['name'] == "illuminance":
                self._attr_unique_id = "soilsensor_illuminance"
            elif sensor_config['name'] == "moisture":
                self._attr_unique_id = "soilsensor_moisture"
            elif sensor_config['name'] == "conductivity":
                self._attr_unique_id = "soilsensor_conductivity"
            elif sensor_config['name'] == "temperature":
                self._attr_unique_id = "soilsensor_temperature"
            elif sensor_config['name'] == "soil_temperature":
                self._attr_unique_id = "soilsensor_soil_temperature"
        elif sensor_config['name'] == "co2":
            if device_config['device_id'] == "devco2device":
                self._attr_unique_id = "devco2device_co2"
            else:
                self._attr_unique_id = "devco2"

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }
        
        if device_config['device_id'] == "devco2device":
            _LOGGER.debug(f"CO2 sensor device_info: {self._attr_device_info}")

    @property
    def should_poll(self):
        """Enable polling for sensor updates."""
        return True

    @property
    def scan_interval(self):
        """Scan interval for instant sensor updates."""
        from datetime import timedelta
        return timedelta(milliseconds=100)

    @property
    def native_value(self):
        """Return the current state."""
        sensor_name = self._sensor_config["name"]
        device_key = self._device_key
        state_manager = self._state_manager

        if sensor_name == "temperature":
            temp = state_manager.environment["air_temperature"]
            if device_key == "air_sensor_2":
                temp += 0.05
            elif device_key == "air_sensor_3":
                temp += 0.1
            return round(temp, 2)
        elif sensor_name == "humidity":
            hum = state_manager.environment["air_humidity"]
            if device_key == "air_sensor_2":
                hum += 0.5
            elif device_key == "air_sensor_3":
                hum += 1.0
            return round(hum, 2)
        elif sensor_name == "temperature":
            if device_key == "sensor_main":
                return round(state_manager.environment["soil_temperature"], 2)
            else:
                return round(state_manager.environment.get("water_temperature", 0), 2)
        elif sensor_name == "carbondioxide":
            return round(state_manager.environment["co2_level"], 2)
        elif sensor_name == "level":
            return round(state_manager.environment["water_level"], 2)
        elif sensor_name == "intensity":
            device_state = state_manager.get_device_state(device_key)
            return device_state.get("intensity", 0)
        elif sensor_name == "par":
            intensity = state_manager.get_device_state(device_key).get("intensity", 0)
            return round(intensity * 5.3, 2)
        elif sensor_name == "duty":
            device_state = state_manager.get_device_state(device_key)
            percentage = device_state.get("percentage")
            if percentage is not None:
                return percentage
            speed = device_state.get("speed", 0)
            return int((speed / 10) * 100)
        elif sensor_name == "moisture":
            return round(55.0 + uniform(-5, 5), 2)
        elif sensor_name == "conductivity":
            return round(1200.0 + uniform(-50, 50), 2)
        elif sensor_name == "soil_temperature":
            return round(state_manager.environment["soil_temperature"], 2)
        elif sensor_name == "illuminance":
            light_state = state_manager.get_device_state("light_main")
            intensity = light_state.get("intensity", 0) if light_state.get("power", False) else 0
            return intensity * 10
        elif sensor_name in ["Far Red PPFD", "Red PPFD", "Blue PPFD", "UV Intensity"]:
            return 100 if state_manager.get_device_state(device_key).get("power", False) else 0

        else:
            return self._sensor_config.get("value", 0.0)