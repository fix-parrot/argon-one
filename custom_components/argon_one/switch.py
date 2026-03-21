"""Switch platform for Argon ONE Always ON mode."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import ArgonOneConfigEntry
from .const import (
    CMD_POWER_ALWAYS_ON,
    CMD_POWER_DEFAULT,
    DOMAIN,
    I2C_ADDRESS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ArgonOneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Argon ONE always-on switch."""
    async_add_entities([ArgonOneAlwaysOnSwitch(entry)])


class ArgonOneAlwaysOnSwitch(SwitchEntity):
    """Switch for Argon ONE Always ON power mode."""

    _attr_has_entity_name = True
    _attr_name = "Always ON"
    _attr_icon = "mdi:power-plug"

    def __init__(self, entry: ArgonOneConfigEntry) -> None:
        """Initialize the switch."""
        self._bus = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_always_on"
        self._is_on: bool | None = None  # unknown after reboot
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Argon ONE",
            "manufacturer": "Argon Forty",
            "model": "Argon ONE Classic (Pi 3/4)",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if Always ON mode is enabled."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Enable Always ON mode."""
        try:
            await self.hass.async_add_executor_job(
                self._bus.write_byte,
                I2C_ADDRESS,
                CMD_POWER_ALWAYS_ON,
            )
        except OSError:
            _LOGGER.exception("I2C error enabling Always ON")
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._is_on = True
        self._attr_available = True

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Disable Always ON mode (set Default)."""
        try:
            await self.hass.async_add_executor_job(
                self._bus.write_byte,
                I2C_ADDRESS,
                CMD_POWER_DEFAULT,
            )
        except OSError:
            _LOGGER.exception("I2C error disabling Always ON")
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._is_on = False
        self._attr_available = True
