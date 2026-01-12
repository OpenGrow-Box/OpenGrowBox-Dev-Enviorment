"""OGB Dev Environment."""

import logging
import asyncio
from datetime import timedelta
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr, area_registry as ar
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN
from .devices import TEST_DEVICES
from .environment import EnvironmentSimulator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OGB Dev from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Check if this entry is already set up to prevent duplicate initialization
    if entry.entry_id in hass.data[DOMAIN]:
        _LOGGER.debug(
            f"Entry {entry.entry_id} already set up, skipping duplicate setup"
        )
        return True

    # Create state manager
    state_manager = DevStateManager(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state_manager
    await state_manager.async_setup()

    # Create device manager
    device_manager = DevDeviceManager(hass, entry)
    await device_manager.async_setup_devices()

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch", "number", "light", "fan", "climate", "humidifier", "select"])

    # Force initial states to off for all entities
    await asyncio.sleep(1)  # Wait for entities to be added
    for entity_id in hass.states.async_entity_ids():
        if entity_id.startswith("switch.ogb") or entity_id.startswith("light.ogb") or entity_id.startswith("fan.ogb") or entity_id.startswith("climate.ogb") or entity_id.startswith("humidifier.ogb"):
            state = hass.states.get(entity_id)
            if state and state.state != "off":
                hass.states.async_set(entity_id, "off")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        await hass.data[DOMAIN][entry.entry_id].async_unload()
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch", "number", "light", "fan", "climate", "humidifier", "select"])


class DevDeviceManager:
    """Manages OGB Dev devices."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.device_registry = dr.async_get(hass)
        self.area_registry = ar.async_get(hass)
        self.area_name = entry.data.get("area_name", "Grow Room")
        self.area = self.area_registry.async_get_or_create(name=self.area_name)


    async def async_setup_devices(self):
        """Create all test devices."""
        for device_key, device_config in TEST_DEVICES.items():
            device_id = device_config["name"].lower()

            # Create device in registry
            device = self.device_registry.async_get_or_create(
                config_entry_id=self.entry.entry_id,
                identifiers={(DOMAIN, device_id)},
                name=device_config["name"],
                manufacturer=device_config.get("manufacturer", "OpenGrowBox"),
                model=device_config.get("model", "Dev Environment"),
                sw_version="1.0.0",
            )

            # Assign to area
            self.device_registry.async_update_device(device.id, area_id=self.area.id)

            # Labels not supported in this HA version

            # Store device info for sensors
            device_config["device_id"] = device_id
            device_config["registry_device"] = device

            _LOGGER.info(f"Created device: {device_config['name']} ({device_id})")


class DevStateManager:
    """Manages state and simulation for OGB Dev devices."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.device_states = {}
        self.environment_simulator = EnvironmentSimulator()
        self.environment = self.environment_simulator.environment
        self._update_task = None

    async def async_setup(self):
        """Initialize state manager."""
        # Initialize device states from config
        for device_key, device_config in TEST_DEVICES.items():
            self.device_states[device_key] = device_config["state"].copy()

        # Schedule periodic updates every 30 seconds
        self._update_task = async_track_time_interval(
            self.hass, self._async_update_simulation, timedelta(seconds=30)
        )

    async def async_unload(self):
        """Unload state manager."""
        if self._update_task:
            self._update_task()
            self._update_task = None

    def get_device_state(self, device_key):
        """Get state for a device."""
        return self.device_states.get(device_key, {})

    def set_device_state(self, device_key, key, value):
        """Set state for a device."""
        if device_key in self.device_states:
            self.device_states[device_key][key] = value



    @callback
    async def _async_update_simulation(self, now):
        """Periodic simulation update."""
        self.environment = self.environment_simulator.update_environment(self.device_states)

        # Notify platforms to update
        # Since sensors pull from config, perhaps modify the config values
        # But better to make sensors dynamic in platform