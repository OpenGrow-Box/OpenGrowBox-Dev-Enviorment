"""Number platform for OGB Dev Environment."""

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN 
from .devices import TEST_DEVICES


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev numbers."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        # Skip devices that have dedicated entities
        if device_config.get("type") in ["Light", "Exhaust", "Intake"]:
            continue
        if "setters" in device_config:
            for setter_key, setter_config in device_config["setters"].items():
                if setter_key != "power":  # Power is handled by switch
                    number = OGBDevNumber(
                        hass=hass,
                        entry=entry,
                        device_config=device_config,
                        setter_config=setter_config,
                        setter_key=setter_key,
                        device_key=device_key
                    )
                    entities.append(number)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev numbers."""
    return True


class OGBDevNumber(NumberEntity):
    """OGB Dev number."""

    def __init__(self, hass, entry, device_config, setter_config, setter_key, device_key):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._setter_config = setter_config
        self._setter_key = setter_key
        self._device_key = device_key
        
        data_entry = self._hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        if isinstance(data_entry, dict):
            self._state_manager = data_entry.get("state_manager")
        else:
            self._state_manager = data_entry

        # Entity properties
        self._attr_unique_id = f"{device_config['device_id']}_{setter_key}"
        self._attr_name = f"{device_config['name']} {setter_key.replace('_', ' ').title()}"

        # Number properties
        self._attr_native_min_value = setter_config["min"]
        self._attr_native_max_value = setter_config["max"]
        self._attr_native_step = 1.0 if setter_config["unit"] == "" else 0.1
        if setter_config.get("unit"):
            self._attr_unit_of_measurement = setter_config["unit"]

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }

    @property
    def native_value(self):
        """Return the current value."""
        return self._state_manager.get_device_state(self._device_key).get(self._setter_key, self._setter_config["default"])

    async def async_set_native_value(self, value):
        """Set the value."""
        self._state_manager.set_device_state(self._device_key, self._setter_key, value)
        self.async_write_ha_state()