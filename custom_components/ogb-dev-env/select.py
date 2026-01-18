"""OGB Dev select."""
import asyncio
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity
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


class OGBDevSeasonSelect(SelectEntity, RestoreEntity):
    """OGB Dev season select."""

    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        
        data_entry = self._hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        if isinstance(data_entry, dict):
            self._state_manager = data_entry.get("state_manager")
        else:
            self._state_manager = data_entry
            
        self._current_option = "summer"

        # Entity properties
        self._attr_unique_id = f"ogb_dev_env_season_{self._entry.entry_id}"
        self._attr_name = "OGB Dev Season"
        self._attr_options = ["spring", "spring_dry", "spring_wet", "summer", "summer_dry", "summer_wet", "fall", "fall_dry", "fall_wet", "winter", "winter_dry", "winter_wet"]
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
        if (state := await self.async_get_last_state()) is not None:
            self._current_option = state.state
            self._state_manager.environment_simulator.set_season(state.state)
        else:
            self._current_option = self._state_manager.environment_simulator.season
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