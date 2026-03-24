"""Config flow for Argon ONE integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    CASE_TYPE_PI5,
    CASE_TYPES,
    CONF_CASE_TYPE,
    CONF_TEMP_SENSOR,
    DOMAIN,
    ERR_I2C_DEVICE_NOT_FOUND,
    ERR_I2C_NOT_AVAILABLE,
    I2C_ADDRESS,
    I2C_BUS_NUMBER,
    PI5_FAN_REGISTER,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CASE_TYPE): vol.In(CASE_TYPES),
    }
)


def _test_i2c(case_type: str) -> str | None:
    """
    Test I2C bus availability and device presence.

    Returns None on success or an error key string.
    """
    if not Path(f"/dev/i2c-{I2C_BUS_NUMBER}").exists():
        return ERR_I2C_NOT_AVAILABLE

    try:
        from smbus2 import SMBus  # noqa: PLC0415

        bus = SMBus(I2C_BUS_NUMBER)
        try:
            if case_type == CASE_TYPE_PI5:
                bus.read_byte_data(I2C_ADDRESS, PI5_FAN_REGISTER)
            else:
                bus.write_byte(I2C_ADDRESS, 0)
        finally:
            bus.close()
    except OSError as err:
        _LOGGER.warning("I2C device not found at 0x%02X: %s", I2C_ADDRESS, err)
        return ERR_I2C_DEVICE_NOT_FOUND
    except Exception:
        _LOGGER.exception("Unexpected error during I2C test")
        return ERR_I2C_NOT_AVAILABLE

    return None


class ArgonOneConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Argon ONE."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,  # noqa: ARG004
    ) -> ArgonOneOptionsFlow:
        """Create the options flow."""
        return ArgonOneOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        try:
            error = await self.hass.async_add_executor_job(
                _test_i2c, user_input[CONF_CASE_TYPE]
            )
        except Exception:
            _LOGGER.exception("Unexpected error in config flow")
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": ERR_I2C_NOT_AVAILABLE},
            )

        if error is not None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": error},
            )

        return self.async_create_entry(title="Argon ONE", data=user_input)


class ArgonOneOptionsFlow(OptionsFlowWithReload):
    """Handle options for Argon ONE."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_TEMP_SENSOR): EntitySelector(
                    EntitySelectorConfig(
                        device_class="temperature",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema, self.config_entry.options
            ),
        )
