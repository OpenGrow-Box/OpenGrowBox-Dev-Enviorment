"""Switch platform for OGB Dev Environment."""

import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

from .devices import TEST_DEVICES


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev switches."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        # Skip devices that have dedicated entities, but keep cooler and dehumidifier for manual control
        if device_config.get("type") in ["Exhaust", "Intake", "Sensor", "Air Sensor"]:
            continue
        # For Light type, skip if has setters (handled by light platform), else create switch
        if device_config.get("type") == "Light" and "setters" in device_config and device_config["setters"]:
            continue
        if device_config.get("type") == "Feed":
            # Create multiple switches for feed pumps
            for pump in ["a", "b", "c", "w", "x", "y", "pp", "pm"]:
                switch = OGBDevSwitch(
                    hass=hass,
                    entry=entry,
                    device_config=device_config,
                    device_key=device_key,
                    pump_key=f"feedpump_{pump}"
                )
                entities.append(switch)
        else:
            # Create power switch for each device
            switch = OGBDevSwitch(
                hass=hass,
                entry=entry,
                device_config=device_config,
                device_key=device_key
            )
            entities.append(switch)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev switches."""
    return True


class OGBDevSwitch(SwitchEntity):
    """OGB Dev switch."""

    def __init__(self, hass, entry, device_config, device_key, pump_key=None):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._device_key = device_key
        self._pump_key = pump_key
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]
        state = self._state_manager.get_device_state(device_key)
        if pump_key:
            self._attr_unique_id = f"{device_config['device_id']}_{pump_key}"
            self._attr_name = f"{device_config['name']} {pump_key.replace('feedpump_', '')}"
        else:
            self._attr_unique_id = f"dev{device_config['name'].replace('Dev', '').lower()}"
            self._attr_name = f"{device_config['name']}"
        self._attr_is_on = False

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }

    async def async_added_to_hass(self):
        """Ensure initial state is off."""
        await super().async_added_to_hass()
        self._attr_is_on = False
        self._hass.states.async_set(self.entity_id, "off")
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if switch is on."""
        state = self._state_manager.get_device_state(self._device_key)
        key = self._pump_key or "power"
        return state.get(key, False)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        key = self._pump_key or "power"
        self._state_manager.set_device_state(self._device_key, key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        key = self._pump_key or "power"
        self._state_manager.set_device_state(self._device_key, key, False)
        self.async_write_ha_state()