"""Tests for Argon ONE fan entity."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.components.fan import FanEntityFeature
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argon_one.const import (
    DEFAULT_FAN_SPEED,
    I2C_ADDRESS,
    PI5_FAN_REGISTER,
    PRESET_DEFAULT,
    PRESET_SILENT,
)

FAN_ENTITY_ID = "fan.argon_one_fan"


async def _setup_fan(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the integration and wait for platform to load."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_set_percentage(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test setting fan speed percentage."""
    await _setup_fan(hass, mock_config_entry_classic)

    await hass.services.async_call(
        "fan",
        "set_percentage",
        {"entity_id": FAN_ENTITY_ID, "percentage": 50},
        blocking=True,
    )

    mock_smbus.write_byte.assert_called_with(I2C_ADDRESS, 50)
    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["percentage"] == 50


async def test_turn_on_default_speed(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test turn_on without args uses DEFAULT_FAN_SPEED."""
    await _setup_fan(hass, mock_config_entry_classic)

    await hass.services.async_call(
        "fan", "turn_on", {"entity_id": FAN_ENTITY_ID}, blocking=True
    )

    mock_smbus.write_byte.assert_called_with(I2C_ADDRESS, DEFAULT_FAN_SPEED)
    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["percentage"] == DEFAULT_FAN_SPEED


async def test_turn_on_with_percentage(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test turn_on with a specific percentage."""
    await _setup_fan(hass, mock_config_entry_classic)

    await hass.services.async_call(
        "fan", "turn_on", {"entity_id": FAN_ENTITY_ID, "percentage": 75}, blocking=True
    )

    mock_smbus.write_byte.assert_called_with(I2C_ADDRESS, 75)
    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["percentage"] == 75


async def test_turn_off(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test turning off the fan."""
    await _setup_fan(hass, mock_config_entry_classic)

    # Turn on first
    await hass.services.async_call(
        "fan", "turn_on", {"entity_id": FAN_ENTITY_ID}, blocking=True
    )
    # Turn off
    await hass.services.async_call(
        "fan", "turn_off", {"entity_id": FAN_ENTITY_ID}, blocking=True
    )

    mock_smbus.write_byte.assert_called_with(I2C_ADDRESS, 0)
    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "off"
    assert state.attributes["percentage"] == 0


async def test_i2c_error_unavailable(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that I2C OSError makes entity unavailable."""
    await _setup_fan(hass, mock_config_entry_classic)

    mock_smbus.write_byte.side_effect = OSError("I2C error")

    await hass.services.async_call(
        "fan", "turn_on", {"entity_id": FAN_ENTITY_ID}, blocking=True
    )

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE


async def test_i2c_recovery(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that entity recovers after I2C error."""
    await _setup_fan(hass, mock_config_entry_classic)

    # Cause error
    mock_smbus.write_byte.side_effect = OSError("I2C error")
    await hass.services.async_call(
        "fan", "turn_on", {"entity_id": FAN_ENTITY_ID}, blocking=True
    )
    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE

    # Recover — call entity method directly since HA skips unavailable entities
    mock_smbus.write_byte.side_effect = None
    entity = hass.data["entity_components"]["fan"].get_entity(FAN_ENTITY_ID)
    await entity.async_set_percentage(30)
    entity.async_write_ha_state()

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["percentage"] == 30


async def test_pi5_protocol(
    hass: HomeAssistant, mock_config_entry_pi5: MockConfigEntry, mock_smbus: MagicMock
) -> None:
    """Test that Pi 5 uses write_byte_data instead of write_byte."""
    await _setup_fan(hass, mock_config_entry_pi5)

    await hass.services.async_call(
        "fan",
        "set_percentage",
        {"entity_id": FAN_ENTITY_ID, "percentage": 50},
        blocking=True,
    )

    mock_smbus.write_byte_data.assert_called_with(I2C_ADDRESS, PI5_FAN_REGISTER, 50)
    mock_smbus.write_byte.assert_not_called()


async def test_supported_features_without_sensor(
    hass: HomeAssistant,
    mock_config_entry_classic: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that PRESET_MODE is not in features without a sensor."""
    await _setup_fan(hass, mock_config_entry_classic)

    state = hass.states.get(FAN_ENTITY_ID)
    features = FanEntityFeature(state.attributes["supported_features"])
    assert not (features & FanEntityFeature.PRESET_MODE)
    assert features & FanEntityFeature.SET_SPEED


async def test_supported_features_with_sensor(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that PRESET_MODE is in features when a sensor is configured."""
    await _setup_fan(hass, mock_config_entry_with_sensor)

    state = hass.states.get(FAN_ENTITY_ID)
    features = FanEntityFeature(state.attributes["supported_features"])
    assert features & FanEntityFeature.PRESET_MODE


async def test_preset_mode_activation(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test activating a preset mode."""
    hass.states.async_set("sensor.mock_temperature", "65")
    await _setup_fan(hass, mock_config_entry_with_sensor)

    await hass.services.async_call(
        "fan",
        "set_preset_mode",
        {"entity_id": FAN_ENTITY_ID, "preset_mode": PRESET_DEFAULT},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["preset_mode"] == PRESET_DEFAULT
    # At 65°C on default curve → 60%
    assert state.attributes["percentage"] == 60


async def test_preset_mode_clear_on_set_percentage(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that setting percentage clears the preset mode."""
    hass.states.async_set("sensor.mock_temperature", "65")
    await _setup_fan(hass, mock_config_entry_with_sensor)

    await hass.services.async_call(
        "fan",
        "set_preset_mode",
        {"entity_id": FAN_ENTITY_ID, "preset_mode": PRESET_DEFAULT},
        blocking=True,
    )

    await hass.services.async_call(
        "fan",
        "set_percentage",
        {"entity_id": FAN_ENTITY_ID, "percentage": 30},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.attributes["preset_mode"] is None
    assert state.attributes["percentage"] == 30


async def test_sensor_state_change_triggers_speed(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that sensor state change recalculates fan speed."""
    hass.states.async_set("sensor.mock_temperature", "55")
    await _setup_fan(hass, mock_config_entry_with_sensor)

    await hass.services.async_call(
        "fan",
        "set_preset_mode",
        {"entity_id": FAN_ENTITY_ID, "preset_mode": PRESET_DEFAULT},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY_ID)
    # At 55°C on default → 25%
    assert state.attributes["percentage"] == 25

    # Change temperature to 70°C
    hass.states.async_set("sensor.mock_temperature", "70")
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    # At 70°C on default → 80%
    assert state.attributes["percentage"] == 80


async def test_sensor_unavailable_during_preset(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that sensor becoming unavailable keeps current speed."""
    hass.states.async_set("sensor.mock_temperature", "65")
    await _setup_fan(hass, mock_config_entry_with_sensor)

    await hass.services.async_call(
        "fan",
        "set_preset_mode",
        {"entity_id": FAN_ENTITY_ID, "preset_mode": PRESET_DEFAULT},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.attributes["percentage"] == 60

    # Sensor goes unavailable
    hass.states.async_set("sensor.mock_temperature", STATE_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    # Speed should remain unchanged
    assert state.attributes["percentage"] == 60


async def test_sensor_invalid_value_during_preset(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test that invalid sensor value keeps current speed."""
    hass.states.async_set("sensor.mock_temperature", "65")
    await _setup_fan(hass, mock_config_entry_with_sensor)

    await hass.services.async_call(
        "fan",
        "set_preset_mode",
        {"entity_id": FAN_ENTITY_ID, "preset_mode": PRESET_DEFAULT},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.attributes["percentage"] == 60

    # Sensor returns non-numeric value
    hass.states.async_set("sensor.mock_temperature", "not_a_number")
    await hass.async_block_till_done()

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.attributes["percentage"] == 60


async def test_turn_on_with_preset_mode(
    hass: HomeAssistant,
    mock_config_entry_with_sensor: MockConfigEntry,
    mock_smbus: MagicMock,
) -> None:
    """Test turn_on with preset_mode argument."""
    hass.states.async_set("sensor.mock_temperature", "70")
    await _setup_fan(hass, mock_config_entry_with_sensor)

    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": FAN_ENTITY_ID, "preset_mode": PRESET_SILENT},
        blocking=True,
    )

    state = hass.states.get(FAN_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["preset_mode"] == PRESET_SILENT
    # At 70°C on silent → 75%
    assert state.attributes["percentage"] == 75
