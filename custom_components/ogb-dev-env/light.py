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
        if device_config.get("type") == "Light" and "setters" in device_config and device_config["setters"]:
            light = OGBDevLight(
                hass=hass,
                entry=entry,
                device_config=device_config,
                device_key=device_key
            )
            entities.append(light)

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
        self._attr_unique_id = f"{device_config['device_id']}_light"
        self._attr_unique_id = f"dev{device_config['name'].replace('Dev', '').lower()}"
        self._attr_name = device_config["name"]
        self._attr_is_on = False
        self._attr_brightness = 0

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
        self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
        self.async_write_ha_state()

        # Delayed OFF to override HA restoration
        async def delayed_off():
            await asyncio.sleep(10)
            self._hass.states.async_set(self.entity_id, "off", {"brightness": 0})
            self.async_write_ha_state()

        self._hass.async_create_task(delayed_off())

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
        self._state_manager.set_device_state(self._device_key, "power", True)
        if "brightness" in kwargs:
            brightness = kwargs["brightness"]
            intensity = int((brightness / 255) * 100)
            self._state_manager.set_device_state(self._device_key, "intensity", intensity)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        self._state_manager.set_device_state(self._device_key, "power", False)
        self.async_write_ha_state()