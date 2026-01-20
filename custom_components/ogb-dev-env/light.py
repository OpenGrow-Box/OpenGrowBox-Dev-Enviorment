"""OGB Dev lights."""
import asyncio
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .devices import TEST_DEVICES
from . import OGBDevRestoreEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev lights."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        if device_config.get("type") != "Light":
            continue

        if "setters" in device_config and device_config["setters"]:
            light = OGBDevLight(
                hass=hass,
                entry=entry,
                device_config=device_config,
                device_key=device_key
            )
            entities.append(light)
        else:
            spectrum_light = OGBDevSpectrumLight(
                hass=hass,
                entry=entry,
                device_config=device_config,
                device_key=device_key
            )
            entities.append(spectrum_light)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev lights."""
    return True


class OGBDevLight(OGBDevRestoreEntity, LightEntity):
    """OGB Dev light with state restoration."""

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

        self._attr_unique_id = f"{self._entry.entry_id}_{device_config['device_id']}_light"
        self._attr_name = device_config["name"]
        self._attr_is_on = False
        intensity = self._state.get("intensity", 0)
        self._attr_brightness = int((intensity / 100) * 255)

        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }

    async def async_added_to_hass(self):
        """Restore state on startup."""
        await super().async_added_to_hass()

        restored_intensity = await self._async_restore_device_state(
            self._device_key, "intensity"
        )
        if restored_intensity is not None:
            intensity = int(restored_intensity)
        else:
            intensity = 0

        restored_power = await self._async_restore_device_state(
            self._device_key, "power"
        )
        is_on = bool(restored_power) if restored_power is not None else False

        await self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        await self._state_manager.set_device_state(self._device_key, "power", is_on)

        self._attr_is_on = is_on
        self._attr_brightness = int((intensity / 100) * 255)
        self._hass.states.async_set(
            self.entity_id,
            "on" if is_on else "off",
            {"brightness": self._attr_brightness}
        )
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state_manager.get_device_state(self._device_key).get("power", False)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        intensity = self._state_manager.get_device_state(self._device_key).get("intensity", 0)
        return int((intensity / 100) * 255)

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if "brightness_pct" in kwargs:
            intensity = kwargs["brightness_pct"]
        elif "brightness" in kwargs:
            intensity = int((kwargs["brightness"] / 255) * 100)
        else:
            intensity = 100

        if intensity == 0:
            await self.async_turn_off()
            return

        await self._state_manager.set_device_state(self._device_key, "power", True)
        await self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._attr_is_on = True
        self._attr_brightness = int((intensity / 100) * 255)
        self._hass.states.async_set(self.entity_id, "on", {"brightness": self._attr_brightness})
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "intensity", 0)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._attr_is_on = False
        self._attr_brightness = 0
        self.async_write_ha_state()
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})

    async def async_toggle(self, **kwargs):
        """Toggle the light."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()


class OGBDevSpectrumLight(OGBDevRestoreEntity, LightEntity):
    """OGB Dev spectrum light (UV, Blue, Red, IR) with state restoration."""

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

        self._attr_unique_id = f"{self._entry.entry_id}_{device_config['device_id']}_light"
        self._attr_name = device_config["name"]
        self._attr_is_on = False

        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

        intensity = self._state.get("intensity", 0)
        self._attr_brightness = int((intensity / 100) * 255)

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_config["device_id"])},
            "name": device_config["name"],
            "manufacturer": device_config.get("manufacturer", "OpenGrowBox"),
            "model": device_config.get("model", "Dev Environment"),
        }

    async def async_added_to_hass(self):
        """Restore state on startup."""
        await super().async_added_to_hass()

        restored_intensity = await self._async_restore_device_state(
            self._device_key, "intensity"
        )
        if restored_intensity is not None:
            intensity = int(restored_intensity)
        else:
            intensity = 0

        restored_power = await self._async_restore_device_state(
            self._device_key, "power"
        )
        is_on = bool(restored_power) if restored_power is not None else False

        await self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        await self._state_manager.set_device_state(self._device_key, "power", is_on)

        self._attr_is_on = is_on
        self._attr_brightness = int((intensity / 100) * 255)
        self._hass.states.async_set(
            self.entity_id,
            "on" if is_on else "off",
            {"brightness": self._attr_brightness}
        )
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state_manager.get_device_state(self._device_key).get("power", False)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        intensity = self._state_manager.get_device_state(self._device_key).get("intensity", 0)
        return int((intensity / 100) * 255)

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if "brightness_pct" in kwargs:
            intensity = kwargs["brightness_pct"]
        elif "brightness" in kwargs:
            intensity = int((kwargs["brightness"] / 255) * 100)
        else:
            intensity = 100

        if intensity == 0:
            await self.async_turn_off()
            return

        await self._state_manager.set_device_state(self._device_key, "power", True)
        await self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._attr_is_on = True
        self._attr_brightness = int((intensity / 100) * 255)
        self._hass.states.async_set(self.entity_id, "on", {"brightness": self._attr_brightness})
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "intensity", 0)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._attr_is_on = False
        self._attr_brightness = 0
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the light."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
