"""Constants for the Argon ONE integration."""

DOMAIN = "argon_one"

I2C_ADDRESS = 0x1A
I2C_BUS_NUMBER = 1  # GPIO I2C bus on all supported Pi models (3/4/5)

# Case types
CASE_TYPE_CLASSIC = "classic"
CASE_TYPE_PI5 = "pi5"
CASE_TYPES = {
    CASE_TYPE_CLASSIC: "Argon ONE Classic (Pi 3/4)",
    CASE_TYPE_PI5: "Argon ONE V3/V5 (Pi 5)",
}

# I2C protocol — Pi 5
PI5_FAN_REGISTER = 0x80

# I2C protocol — Classic power commands
CMD_POWER_DEFAULT = 0xFD
CMD_POWER_ALWAYS_ON = 0xFE

# Config entry keys
CONF_CASE_TYPE = "case_type"

# Fan defaults
DEFAULT_FAN_SPEED = 10
HYSTERESIS_CELSIUS = 2.0

# Options keys
CONF_TEMP_SENSOR = "temperature_sensor"

# Fan preset modes
PRESET_SILENT = "silent"
PRESET_DEFAULT = "default"
PRESET_PERFORMANCE = "performance"

PRESET_MODES = [PRESET_SILENT, PRESET_DEFAULT, PRESET_PERFORMANCE]

# Temperature curves: list of (threshold_celsius, fan_speed_percent)
# Evaluated top-down; first matching threshold (temp >= threshold) wins.
# Must be sorted descending by threshold.
PRESET_CURVES: dict[str, list[tuple[int, int]]] = {
    PRESET_SILENT:      [(75, 100), (70, 75), (65, 50), (58, 25), (50, 10), (0, 0)],
    PRESET_DEFAULT:     [(75, 100), (70, 80), (65, 60), (60, 40), (55, 25), (50, 10), (0, 0)],  # noqa: E501
    PRESET_PERFORMANCE: [(72, 100), (67, 80), (62, 60), (57, 40), (52, 25), (47, 10), (0, 0)],  # noqa: E501
}
