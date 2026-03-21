# Argon ONE — Home Assistant Integration

Custom integration for [Argon ONE](https://argon40.com/) Raspberry Pi cases. Controls the built-in fan and power mode via I2C.

## Supported Cases

| Case | Raspberry Pi | Fan Control | Always ON Mode | Tested |
|---|---|---|---|---|
| Argon ONE V1/V2 (Classic) | Pi 3 / Pi 4 | ✅ | ✅ (via I2C) | ❌ [Help wanted](https://github.com/fix-parrot/argon-one/issues) |
| Argon ONE V3 | Pi 5 | ✅ | ❌ (hardware jumper) | ✅ |
| Argon ONE V5 | Pi 5 | ✅ | ❌ (hardware jumper) | ❌ [Help wanted](https://github.com/fix-parrot/argon-one/issues) |

> **Note:** The integration has only been tested on **Argon ONE V3 with Raspberry Pi 5**. If you have a Classic (V1/V2) case or an Argon ONE V5, please check the [open issues](https://github.com/fix-parrot/argon-one/issues) — your help with testing is very welcome!

## Prerequisites

**Enable I2C** on your Raspberry Pi before installing the integration. This is the most important step — disabled I2C will prevent the integration from working.

### Home Assistant OS

**Recommended:** Install the [HassOS I2C Configurator](https://community.home-assistant.io/t/add-on-hassos-i2c-configurator/264167) add-on and click **Start**. The add-on will automatically enable I2C and reboot your system.

**Alternative:** Follow the [official Home Assistant documentation](https://www.home-assistant.io/common-tasks/os) for manual I2C configuration.

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

Copy the `custom_components/argon_one` folder to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Argon ONE**
3. Select your case type (Classic or Pi 5)
4. Done!

## Entities

The integration creates the following entities under a single **Argon ONE** device:

| Entity | Entity ID | Case Types | Description |
|---|---|---|---|
| Fan | `fan.argon_one_fan` | All | Fan speed control 0–100% |
| Switch | `switch.argon_one_always_on` | Classic only | Power mode: Always ON / Default |

- **Fan** — controls the case fan speed as a percentage (0–100%). Turning on
  without specifying speed sets 10% (minimum working speed). The fan physically
  does not spin below ~10%.
- **Switch** (Classic only) — toggles the power mode. **ON** = Always ON
  (Pi starts automatically when power is applied). **OFF** = Default (button
  press required). Not available on Pi 5 cases — use the hardware jumper instead.

## Services

The integration uses standard Home Assistant services (no custom services):

| Service | Description |
|---|---|
| `fan.turn_on` | Turn on the fan (default 10% if no speed specified) |
| `fan.turn_off` | Turn off the fan |
| `fan.set_percentage` | Set fan speed 0–100% |
| `switch.turn_on` | Enable Always ON mode (Classic only) |
| `switch.turn_off` | Set Default power mode (Classic only) |

## Automation Examples

### Silent Profile — temperature-based fan control

```yaml
automation:
  - alias: "Argon ONE Fan - Silent Profile"
    trigger:
      - platform: state
        entity_id: sensor.system_monitor_processor_temperature
    action:
      - service: fan.set_percentage
        target:
          entity_id: fan.argon_one_fan
        data:
          percentage: >
            {% set temp = states('sensor.system_monitor_processor_temperature') | float %}
            {% if temp < 40 %} 0
            {% elif temp < 50 %} 10
            {% elif temp < 60 %} 25
            {% elif temp < 70 %} 50
            {% else %} 100
            {% endif %}
```

### Always ON mode

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
