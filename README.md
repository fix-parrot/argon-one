# Argon ONE — Home Assistant Integration

Custom integration for [Argon ONE](https://argon40.com/) Raspberry Pi cases.
Controls the built-in fan (speed 0–100%) and power mode via I2C bus. Supports
automatic temperature-based fan control with preset modes (Silent, Default,
Performance).

## Supported Cases

| Case | Raspberry Pi | Fan Control | Always ON Mode | Tested |
|---|---|---|---|---|
| Argon ONE V1 (Classic) | Pi 3 | ✅ | ✅ (via I2C) | ❌ [Help wanted](https://github.com/fix-parrot/argon-one/issues) |
| Argon ONE V2 (Classic) | Pi 4 | ✅ | ✅ (via I2C) | ❌ [Help wanted](https://github.com/fix-parrot/argon-one/issues) |
| Argon ONE V3 | Pi 5 | ✅ | ❌ (hardware jumper) | ✅ |
| Argon ONE V5 | Pi 5 | ✅ | ❌ (hardware jumper) | ❌ [Help wanted](https://github.com/fix-parrot/argon-one/issues) |

> **Note:** The integration has only been tested on **Argon ONE V3 with
> Raspberry Pi 5**. If you have a Classic (V1/V2) case or an Argon ONE V5,
> please check the [open issues](https://github.com/fix-parrot/argon-one/issues)
> — your help with testing is very welcome!

## Key Concepts

- **Fan speed** — direct percentage control (0–100%) of the case fan via I2C.
  The fan physically does not spin below ~10%.
- **Preset modes** — automatic temperature-based speed profiles (Silent,
  Default, Performance). The fan adjusts speed in real time based on a
  temperature sensor you configure. Requires a temperature sensor entity in
  Home Assistant (e.g., `sensor.system_monitor_processor_temperature`).
- **Hysteresis** — when a preset is active, the fan speed only decreases when
  the temperature drops 2 °C below the threshold, preventing rapid on/off
  cycling.
- **Always ON mode** (Classic cases only) — controls the power behavior: when
  enabled, the Pi starts automatically when power is applied; when disabled, a
  button press is required. Pi 5 cases use a hardware jumper for this.
- **I2C** — the communication bus between the Pi and the Argon ONE board. Must
  be enabled before installing the integration.

## Prerequisites

**Enable I2C** on your Raspberry Pi before installing the integration. Disabled
I2C will prevent the integration from working.

### Home Assistant OS

**Recommended:** Install the [HassOS I2C Configurator](https://community.home-assistant.io/t/add-on-hassos-i2c-configurator/264167)
add-on and click **Start**. The add-on will automatically enable I2C and
reboot your system.

**Alternative:** Follow the [official Home Assistant documentation](https://www.home-assistant.io/common-tasks/os)
for manual I2C configuration.

After enabling I2C, verify it's available:

```bash
ls /dev/i2c-1
```

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click **Integrations** → **⋮** → **Custom repositories**
3. Add `https://github.com/fix-parrot/argon-one` as **Integration**
4. Search for **Argon ONE** and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/argon_one` folder to your Home Assistant
`config/custom_components/` directory and restart.

## Configuration

### Initial setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Argon ONE**
3. Select your case type (Classic or Pi 5)
4. The integration validates the I2C connection and creates the device

### Temperature sensor (optional)

To enable preset modes, configure a temperature sensor:

1. Go to **Settings** → **Devices & Services** → **Argon ONE** → **Configure**
2. Select a temperature sensor entity
   (e.g., `sensor.system_monitor_processor_temperature`)
3. Save — the integration reloads and preset modes become available on the fan

To disable presets, clear the sensor field and save.

## Entities

The integration creates entities under a single **Argon ONE** device:

| Entity | Entity ID | Case Types | Description |
|---|---|---|---|
| Fan | `fan.argon_one_fan` | All | Fan speed control 0–100% and preset modes |
| Switch | `switch.argon_one_always_on` | Classic only | Power mode: Always ON / Default |

### Fan

Controls the case fan speed as a percentage (0–100%). Turning on without
specifying speed sets 10% (minimum working speed).

When a temperature sensor is configured, the fan supports three preset modes:

| Preset | Description |
|---|---|
| **Silent** | Fan stays off until 50 °C, ramps gradually, 100% at 75 °C |
| **Default** | Balanced curve — starts at 50 °C, wider speed range |
| **Performance** | Aggressive cooling — starts at 47 °C with higher speeds at each step |

Selecting a preset activates automatic control: the fan speed adjusts in real
time as temperature changes. Setting a manual speed or turning the fan off
clears the active preset.

### Switch (Classic only)

Toggles the power mode:

- **ON** = Always ON (Pi starts automatically when power is applied)
- **OFF** = Default (button press required to start)

Not available on Pi 5 cases — use the hardware jumper instead.

## Services

The integration uses standard Home Assistant services (no custom services):

| Service | Description |
|---|---|
| `fan.turn_on` | Turn on the fan (default 10%, or specify speed/preset) |
| `fan.turn_off` | Turn off the fan (clears active preset) |
| `fan.set_percentage` | Set fan speed 0–100% (clears active preset) |
| `fan.set_preset_mode` | Activate a preset (silent, default, performance) |
| `switch.turn_on` | Enable Always ON mode (Classic only) |
| `switch.turn_off` | Set Default power mode (Classic only) |

## Usage Examples

### Activate a preset mode

```yaml
service: fan.set_preset_mode
target:
  entity_id: fan.argon_one_fan
data:
  preset_mode: silent
```

### Set manual speed

```yaml
service: fan.set_percentage
target:
  entity_id: fan.argon_one_fan
data:
  percentage: 50
```

### Enable Always ON on startup (Classic only)

```yaml
automation:
  - alias: "Enable Always ON on startup"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.argon_one_always_on
```

## Documentation

- [Development guide](DEVELOPMENT.md) — setup, workflow, troubleshooting
- [Contributing](CONTRIBUTING.md) — how to report bugs and submit changes
- [Changelog](CHANGELOG.md) — version history
- [LLM agent rules](AGENTS.md) — code guidelines for AI-assisted development

## License

MIT
