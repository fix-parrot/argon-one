"""Fan platform for Argon ONE."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.fan import FanEntity, FanEntityFeature

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import ArgonOneConfigEntry
from .const import (
    CASE_TYPE_PI5,
    CONF_CASE_TYPE,
    DEFAULT_FAN_SPEED,
    DOMAIN,
    I2C_ADDRESS,
    PI5_FAN_REGISTER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ArgonOneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Argon ONE fan from config entry."""
    async_add_entities([ArgonOneFan(entry)])


class ArgonOneFan(FanEntity):
    """Argon ONE case fan."""

    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, entry: ArgonOneConfigEntry) -> None:
        """Initialize the fan."""
        self._bus = entry.runtime_data
        self._case_type = entry.data[CONF_CASE_TYPE]
        self._attr_unique_id = f"{entry.entry_id}_fan"
        self._percentage: int | None = None
        self._is_on = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Argon ONE",
            "manufacturer": "Argon Forty",
            "model": (
                "Argon ONE V3/V5 (Pi 5)"
                if self._case_type == CASE_TYPE_PI5
                else "Argon ONE Classic (Pi 3/4)"
            ),
        }

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        return self._is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return self._percentage

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed percentage."""
        await self._async_send_speed(percentage)
        self._percentage = percentage
        self._is_on = percentage > 0

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Turn on the fan."""
        if percentage is None:
            percentage = DEFAULT_FAN_SPEED
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn off the fan."""
        await self._async_send_speed(0)
        self._percentage = 0
        self._is_on = False

    async def _async_send_speed(self, speed: int) -> None:
        """Send speed command via I2C."""
        try:
            if self._case_type == CASE_TYPE_PI5:
                await self.hass.async_add_executor_job(
                    self._bus.write_byte_data,
                    I2C_ADDRESS,
                    PI5_FAN_REGISTER,
                    speed,
                )
            else:
                await self.hass.async_add_executor_job(
                    self._bus.write_byte,
                    I2C_ADDRESS,
                    speed,
                )
        except OSError:
            _LOGGER.exception("I2C error setting fan speed")
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._attr_available = True
