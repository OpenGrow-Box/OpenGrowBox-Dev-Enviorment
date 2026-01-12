"""Config flow for OGB Dev Environment."""

import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)
from homeassistant.helpers import selector

AREA_SCHEMA = vol.Schema({
    vol.Optional("area_name", default="°Demo Room"): str,
})


class ConfigFlow(config_entries.ConfigFlow,domain=DOMAIN):
    """Config flow for OGB Dev Environment."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.info("OGB Dev ConfigFlow step_user called")
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=AREA_SCHEMA,
            )

        return self.async_create_entry(
            title=f"OGB Dev Environment ({user_input['area_name']})",
            data=user_input,
        )

        return self.async_create_entry(
            title=f"OGB Dev Environment ({user_input['area_name']})",
            data=user_input,
        )

        # Simple schema - just a text input for room
        data_schema = vol.Schema({
            vol.Required("room"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )