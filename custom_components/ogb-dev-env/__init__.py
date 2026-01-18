"""OGB Dev Environment."""
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr, area_registry as ar
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
import json
from .const import DOMAIN
from .devices import TEST_DEVICES
from .environment import EnvironmentSimulator

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OGB Dev from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if entry.entry_id in hass.data[DOMAIN]:
        return True

    state_store = OGBDevStore(hass, entry.entry_id)

    state_manager = DevStateManager(hass, entry, state_store)
    hass.data[DOMAIN][entry.entry_id] = state_manager

    device_manager = DevDeviceManager(hass, entry)
    await device_manager.async_setup_devices()

    coordinator = OGBDevCoordinator(hass, entry, state_manager)
    await coordinator.async_load_stored_states()
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor", "switch", "light", "fan", "climate", "humidifier", "select"]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        state_manager = hass.data[DOMAIN][entry.entry_id]
        await state_manager.async_save_states()
        if "coordinator" in hass.data[DOMAIN][entry.entry_id]:
            await hass.data[DOMAIN][entry.entry_id]["coordinator"].async_shutdown()
    return await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "switch", "light", "fan", "climate", "humidifier", "select"]
    )


class OGBDevStore:
    """Storage for device states."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        self.hass = hass
        self.entry_id = entry_id
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")

    async def async_save(self, data: dict) -> None:
        """Save data to storage."""
        try:
            await self._store.async_save(data)
            _LOGGER.debug("Saved device states to storage")
        except Exception as ex:
            _LOGGER.error(f"Failed to save device states: {ex}")

    async def async_load(self) -> dict | None:
        """Load data from storage."""
        try:
            data = await self._store.async_load()
            if data:
                _LOGGER.debug("Loaded device states from storage")
            return data
        except Exception as ex:
            _LOGGER.error(f"Failed to load device states: {ex}")
            return None


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

            device = self.device_registry.async_get_or_create(
                config_entry_id=self.entry.entry_id,
                identifiers={(DOMAIN, device_id)},
                name=device_config["name"],
                manufacturer=device_config.get("manufacturer", "OpenGrowBox"),
                model=device_config.get("model", "Dev Environment"),
                sw_version="1.0.0",
            )

            self.device_registry.async_update_device(device.id, area_id=self.area.id)

            device_config["device_id"] = device_id
            device_config["registry_device"] = device

            _LOGGER.debug(f"Created device: {device_config['name']} ({device_id})")


class DevStateManager:
    """Manages state and simulation for OGB Dev devices."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: OGBDevStore):
        self.hass = hass
        self.entry = entry
        self.store = store
        self.device_states = {}
        self.environment_simulator = EnvironmentSimulator()
        self.environment = self.environment_simulator.environment
        self._update_task = None

    async def async_setup(self):
        """Initialize state manager."""
        for device_key, device_config in TEST_DEVICES.items():
            self.device_states[device_key] = dict(device_config["state"])

        self._update_task = async_track_time_interval(
            self.hass, self._async_update_simulation, timedelta(seconds=30)
        )

    async def async_unload(self):
        """Unload state manager."""
        if self._update_task:
            self._update_task()
            self._update_task = None

    async def async_save_states(self):
        """Save current device states to storage."""
        data = {
            "device_states": self.device_states,
            "environment": self.environment,
        }
        await self.store.async_save(data)

    async def async_load_stored_states(self) -> dict:
        """Load and apply stored device states."""
        data = await self.store.async_load()
        if data and isinstance(data, dict):
            if "device_states" in data:
                for key, state in data["device_states"].items():
                    if key in self.device_states:
                        self.device_states[key].update(state)
            if "environment" in data and isinstance(data["environment"], dict):
                self.environment = data["environment"]
                self.environment_simulator.environment = data["environment"]
            _LOGGER.debug("Restored device states from storage")
        return self.device_states

    def get_device_state(self, device_key):
        """Get state for a device."""
        return self.device_states.get(device_key, {})

    async def set_device_state(self, device_key, key, value):
        """Set state for a device."""
        if device_key in self.device_states:
            self.device_states[device_key][key] = value
        await self._async_update_simulation(None)

    @callback
    async def _async_update_simulation(self, now):
        """Periodic simulation update."""
        weather_data = {"temp": None, "hum": None}
        weather_entity = self.hass.states.get("weather.home")
        if weather_entity:
            weather_data["temp"] = weather_entity.attributes.get("temperature")
            weather_data["hum"] = weather_entity.attributes.get("humidity")

        self.environment = self.environment_simulator.update_environment(
            self.device_states, weather_data
        )

        self.environment["air_temperature"] = round(self.environment["air_temperature"], 1)
        self.environment["air_humidity"] = round(self.environment["air_humidity"], 1)


class OGBDevCoordinator:
    """Coordinator for OGB Dev Environment simulation."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, state_manager: DevStateManager):
        self.hass = hass
        self.entry = entry
        self.state_manager = state_manager
        self._update_task = None
        self._unsub_setup = None

    async def async_load_stored_states(self):
        """Load stored states on startup."""
        await self.state_manager.async_load_stored_states()
        self._update_task = async_track_time_interval(
            self.hass, self._async_update, timedelta(seconds=30)
        )

    @callback
    async def _async_update(self, now=None):
        """Update simulation."""
        await self.state_manager.async_save_states()

    async def async_shutdown(self):
        """Shutdown coordinator."""
        if self._update_task:
            self._update_task()
            self._update_task = None
        await self.state_manager.async_save_states()


class OGBDevRestoreEntity(RestoreEntity):
    """Mixin for restoring entity states."""

    async def _async_restore_state(self, state_key: str, default=None):
        """Restore state from HA storage."""
        if state := await self.async_get_last_state():
            if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                try:
                    value = float(state.state)
                    _LOGGER.debug(
                        f"Restored {self.entity_id} {state_key} = {value}"
                    )
                    return value
                except (ValueError, TypeError):
                    pass
        return default

    async def _async_restore_device_state(self, device_key: str, state_key: str):
        """Restore device state and apply to state manager."""
        if state := await self.async_get_last_state():
            if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                try:
                    value = float(state.state)
                    state_manager = self.hass.data[DOMAIN][self._entry.entry_id]
                    await state_manager.set_device_state(device_key, state_key, value)
                    _LOGGER.debug(
                        f"Restored {device_key}.{state_key} = {value}"
                    )
                    return value
                except (ValueError, TypeError):
                    pass
        return None
