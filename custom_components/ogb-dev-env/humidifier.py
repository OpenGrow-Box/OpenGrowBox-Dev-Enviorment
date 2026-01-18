"""OGB Dev humidifier."""
import asyncio
from homeassistant.components.humidifier import HumidifierEntity, HumidifierDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .devices import TEST_DEVICES
from . import OGBDevRestoreEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev humidifier."""
    entities = []

    humidifier = OGBDevHumidifier(
        hass=hass,
        entry=entry
    )
    entities.append(humidifier)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev humidifier."""
    return True


class OGBDevHumidifier(OGBDevRestoreEntity, HumidifierEntity):
    """OGB Dev humidifier control with state restoration."""

    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]["state_manager"]

        self._attr_unique_id = "ogb_dev_humidifier"
        self._attr_name = "OGB Dev Humidity Control"
        self._attr_device_class = HumidifierDeviceClass.HUMIDIFIER

        self._attr_min_humidity = 20
        self._attr_max_humidity = 90
        self._attr_target_humidity = 60

        self._attr_device_info = {
            "identifiers": {(DOMAIN, "humidity_control")},
            "name": "Humidity Control",
            "manufacturer": "OpenGrowBox",
            "model": "Dev Environment",
        }

    async def async_added_to_hass(self):
        """Restore state on startup."""
        await super().async_added_to_hass()

        restored_target = await self._async_restore_state("target_humidity", 60.0)
        self._attr_target_humidity = float(restored_target) if restored_target else 60.0

        humidifier_on = await self._async_restore_device_state("humidifier", "power")
        dehumidifier_on = await self._async_restore_device_state("dehumidifier", "power")

        if humidifier_on:
            self._attr_mode = "humidify"
        elif dehumidifier_on:
            self._attr_mode = "dehumidify"
        else:
            self._attr_mode = None

        self._hass.states.async_set(self.entity_id, "on" if (humidifier_on or dehumidifier_on) else "off")
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if humidifier is on."""
        humidifier_state = self._state_manager.get_device_state("humidifier").get("power", False)
        dehumidifier_state = self._state_manager.get_device_state("dehumidifier").get("power", False)
        return humidifier_state or dehumidifier_state

    @property
    def current_humidity(self):
        """Return the current humidity."""
        hum = self._state_manager.environment["air_humidity"]
        hum += 0.5
        return round(hum, 2)

    @property
    def target_humidity(self):
        """Return the target humidity."""
        return self._attr_target_humidity

    async def async_set_humidity(self, humidity):
        """Set new target humidity."""
        self._attr_target_humidity = humidity
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the humidifier on."""
        target = self._attr_target_humidity
        current = self.current_humidity
        if target > current:
            await self._state_manager.set_device_state("humidifier", "power", True)
            await self._state_manager.set_device_state("dehumidifier", "power", False)
            self._attr_mode = "humidify"
        else:
            await self._state_manager.set_device_state("humidifier", "power", False)
            await self._state_manager.set_device_state("dehumidifier", "power", True)
            self._attr_mode = "dehumidify"
        self._hass.states.async_set(self.entity_id, "on")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the humidifier off."""
        await self._state_manager.set_device_state("humidifier", "power", False)
        await self._state_manager.set_device_state("dehumidifier", "power", False)
        self._attr_mode = None
        self._hass.states.async_set(self.entity_id, "off")
        self.async_write_ha_state()
