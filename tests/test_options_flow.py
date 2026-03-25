"""Tests for Argon ONE options flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argon_one.const import CONF_TEMP_SENSOR


async def test_set_temperature_sensor(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test setting a temperature sensor in options flow."""
    await hass.config_entries.async_setup(mock_config_entry_classic.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        mock_config_entry_classic.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_TEMP_SENSOR: "sensor.mock_temperature"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_TEMP_SENSOR: "sensor.mock_temperature"}


async def test_clear_temperature_sensor(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test clearing the temperature sensor in options flow."""
    await hass.config_entries.async_setup(mock_config_entry_with_sensor.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        mock_config_entry_with_sensor.entry_id
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_TEMP_SENSOR not in result["data"]
