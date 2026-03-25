"""Tests for Argon ONE config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argon_one.const import (
    CASE_TYPE_CLASSIC,
    CASE_TYPE_PI5,
    CONF_CASE_TYPE,
    DOMAIN,
    ERR_I2C_DEVICE_NOT_FOUND,
    ERR_I2C_NOT_AVAILABLE,
)


async def test_form_shown(hass: HomeAssistant) -> None:
    """Test that the user form is shown on first call."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_successful_setup_classic(hass: HomeAssistant) -> None:
    """Test successful config flow for Classic case type."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch("custom_components.argon_one.config_flow._test_i2c", return_value=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Argon ONE"
    assert result["data"] == {CONF_CASE_TYPE: CASE_TYPE_CLASSIC}


async def test_successful_setup_pi5(hass: HomeAssistant) -> None:
    """Test successful config flow for Pi 5 case type."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch("custom_components.argon_one.config_flow._test_i2c", return_value=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CASE_TYPE: CASE_TYPE_PI5},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CASE_TYPE: CASE_TYPE_PI5}


async def test_i2c_not_available(hass: HomeAssistant) -> None:
    """Test error when I2C bus is not available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.argon_one.config_flow._test_i2c",
        return_value=ERR_I2C_NOT_AVAILABLE,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": ERR_I2C_NOT_AVAILABLE}


async def test_i2c_device_not_found(hass: HomeAssistant) -> None:
    """Test error when I2C device is not found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.argon_one.config_flow._test_i2c",
        return_value=ERR_I2C_DEVICE_NOT_FOUND,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": ERR_I2C_DEVICE_NOT_FOUND}


async def test_already_configured(hass: HomeAssistant) -> None:
    """Test abort when integration is already configured (single_config_entry)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Argon ONE",
        data={CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
    )
    entry.add_to_hass(hass)

    # single_config_entry: true → flow aborts immediately at init
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_unexpected_exception(hass: HomeAssistant) -> None:
    """Test error form when _test_i2c raises an unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    with patch(
        "custom_components.argon_one.config_flow._test_i2c",
        side_effect=RuntimeError("boom"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CASE_TYPE: CASE_TYPE_CLASSIC},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": ERR_I2C_NOT_AVAILABLE}
