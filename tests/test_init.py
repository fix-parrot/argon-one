"""Tests for Argon ONE integration setup and unload."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_classic_setup_loads_fan_and_switch(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that Classic case type loads both fan and switch platforms."""
    await hass.config_entries.async_setup(mock_config_entry_classic.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("fan.argon_one_fan") is not None
    assert hass.states.get("switch.argon_one_always_on") is not None


async def test_pi5_setup_loads_fan_only(
    hass: HomeAssistant, mock_config_entry_pi5: MockConfigEntry, mock_smbus: MagicMock
) -> None:
    """Test that Pi 5 case type loads only the fan platform."""
    await hass.config_entries.async_setup(mock_config_entry_pi5.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("fan.argon_one_fan") is not None
    assert hass.states.get("switch.argon_one_always_on") is None


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that unloading the entry closes the bus."""
    await hass.config_entries.async_setup(mock_config_entry_classic.entry_id)
    await hass.async_block_till_done()

    await hass.config_entries.async_unload(mock_config_entry_classic.entry_id)
    await hass.async_block_till_done()

    mock_smbus.close.assert_called_once()
