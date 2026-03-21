"""Argon ONE integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from smbus2 import SMBus

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import CASE_TYPE_CLASSIC, CONF_CASE_TYPE, I2C_BUS_NUMBER

_LOGGER = logging.getLogger(__name__)

PLATFORMS_CLASSIC = [Platform.FAN, Platform.SWITCH]
PLATFORMS_PI5 = [Platform.FAN]

type ArgonOneConfigEntry = ConfigEntry[SMBus]


async def async_setup_entry(hass: HomeAssistant, entry: ArgonOneConfigEntry) -> bool:
    """Set up Argon ONE from a config entry."""
    bus = await hass.async_add_executor_job(SMBus, I2C_BUS_NUMBER)
    entry.runtime_data = bus

    case_type = entry.data[CONF_CASE_TYPE]
    platforms = PLATFORMS_CLASSIC if case_type == CASE_TYPE_CLASSIC else PLATFORMS_PI5
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ArgonOneConfigEntry) -> bool:
    """Unload a config entry."""
    case_type = entry.data[CONF_CASE_TYPE]
    platforms = PLATFORMS_CLASSIC if case_type == CASE_TYPE_CLASSIC else PLATFORMS_PI5
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        bus: SMBus = entry.runtime_data
        await hass.async_add_executor_job(bus.close)
    return unload_ok
