# AGENTS.md

## Project Overview

Custom Home Assistant integration for **Argon ONE** Raspberry Pi cases.
Controls the built-in fan (speed 0–100%) and power mode (Always ON / Default)
via I2C bus. Supports both Classic cases (Pi 3/4) and V3/V5 cases (Pi 5) with
different I2C protocols.

Installed via HACS as a custom integration. Configured through the HA UI
(config flow). No YAML configuration.

## Technical Context

- **Language/Version**: Python 3.12+
- **Primary Dependencies**: `homeassistant` (core), `smbus2==0.6.0` (I2C),
  `voluptuous` (config flow validation, transitive via HA)
- **Storage**: Home Assistant config entries (managed by HA Core)
- **Testing**: N/A (no test suite yet; target framework: `pytest` +
  `pytest-homeassistant-custom-component`)
- **Target Platform**: Home Assistant OS on Raspberry Pi 3/4/5
- **Project Type**: single — custom HA integration, installed via HACS
- **Min HA Version**: 2026.1
- **IoT Class**: `assumed_state` (no read-back from device)
- **Performance Goals**: I2C command < 100 ms, never blocks the event loop
- **Constraints**: All I2C ops are blocking → must use
  `hass.async_add_executor_job`; I2C must be enabled by user before install
- **Scale/Scope**: Single user, single device, minimal I2C traffic

## Project Structure

```text
.
├── .devcontainer.json           # VS Code devcontainer config (HA dev env)
├── .gitattributes               # Git line-ending and diff settings
├── .github/
│   ├── ISSUE_TEMPLATE/          # Bug report & feature request templates
│   ├── dependabot.yml           # Dependabot config for deps updates
│   └── workflows/
│       ├── lint.yml             # Ruff lint & format CI
│       └── validate.yml         # Hassfest + HACS validation CI
├── config/
│   └── configuration.yaml       # HA dev config (devcontainer)
├── custom_components/argon_one/ # HA custom integration package
│   ├── __init__.py              # Entry point: async_setup_entry / async_unload_entry
│   ├── config_flow.py           # UI config flow: case type selection, I2C check
│   ├── const.py                 # Constants: domain, I2C addresses, case types
│   ├── fan.py                   # FanEntity: speed control via I2C
│   ├── switch.py                # SwitchEntity: Always ON mode (Classic only)
│   ├── manifest.json            # Integration metadata
│   └── translations/
│       └── en.json              # English strings for config flow
├── scripts/
│   ├── develop                  # Start HA in dev mode
│   ├── lint                     # Run ruff format + check
│   └── setup                    # Install Python deps
├── .ruff.toml                   # Ruff linter/formatter config
├── requirements.txt             # Dev dependencies
├── hacs.json                    # HACS repository metadata
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Project changelog
├── DEVELOPMENT.md               # Development guide
├── README.md                    # User-facing documentation
├── LICENSE                      # MIT license
└── AGENTS.md                    # This file
```

## Build And Test Commands

This is a Home Assistant custom integration — there is no standalone build
step. The integration is loaded by HA at runtime.

- **Install for development**: Copy `custom_components/argon_one/` into HA's
  `config/custom_components/` directory and restart HA
- **Validate manifest**: `python -m script.hassfest --integration-path custom_components/argon_one`
  (requires HA Core dev environment)
- **HACS validation**: `gh workflow run validate.yml` (or auto on push/PR to main)
- **Run tests**: N/A (no test suite yet)
- **Lint**: `scripts/lint` (runs `ruff format .` + `ruff check . --fix`)
- **Format**: `ruff format .`
- **Dev server**: `scripts/develop` (starts HA with devcontainer config)

## Contribution Instructions

1. **Single integration, single config entry** — the integration supports only
   one Argon ONE case per HA instance (`single_config_entry: true` in manifest).
2. **All I2C operations in executor** — never call `SMBus` methods directly
   from async code. Always use `await hass.async_add_executor_job(...)`.
3. **Two I2C protocols** — Classic (Pi 3/4) uses `write_byte(0x1A, value)`;
   Pi 5 (V3/V5) uses `write_byte_data(0x1A, 0x80, value)`. Dispatch is in
   `fan.py` → `_async_send_speed`.
4. **Switch only for Classic** — `switch.py` (Always ON) is loaded only when
   `case_type == "classic"`. Platform list is controlled in `__init__.py`.
5. **No `strings.json`** — custom integrations use `translations/en.json`
   directly, not `strings.json` (that's for core integrations only).
6. **Use standard HA services** — no custom services. Fan control via
   `fan.set_percentage` / `fan.turn_on` / `fan.turn_off`; power mode via
   `switch.turn_on` / `switch.turn_off`.
7. **Typed config entry** — use `ArgonOneConfigEntry` (defined in `__init__.py`)
   which is `ConfigEntry[SMBus]`. Access the bus via `entry.runtime_data`.
8. **Error handling** — on I2C `IOError`, set `_attr_available = False` and
   call `self.async_write_ha_state()`. Restore on next successful operation.
9. **Keep it simple** — project principle is to avoid over-engineering.
   No GPIO button handling, no preset modes (yet), no complex abstractions.

## Code Guidelines

### Architecture

- **Platform pattern**: `__init__.py` opens the I2C bus, stores it in
  `entry.runtime_data`, and forwards setup to platform modules (`fan.py`,
  `switch.py`). Each platform creates its entity from the config entry.
- **No coordinator**: State is `assumed_state` (write-only device). No polling
  or data coordinator needed.
- **DeviceInfo**: Defined inline in each entity's `__init__` with shared
  `identifiers` so HA groups entities under one device.

### Code Quality

- **Type hints**: All function signatures use type annotations. Use
  `from __future__ import annotations` in every module.
- **Logging**: Use `_LOGGER = logging.getLogger(__name__)` per module.
  Log I2C errors at `error` level, diagnostics at `warning`/`debug`.
- **Constants**: All magic numbers go in `const.py`. No inline hex values
  in business logic.
- **HA entity pattern**: Use `_attr_*` class attributes for static properties;
  use `@property` for dynamic state (`is_on`, `percentage`).

### Testing

- No test suite exists yet. When adding tests:
  - Use `pytest-homeassistant-custom-component`
  - Mock `smbus2.SMBus` for all I2C operations
  - Test config flow (success, I2C unavailable, I2C device not found,
    already configured)
  - Test fan entity (set speed, turn on/off, I2C error → unavailable)
  - Test switch entity (turn on/off, I2C error → unavailable)
  - Test platform loading (Classic → fan + switch; Pi 5 → fan only)
