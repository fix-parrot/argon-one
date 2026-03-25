"""Fake smbus2 module for development without I2C hardware."""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger("mock_smbus2")


class SMBus:
    """Mock SMBus that logs all I2C operations instead of performing real I2C."""

    def __init__(self, bus: int = 1) -> None:
        """Initialize the mock SMBus."""
        _LOGGER.info("MockSMBus: opened bus %d", bus)
        self._bus = bus

    def write_byte(self, addr: int, value: int) -> None:
        """Log a write_byte call."""
        _LOGGER.info("MockSMBus: write_byte(0x%02X, %d)", addr, value)

    def write_byte_data(self, addr: int, register: int, value: int) -> None:
        """Log a write_byte_data call."""
        _LOGGER.info(
            "MockSMBus: write_byte_data(0x%02X, 0x%02X, %d)", addr, register, value
        )

    def read_byte_data(self, addr: int, register: int) -> int:
        """Log a read_byte_data call and return 0."""
        _LOGGER.info("MockSMBus: read_byte_data(0x%02X, 0x%02X)", addr, register)
        return 0

    def close(self) -> None:
        """Log bus close."""
        _LOGGER.info("MockSMBus: closed bus %d", self._bus)
