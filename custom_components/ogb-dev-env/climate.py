"""OGB Dev climate."""
import asyncio
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode, HVACAction
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import UnitOfTemperature
from .const import DOMAIN
from .devices import TEST_DEVICES


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev climate."""
    entities = []

    # Create a single climate entity for temperature control using heater and cooler
    climate = OGBDevClimate(
        hass=hass,
        entry=entry
    )
    entities.append(climate)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev climate."""
    return True


class OGBDevClimate(ClimateEntity):
    """OGB Dev climate control."""

    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]

        # Entity properties
        self._attr_unique_id = "ogb_dev_climate"
        self._attr_name = "OGB Dev Climate Control"

        # Climate properties
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature = 23.0
        self._attr_min_temp = 10
        self._attr_max_temp = 50
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        # Device info - use a virtual device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "climate_control")},
            "name": "Climate Control",
            "manufacturer": "OpenGrowBox",
            "model": "Dev Environment",
        }

    async def async_added_to_hass(self):
        """Ensure initial state is off."""
        await super().async_added_to_hass()
        self._attr_hvac_mode = HVACMode.OFF
        self._hass.states.async_set(self.entity_id, "off")
        self.async_write_ha_state()

    @property
    def current_temperature(self):
        """Return the current temperature mirrored from DevSensor1."""
        temp = self._state_manager.environment["air_temperature"]
        # Mirror DevSensor1: base + 0.05 for variation
        temp += 0.05
        return round(temp, 2)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._attr_target_temperature

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        heater_state = self._state_manager.get_device_state("heater").get("power", False)
        cooler_state = self._state_manager.get_device_state("cooler").get("power", False)
        dehumidifier_state = self._state_manager.get_device_state("dehumidifier").get("power", False)
        if heater_state:
            return HVACMode.HEAT
        elif cooler_state:
            return HVACMode.COOL
        elif dehumidifier_state:
            return HVACMode.DRY
        else:
            return HVACMode.OFF

    @property
    def hvac_action(self):
        """Return the current running hvac operation."""
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            return HVACAction.HEATING
        elif mode == HVACMode.COOL:
            return HVACAction.COOLING
        elif mode == HVACMode.DRY:
            return HVACAction.DRYING
        else:
            return HVACAction.OFF

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if "temperature" in kwargs:
            self._attr_target_temperature = kwargs["temperature"]
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._state_manager.set_device_state("heater", "power", False)
            await self._state_manager.set_device_state("cooler", "power", False)
            await self._state_manager.set_device_state("dehumidifier", "power", False)
        elif hvac_mode == HVACMode.HEAT:
            await self._state_manager.set_device_state("heater", "power", True)
            await self._state_manager.set_device_state("cooler", "power", False)
            await self._state_manager.set_device_state("dehumidifier", "power", False)
        elif hvac_mode == HVACMode.COOL:
            await self._state_manager.set_device_state("heater", "power", False)
            await self._state_manager.set_device_state("cooler", "power", True)
            await self._state_manager.set_device_state("dehumidifier", "power", False)
        elif hvac_mode == HVACMode.DRY:
            await self._state_manager.set_device_state("heater", "power", False)
            await self._state_manager.set_device_state("cooler", "power", False)
            await self._state_manager.set_device_state("dehumidifier", "power", True)
        self.async_write_ha_state()