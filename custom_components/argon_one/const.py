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
