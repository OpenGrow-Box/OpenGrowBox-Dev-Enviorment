"""OGB Dev select."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up OGB Dev select."""
    entities = []

    season_select = OGBDevSeasonSelect(hass, entry)
    entities.append(season_select)

    if entities:
        async_add_entities(entities)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload OGB Dev select."""
    return True


class OGBDevSeasonSelect(SelectEntity):
    """OGB Dev season select."""

    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        self._state_manager = self._hass.data[DOMAIN][self._entry.entry_id]
        self._current_option = "spring"

        # Entity properties
        self._attr_unique_id = f"ogb_dev_env_season_{self._entry.entry_id}"
        self._attr_name = "OGB Dev Season"
        self._attr_options = ["spring", "summer", "fall", "winter"]
        self._attr_current_option = self._current_option

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "environment_control")},
            "name": "Environment Control",
            "manufacturer": "OpenGrowBox",
            "model": "Dev Environment",
        }

    async def async_added_to_hass(self):
        """Ensure proper entity registration."""
        await super().async_added_to_hass()
        self.async_write_ha_state()

    @property
    def current_option(self):
        """Return the current selected option."""
        return self._current_option

    async def async_select_option(self, option):
        """Change the selected option."""
        try:
            self._current_option = option
            self._state_manager.environment_simulator.set_season(option)
            self.async_write_ha_state()
        except Exception as e:
            # Log error but don't fail the selection
            self._hass.logger.error("Error setting season to %s: %s", option, str(e))
            raise