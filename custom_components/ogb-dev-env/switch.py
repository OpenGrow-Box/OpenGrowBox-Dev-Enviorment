"""Switch platform for OGB Dev Environment."""
import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

from .devices import TEST_DEVICES
from . import OGBDevRestoreEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev switches."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        if device_config.get("type") in ["Exhaust", "Intake", "Air Sensor"]:
            continue
        if device_config.get("type") == "Sensor" and device_config.get("device_id") != "devco2device":
            continue
        if device_config.get("type") == "Light" and "setters" in device_config and device_config["setters"]:
            continue
        if device_config.get("type") == "Feed":
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


class OGBDevSwitch(OGBDevRestoreEntity, SwitchEntity):
    """OGB Dev switch with state restoration."""

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
            if device_config['device_id'] == "devco2device":
                self._attr_unique_id = "devco2device"
            elif device_config['name'] == "Irrigation Dripper":
                self._attr_unique_id = "dripperirrigation"
            elif "Dumb" in device_config['name']:
                self._attr_unique_id = f"dev{device_config['name'].replace('DevDumb', 'dumb').replace('Fan', '').lower()}"
            else:
                self._attr_unique_id = f"dev{device_config['name'].replace('Dev', '').lower()}"
            self._attr_name = f"{device_config['name']}"
        self._attr_is_on = False

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }

    async def async_added_to_hass(self):
        """Restore state on startup."""
        await super().async_added_to_hass()

        state_key = self._pump_key or "power"
        restored = await self._async_restore_device_state(self._device_key, state_key)

        is_on = bool(restored) if restored is not None else False

        await self._state_manager.set_device_state(self._device_key, state_key, is_on)
        self._attr_is_on = is_on
        self._hass.states.async_set(self.entity_id, "on" if is_on else "off")
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
        await self._state_manager.set_device_state(self._device_key, key, True)
        self._attr_is_on = True
        self._hass.states.async_set(self.entity_id, "on")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        key = self._pump_key or "power"
        await self._state_manager.set_device_state(self._device_key, key, False)
        self._attr_is_on = False
        self._hass.states.async_set(self.entity_id, "off")
        self.async_write_ha_state()
