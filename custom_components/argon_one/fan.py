"""Fan platform for Argon ONE."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.event import async_track_state_change_event

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import ArgonOneConfigEntry
from .const import (
    CASE_TYPE_PI5,
    CONF_CASE_TYPE,
    CONF_TEMP_SENSOR,
    DEFAULT_FAN_SPEED,
    DOMAIN,
    HYSTERESIS_CELSIUS,
    I2C_ADDRESS,
    PI5_FAN_REGISTER,
    PRESET_CURVES,
    PRESET_MODES,
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

    def __init__(self, entry: ArgonOneConfigEntry) -> None:
        """Initialize the fan."""
        self._bus = entry.runtime_data
        self._case_type = entry.data[CONF_CASE_TYPE]
        self._attr_unique_id = f"{entry.entry_id}_fan"
        self._percentage: int | None = None
        self._is_on = False
        self._preset_mode: str | None = None
        self._unsub_sensor: Callable[[], None] | None = None

        temp_sensor: str | None = entry.options.get(CONF_TEMP_SENSOR)
        self._temp_sensor_entity_id = temp_sensor

        features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )
        if temp_sensor:
            features |= FanEntityFeature.PRESET_MODE
            self._attr_preset_modes = list(PRESET_MODES)
        self._attr_supported_features = features

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

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        return self._preset_mode

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed percentage."""
        self._clear_preset()
        await self._async_send_speed(percentage)
        self._percentage = percentage
        self._is_on = percentage > 0

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the fan preset mode."""
        if preset_mode not in PRESET_CURVES:
            msg = f"Invalid preset mode: {preset_mode}"
            raise ValueError(msg)

        self._preset_mode = preset_mode
        self._subscribe_sensor()
        await self._async_apply_preset()
        self._is_on = True

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Turn on the fan."""
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is None:
            percentage = DEFAULT_FAN_SPEED
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Turn off the fan."""
        self._clear_preset()
        await self._async_send_speed(0)
        self._percentage = 0
        self._is_on = False

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        self._unsubscribe_sensor()

    # ------------------------------------------------------------------
    # Preset helpers
    # ------------------------------------------------------------------

    def _clear_preset(self) -> None:
        """Clear active preset and unsubscribe from sensor."""
        if self._preset_mode is not None:
            self._preset_mode = None
            self._unsubscribe_sensor()

    def _subscribe_sensor(self) -> None:
        """Subscribe to temperature sensor state changes."""
        self._unsubscribe_sensor()
        if self._temp_sensor_entity_id is None:
            return
        self._unsub_sensor = async_track_state_change_event(
            self.hass,
            [self._temp_sensor_entity_id],
            self._on_sensor_state_change,
        )

    def _unsubscribe_sensor(self) -> None:
        """Unsubscribe from temperature sensor."""
        if self._unsub_sensor is not None:
            self._unsub_sensor()
            self._unsub_sensor = None

    async def _on_sensor_state_change(self, _event: Event) -> None:
        """Handle temperature sensor state change."""
        await self._async_apply_preset()
        self.async_write_ha_state()

    async def _async_apply_preset(self) -> None:
        """Compute and send fan speed from current preset and sensor value."""
        if self._preset_mode is None or self._temp_sensor_entity_id is None:
            return

        state = self.hass.states.get(self._temp_sensor_entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            _LOGGER.warning(
                "Temperature sensor %s is unavailable, keeping current speed",
                self._temp_sensor_entity_id,
            )
            return

        try:
            temp = float(state.state)
        except ValueError:
            _LOGGER.warning(
                "Cannot parse temperature from %s: %s",
                self._temp_sensor_entity_id,
                state.state,
            )
            return

        speed = self._compute_speed(self._preset_mode, temp, self._percentage)
        await self._async_send_speed(speed)
        self._percentage = speed
        self._is_on = speed > 0

    @staticmethod
    def _compute_speed(
        preset_mode: str,
        temperature: float,
        current_speed: int | None = None,
    ) -> int:
        """Return fan speed for a preset curve with hysteresis."""
        curve = PRESET_CURVES[preset_mode]

        new_speed = 0
        for threshold, speed in curve:
            if temperature >= threshold:
                new_speed = speed
                break

        if current_speed is None or new_speed >= current_speed:
            return new_speed

        current_threshold = None
        for threshold, speed in curve:
            if speed == current_speed:
                current_threshold = threshold
                break

        if current_threshold is None:
            _LOGGER.warning(
                "Current speed not found in curve: "
                "preset=%s temp=%.2f current_speed=%s fallback_speed=%s",
                preset_mode,
                temperature,
                current_speed,
                new_speed,
            )
            return new_speed

        hold_until = current_threshold - HYSTERESIS_CELSIUS

        if temperature >= hold_until:
            _LOGGER.debug(
                "Hold fan speed: "
                "preset=%s temp=%.2f current_speed=%s hold_until_below=%.2f",
                preset_mode,
                temperature,
                current_speed,
                hold_until,
            )
            return current_speed

        _LOGGER.debug(
            "Decrease fan speed: preset=%s temp=%.2f old_speed=%s new_speed=%s",
            preset_mode,
            temperature,
            current_speed,
            new_speed,
        )
        return new_speed

    # ------------------------------------------------------------------
    # I2C
    # ------------------------------------------------------------------

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
