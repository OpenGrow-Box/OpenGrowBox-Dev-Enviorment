"""OGB Dev fans."""
import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .devices import TEST_DEVICES
from . import OGBDevRestoreEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev fans."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        if device_config.get("type") in ["Exhaust", "Intake", "Ventilation"]:
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


class OGBDevFan(OGBDevRestoreEntity, FanEntity):
    """OGB Dev fan with state restoration."""

    def __init__(self, hass, entry, device_config, device_key):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._device_key = device_key
        
        data_entry = self._hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        if isinstance(data_entry, dict):
            self._state_manager = data_entry.get("state_manager")
        else:
            self._state_manager = data_entry
            
        self._state = self._state_manager.get_device_state(device_key) if self._state_manager else {}

        self._attr_unique_id = f"{self._entry.entry_id}_{device_config['device_id']}_fan"
        self._attr_name = device_config["name"]
        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_supported_features = FanEntityFeature.SET_SPEED

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }

    async def async_added_to_hass(self):
        """Restore state on startup."""
        await super().async_added_to_hass()

        restored_percentage = await self._async_restore_device_state(
            self._device_key, "percentage"
        )
        restored_power = await self._async_restore_device_state(
            self._device_key, "power"
        )

        percentage = int(restored_percentage) if restored_percentage is not None else 0
        is_on = bool(restored_power) if restored_power is not None else False

        if percentage > 0:
            is_on = True

        await self._state_manager.set_device_state(self._device_key, "percentage", percentage)
        await self._state_manager.set_device_state(self._device_key, "power", is_on)

        self._attr_percentage = percentage if is_on else 0
        self._attr_is_on = is_on
        self._hass.states.async_set(
            self.entity_id,
            "on" if is_on else "off",
            {"percentage": self._attr_percentage}
        )
        self.async_write_ha_state()

    @property
    def percentage(self):
        """Return the current percentage."""
        state = self._state_manager.get_device_state(self._device_key)
        return state.get("percentage", 0) if state.get("power", False) else 0

    @property
    def is_on(self):
        """Return true if fan is on."""
        return self._state_manager.get_device_state(self._device_key).get("power", False)

    async def async_set_percentage(self, percentage: int):
        """Set the speed of the fan."""
        is_on = percentage > 0
        await self._state_manager.set_device_state(self._device_key, "power", is_on)
        await self._state_manager.set_device_state(self._device_key, "percentage", percentage)
        self._attr_percentage = percentage
        self._attr_is_on = is_on
        self._hass.states.async_set(
            self.entity_id,
            "on" if is_on else "off",
            {"percentage": percentage}
        )
        self.async_write_ha_state()

    async def async_turn_on(self, percentage: int = 100, **kwargs):
        """Turn the fan on."""
        if percentage is None:
            percentage = 100
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "percentage", 0)
        self._attr_percentage = 0
        self._attr_is_on = False
        self._hass.states.async_set(self.entity_id, "off", {"percentage": 0})
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the fan."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
