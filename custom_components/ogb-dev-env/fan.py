"""OGB Dev fans."""
import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .devices import TEST_DEVICES


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev fans."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        if device_config.get("type") in ["Exhaust", "Intake"] or device_key == "ventilation_fan":
            fan = OGBDevFan(
                hass=hass,
                entry=entry,
                device_config=device_config,
                device_key=device_key
            )
            entities.append(fan)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev fans."""
    return True


class OGBDevFan(FanEntity):
    """OGB Dev fan."""

    def __init__(self, hass, entry, device_config, device_key):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._device_key = device_key
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]
        self._state = self._state_manager.get_device_state(device_key)

        # Entity properties
        self._attr_unique_id = f"dev{device_config['name'].replace('Dev', '').lower()}"
        self._attr_name = device_config["name"]
        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_supported_features = FanEntityFeature.SET_SPEED | 32



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

        # Delayed OFF to override HA restoration
        async def delayed_off():
            await asyncio.sleep(10)
            self._hass.states.async_set(self.entity_id, "off")
            self.async_write_ha_state()

        self._hass.async_create_task(delayed_off())

    @property
    def is_on(self):
        """Return true if fan is on."""
        return self._state.get("power", False)

    @property
    def percentage(self):
        """Return the current speed percentage."""
        speed = self._state.get("speed", 0)
        return int((speed / 10) * 100)

    async def async_set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = int((percentage / 100) * 10)
            self._state_manager.set_device_state(self._device_key, "speed", speed)
            self._state_manager.set_device_state(self._device_key, "power", True)
            self.async_write_ha_state()

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        """Turn the fan on."""
        self._state_manager.set_device_state(self._device_key, "power", True)
        if percentage is not None:
            self._attr_percentage = percentage
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        self._state_manager.set_device_state(self._device_key, "power", False)
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        self._attr_percentage = percentage
        if percentage > 0:
            self._state_manager.set_device_state(self._device_key, "power", True)
        else:
            self._state_manager.set_device_state(self._device_key, "power", False)
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the fan."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

