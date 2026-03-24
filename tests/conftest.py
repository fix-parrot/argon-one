"""Shared test fixtures for Argon ONE integration tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argon_one.const import (
    CASE_TYPE_CLASSIC,
    CASE_TYPE_PI5,
    CONF_CASE_TYPE,
    CONF_TEMP_SENSOR,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations for all tests."""


@pytest.fixture
def mock_smbus():
    """Patch smbus2.SMBus everywhere it's imported and return the mock instance."""
    mock_bus = MagicMock()
    with (
        patch("custom_components.argon_one.SMBus", return_value=mock_bus),
        patch("smbus2.SMBus", return_value=mock_bus),
    ):
        yield mock_bus


@pytest.fixture
def mock_config_entry_classic(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry for Classic case type."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Argon ONE",
        data={CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
        options={},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry_pi5(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry for Pi 5 case type."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Argon ONE",
        data={CONF_CASE_TYPE: CASE_TYPE_PI5},
        options={},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry_with_sensor(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock Classic config entry with a temperature sensor configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Argon ONE",
        data={CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
        options={CONF_TEMP_SENSOR: "sensor.mock_temperature"},
    )
    entry.add_to_hass(hass)
    return entry
