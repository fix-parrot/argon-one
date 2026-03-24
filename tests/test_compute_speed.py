"""Unit tests for ArgonOneFan._compute_speed static method."""

from __future__ import annotations

import pytest

from custom_components.argon_one.const import (
    PRESET_DEFAULT,
    PRESET_PERFORMANCE,
    PRESET_SILENT,
)
from custom_components.argon_one.fan import ArgonOneFan


class TestComputeSpeedSilent:
    """Tests for the Silent preset curve."""

    # Silent: [(75, 100), (70, 75), (65, 50), (58, 25), (50, 10), (0, 0)]

    @pytest.mark.parametrize(
        ("temp", "expected"),
        [
            (100, 100),
            (75, 100),
            (74, 75),
            (70, 75),
            (69, 50),
            (65, 50),
            (64, 25),
            (58, 25),
            (57, 10),
            (50, 10),
            (49, 0),
            (0, 0),
        ],
    )
    def test_no_hysteresis(self, temp: float, expected: int) -> None:
        """Test speed lookup without hysteresis (current_speed=None)."""
        assert ArgonOneFan._compute_speed(PRESET_SILENT, temp) == expected

    @pytest.mark.parametrize(
        ("temp", "expected"),
        [
            (100, 100),
            (75, 100),
            (74, 75),
            (70, 75),
            (69, 50),
            (65, 50),
            (64, 25),
            (58, 25),
            (57, 10),
            (50, 10),
            (49, 0),
            (0, 0),
        ],
    )
    def test_current_speed_none(self, temp: float, expected: int) -> None:
        """current_speed=None means no hysteresis, direct curve lookup."""
        assert ArgonOneFan._compute_speed(PRESET_SILENT, temp, None) == expected


class TestComputeSpeedDefault:
    """Tests for the Default preset curve."""

    # Default: [(75, 100), (70, 80), (65, 60), (60, 40), (55, 25), (50, 10), (0, 0)]

    @pytest.mark.parametrize(
        ("temp", "expected"),
        [
            (100, 100),
            (75, 100),
            (70, 80),
            (65, 60),
            (60, 40),
            (55, 25),
            (50, 10),
            (49, 0),
            (0, 0),
        ],
    )
    def test_no_hysteresis(self, temp: float, expected: int) -> None:
        """Test speed lookup without hysteresis."""
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, temp) == expected


class TestComputeSpeedPerformance:
    """Tests for the Performance preset curve."""

    # Performance: [(72, 100), (67, 80), (62, 60), (57, 40), (52, 25), (47, 10), (0, 0)]

    @pytest.mark.parametrize(
        ("temp", "expected"),
        [
            (100, 100),
            (72, 100),
            (67, 80),
            (62, 60),
            (57, 40),
            (52, 25),
            (47, 10),
            (46, 0),
            (0, 0),
        ],
    )
    def test_no_hysteresis(self, temp: float, expected: int) -> None:
        """Test speed lookup without hysteresis."""
        assert ArgonOneFan._compute_speed(PRESET_PERFORMANCE, temp) == expected


class TestHysteresis:
    """Tests for hysteresis behavior when temperature drops."""

    # Default curve: [(75, 100), (70, 80), (65, 60), (60, 40), (55, 25), (50, 10), (0, 0)]
    # HYSTERESIS_CELSIUS = 2.0

    def test_increase_no_hold(self) -> None:
        """When new_speed >= current_speed, return new_speed immediately."""
        # At 70°C with current_speed=60, new_speed=80 >= 60 → return 80
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 70, 60) == 80

    def test_hold_within_hysteresis(self) -> None:
        """Temp drops within hysteresis band → hold current speed."""
        # current_speed=60, threshold=65, hold_until=63
        # temp=64 >= 63 → hold at 60
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 64, 60) == 60

    def test_hold_at_exact_boundary(self) -> None:
        """Temp at exact hysteresis boundary → still hold."""
        # current_speed=60, threshold=65, hold_until=63.0
        # temp=63.0 >= 63.0 → hold
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 63.0, 60) == 60

    def test_decrease_below_hysteresis(self) -> None:
        """Temp drops below hysteresis band → decrease speed."""
        # current_speed=60, threshold=65, hold_until=63
        # temp=62.9 < 63 → decrease to 40 (next step for 62.9°C)
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 62.9, 60) == 40

    def test_hold_at_threshold(self) -> None:
        """Temp at threshold → new_speed equals current, returned directly."""
        # At 65°C, new_speed=60, current_speed=60, new_speed >= current → return 60
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 65, 60) == 60

    def test_speed_not_in_curve_fallback(self) -> None:
        """When current_speed is not in the curve, fall back to new_speed."""
        # current_speed=45 is not in default curve → fallback to new_speed
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 62, 45) == 40

    def test_hold_top_speed(self) -> None:
        """At top speed 100, hold within hysteresis."""
        # current_speed=100, threshold=75, hold_until=73
        # temp=74 >= 73 → hold at 100
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 74, 100) == 100

    def test_decrease_from_top(self) -> None:
        """Drop from top speed when below hysteresis."""
        # current_speed=100, threshold=75, hold_until=73
        # temp=72.5 < 73 → decrease to 80
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 72.5, 100) == 80

    def test_hold_lowest_nonzero(self) -> None:
        """Hold lowest nonzero speed within hysteresis."""
        # current_speed=10, threshold=50, hold_until=48
        # temp=49 >= 48 → hold at 10
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 49, 10) == 10

    def test_decrease_from_lowest_nonzero(self) -> None:
        """Drop from lowest nonzero when below hysteresis."""
        # current_speed=10, threshold=50, hold_until=48
        # temp=47 < 48 → decrease to 0
        assert ArgonOneFan._compute_speed(PRESET_DEFAULT, 47, 10) == 0
