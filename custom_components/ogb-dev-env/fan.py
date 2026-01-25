"""OGB Dev fans."""
import asyncio
import logging
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .devices import TEST_DEVICES
from . import OGBDevRestoreEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev fans."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        device_type = device_config.get("type")
        _LOGGER.debug(f"Checking device {device_key}: type={device_type}")
        if device_type in ["Exhaust", "Intake", "Ventilation"] and "sensors" in device_config and any(s.get("name") == "duty" for s in device_config["sensors"]):
            _LOGGER.debug(f"Creating fan for {device_key}")
            fan = OGBDevFan(
                hass=hass,
                entry=entry,
                device_config=device_config,
                device_key=device_key
            )
            entities.append(fan)

    _LOGGER.debug(f"Created {len(entities)} fan entities")
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
        self._duty = 0
        
        data_entry = self._hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        if isinstance(data_entry, dict):
            self._state_manager = data_entry.get("state_manager")
        else:
            self._state_manager = data_entry
            
        self._state = self._state_manager.get_device_state(device_key) if self._state_manager else {}

        self._attr_unique_id = f"{self._entry.entry_id}_{device_config['device_id']}_fan"
        self._attr_entity_id = f"fan.{device_config['device_id']}"
        self._attr_name = device_config["name"]
        self._attr_is_on = False
        self._attr_percentage = 0
        self._duty = self._state.get("percentage", 0)
        self._attr_supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

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

        if restored_percentage is not None:
            self._duty = int(restored_percentage)
        else:
            self._duty = self._state.get("percentage", 0)
            
        is_on = bool(restored_power) if restored_power is not None else False

        if self._duty > 0:
            is_on = True

        await self._state_manager.set_device_state(self._device_key, "percentage", self._duty)
        await self._state_manager.set_device_state(self._device_key, "power", is_on)

        self._attr_percentage = self._duty if is_on else 0
        self._attr_is_on = is_on
        self._attr_extra_state_attributes = {"duty": self._duty}
        self._hass.states.async_set(
            self.entity_id,
            "on" if is_on else "off",
            {"percentage": self._attr_percentage, "duty": self._duty}
        )
        self.async_write_ha_state()
        
        _LOGGER.debug(f"Fan {self.entity_id} initialized: is_on={is_on}, percentage={self._attr_percentage}, duty={self._duty}")

    @property
    def percentage(self):
        """Return the current percentage."""
        return self._attr_percentage

    @property
    def is_on(self):
        """Return true if fan is on."""
        return self._attr_is_on

    async def async_set_percentage(self, percentage: int):
        """Set the speed of the fan."""
        is_on = percentage > 0
        self._duty = percentage
        self._attr_extra_state_attributes = {"duty": self._duty}
        await self._state_manager.set_device_state(self._device_key, "power", is_on)
        await self._state_manager.set_device_state(self._device_key, "percentage", percentage)
        self._attr_percentage = percentage
        self._attr_is_on = is_on
        self._hass.states.async_set(
            self.entity_id,
            "on" if is_on else "off",
            {"percentage": percentage, "duty": self._duty}
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
        self._duty = 0
        self._attr_extra_state_attributes = {"duty": self._duty}
        self._hass.states.async_set(self.entity_id, "off", {"percentage": 0, "duty": 0})
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the fan."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
