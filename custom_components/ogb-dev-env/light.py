"""OGB Dev lights."""
import asyncio
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .devices import TEST_DEVICES


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev lights."""
    entities = []

    for device_key, device_config in TEST_DEVICES.items():
        if device_config.get("type") == "Light":
            if "setters" in device_config and device_config["setters"]:
                # Main light with brightness control
                light = OGBDevLight(
                    hass=hass,
                    entry=entry,
                    device_config=device_config,
                    device_key=device_key
                )
                entities.append(light)
            else:
                # Spectrum lights (UV, Blue, Red, IR) - on/off only
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


class OGBDevLight(LightEntity):
    """OGB Dev light."""

    def __init__(self, hass, entry, device_config, device_key):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._device_key = device_key
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]
        self._state = self._state_manager.get_device_state(device_key)

        # Entity properties
        self._attr_unique_id = f"{self._entry.entry_id}_{device_config['device_id']}_light"
        self._attr_name = device_config["name"]
        self._attr_is_on = False
        intensity = self._state.get("intensity", 0)
        self._attr_brightness = int((intensity / 100) * 255)

        # Light properties
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

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
        self._attr_brightness = 0
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "intensity", 0)
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state.get("power", False)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        intensity = self._state.get("intensity", 0)
        return int((intensity / 100) * 255)



    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if "brightness_pct" in kwargs:
            intensity = kwargs["brightness_pct"]
        elif "brightness" in kwargs:
            intensity = int((kwargs["brightness"] / 255) * 100)
        else:
            intensity = 100  # Default to full intensity

        if intensity == 0:
            await self.async_turn_off()
            return

        self._attr_is_on = True
        self._attr_brightness = int((intensity / 100) * 255)
        await self._state_manager.set_device_state(self._device_key, "power", True)
        await self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._hass.states.async_set(self.entity_id, "on", {"brightness": self._attr_brightness})
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        self._attr_is_on = False
        self._attr_brightness = 0
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "intensity", 0)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the light."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()


class OGBDevSpectrumLight(LightEntity):
    """OGB Dev spectrum light (UV, Blue, Red, IR) - with brightness control."""

    def __init__(self, hass, entry, device_config, device_key):
        self._hass = hass
        self._entry = entry
        self._device_config = device_config
        self._device_key = device_key
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]
        self._state = self._state_manager.get_device_state(device_key)

        # Entity properties
        self._attr_unique_id = f"{self._entry.entry_id}_{device_config['device_id']}_light"
        self._attr_name = device_config["name"]
        self._attr_is_on = False

        # Spectrum lights support brightness like main light
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

        # Initialize brightness from state
        intensity = self._state.get("intensity", 0)
        self._attr_brightness = int((intensity / 100) * 255)

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
        self._attr_brightness = 0
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "intensity", 0)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
        self.async_write_ha_state()

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state.get("power", False)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        intensity = self._state.get("intensity", 0)
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

        self._attr_is_on = True
        self._attr_brightness = int((intensity / 100) * 255)
        await self._state_manager.set_device_state(self._device_key, "power", True)
        await self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._hass.states.async_set(self.entity_id, "on", {"brightness": self._attr_brightness})
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        self._attr_is_on = False
        self._attr_brightness = 0
        await self._state_manager.set_device_state(self._device_key, "power", False)
        await self._state_manager.set_device_state(self._device_key, "intensity", 0)
        self._state = self._state_manager.get_device_state(self._device_key)
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs):
        """Toggle the light."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()