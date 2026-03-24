"""Tests for Argon ONE Always ON switch entity."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argon_one.const import (
    CMD_POWER_ALWAYS_ON,
    CMD_POWER_DEFAULT,
    I2C_ADDRESS,
)

SWITCH_ENTITY_ID = "switch.argon_one_always_on"


async def _setup_switch(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the integration and wait for platform to load."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_turn_on(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test enabling Always ON mode."""
    await _setup_switch(hass, mock_config_entry_classic)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": SWITCH_ENTITY_ID}, blocking=True
    )

    mock_smbus.write_byte.assert_called_with(I2C_ADDRESS, CMD_POWER_ALWAYS_ON)
    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == "on"


async def test_turn_off(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test disabling Always ON mode."""
    await _setup_switch(hass, mock_config_entry_classic)

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH_ENTITY_ID}, blocking=True
    )

    mock_smbus.write_byte.assert_called_with(I2C_ADDRESS, CMD_POWER_DEFAULT)
    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == "off"


async def test_i2c_error_on_turn_on(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that I2C error on turn_on makes entity unavailable."""
    await _setup_switch(hass, mock_config_entry_classic)

    mock_smbus.write_byte.side_effect = OSError("I2C error")

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": SWITCH_ENTITY_ID}, blocking=True
    )

    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE


async def test_i2c_error_on_turn_off(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that I2C error on turn_off makes entity unavailable."""
    await _setup_switch(hass, mock_config_entry_classic)

    mock_smbus.write_byte.side_effect = OSError("I2C error")

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH_ENTITY_ID}, blocking=True
    )

    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE


async def test_i2c_recovery(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that entity recovers after I2C error."""
    await _setup_switch(hass, mock_config_entry_classic)

    # Cause error
    mock_smbus.write_byte.side_effect = OSError("I2C error")
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": SWITCH_ENTITY_ID}, blocking=True
    )
    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE

    # Recover — call entity method directly since HA skips unavailable entities
    mock_smbus.write_byte.side_effect = None
    entity = hass.data["entity_components"]["switch"].get_entity(SWITCH_ENTITY_ID)
    await entity.async_turn_on()
    entity.async_write_ha_state()

    state = hass.states.get(SWITCH_ENTITY_ID)
    assert state.state == "on"
