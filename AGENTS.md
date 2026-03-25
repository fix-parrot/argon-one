# AGENTS.md

## Project Overview

Custom Home Assistant integration for **Argon ONE** Raspberry Pi cases.
Controls the built-in fan (speed 0–100%) and power mode (Always ON / Default)
via I2C bus. Supports both Classic cases (Pi 3/4) and V3/V5 cases (Pi 5) with
different I2C protocols.

Fan preset modes (Silent, Default, Performance) provide automatic
temperature-based speed control with hysteresis when a temperature sensor is
configured via the options flow.

Installed via HACS as a custom integration. Configured through the HA UI
(config flow + options flow). No YAML configuration.

## Technical Context

- **Language/Version**: Python 3.13.2+
- **Primary Dependencies**: `homeassistant==2026.1.1` (core),
  `smbus2==0.6.0` (I2C), `voluptuous` (config/options flow validation,
  transitive via HA)
- **Package Manager**: `uv` — dependencies in `pyproject.toml`, locked in
  `uv.lock`, virtual env in `.venv`
- **Storage**: Home Assistant config entries and options (managed by HA Core)
- **Testing**: `pytest` + `pytest-homeassistant-custom-component==0.13.306`
  (84 tests, 92% coverage)
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
├── .devcontainer/
│   └── devcontainer.json        # VS Code devcontainer config (HA dev env)
├── .github/
│   ├── ISSUE_TEMPLATE/          # Bug report, feature request & testing templates
│   ├── scripts/
│   │   ├── build-release-zip    # Build zip archive from custom_components/
│   │   ├── bump-version         # Bump version in pyproject.toml, manifest, CHANGELOG
│   │   └── extract-changelog    # Extract release notes for a given version
│   ├── dependabot.yml           # Dependabot config for deps updates
│   └── workflows/
│       ├── bump.yml             # Version bump workflow (workflow_dispatch)
│       ├── lint.yml             # Ruff + mypy CI
│       ├── release.yml          # Build zip + GitHub Release on tag push
│       ├── tag.yml              # Auto-tag + release on merged bump PR
│       ├── test.yml             # Pytest + coverage CI
│       └── validate.yml         # Hassfest + HACS validation CI
├── config/
│   └── configuration.yaml       # HA dev config (mock temp sensor + debug logging)
├── custom_components/argon_one/ # HA custom integration package
│   ├── __init__.py              # Entry point: async_setup_entry / async_unload_entry
│   ├── config_flow.py           # Config flow + options flow (case type, temp sensor)
│   ├── const.py                 # Constants: I2C, case types, preset curves
│   ├── fan.py                   # FanEntity: speed control, preset modes, sensor tracking
│   ├── switch.py                # SwitchEntity: Always ON mode (Classic only)
│   ├── manifest.json            # Integration metadata
│   └── translations/
│       └── en.json              # English strings for config & options flows
├── testing/
│   └── mock_smbus2/
│       └── smbus2.py            # Fake SMBus for devcontainer (logs I2C calls)
├── tests/
│   ├── conftest.py              # Shared fixtures (mock_smbus, config entries)
│   ├── test_compute_speed.py    # Unit tests for _compute_speed + hysteresis
│   ├── test_config_flow.py      # Config flow tests (success, errors, abort)
│   ├── test_options_flow.py     # Options flow tests (set/clear sensor)
│   ├── test_fan.py              # Fan entity tests (speed, presets, I2C, sensor)
│   ├── test_switch.py           # Switch entity tests (on/off, I2C errors)
│   └── test_init.py             # Platform loading + unload tests
├── scripts/
│   ├── deploy                   # Automated deployment to HA instances
│   ├── develop                  # Start HA in dev mode (mock I2C)
│   ├── lint                     # Run ruff format + check via uv
│   ├── setup                    # uv sync
│   └── test                     # Run pytest with coverage via uv
├── .pre-commit-config.yaml      # Pre-commit hooks (ruff + mypy)
├── .ruff.toml                   # Ruff linter/formatter config
├── mypy.ini                     # Mypy type checker config
├── pyproject.toml               # Project metadata + dependencies
├── uv.lock                      # Locked dependency versions
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

- **Install for development**: `uv sync` (creates `.venv` with all deps)
- **Run tests**: `scripts/test` (runs `uv run pytest tests/ --cov`)
- **Lint**: `scripts/lint` (runs `uv run ruff format .` + `uv run ruff check . --fix`)
- **Type check**: `uv run mypy custom_components/argon_one/`
- **Format**: `uv run ruff format .`
- **Dev server**: `scripts/develop` (starts HA with mock I2C)
- **Deploy**: `scripts/deploy` (automated deployment to HA instances)
- **Validate manifest**: `python -m script.hassfest --integration-path custom_components/argon_one`
  (requires HA Core dev environment)
- **HACS validation**: `gh workflow run validate.yml` (or auto on push/PR to main)
- **Bump version**: `gh workflow run bump.yml -f bump_type=patch` (creates PR)
- **Release (manual tag)**: `git tag -a vX.Y.Z -m "Release vX.Y.Z" && git push origin vX.Y.Z`

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
8. **Error handling** — on I2C `OSError`, set `_attr_available = False` and
   call `self.async_write_ha_state()`. Restore on next successful operation.
9. **Options flow with reload** — `ArgonOneOptionsFlow` extends
   `OptionsFlowWithReload`. Changing the temperature sensor causes full
   platform reload; fan reads sensor entity from `entry.options` at init.
10. **Preset modes require a temperature sensor** — `FanEntityFeature.PRESET_MODE`
    is only added when `entry.options[CONF_TEMP_SENSOR]` is set. Without a
    sensor, presets are unavailable.
11. **Temperature curves and hysteresis** — preset curves are defined in
    `const.py` → `PRESET_CURVES`. Speed decreases only when temperature drops
    below (threshold − `HYSTERESIS_CELSIUS`), preventing fan oscillation.
12. **Keep it simple** — project principle is to avoid over-engineering.
    No GPIO button handling, no complex abstractions.

## Code Guidelines

### Architecture

- **Platform pattern**: `__init__.py` opens the I2C bus, stores it in
  `entry.runtime_data`, and forwards setup to platform modules (`fan.py`,
  `switch.py`). Each platform creates its entity from the config entry.
- **No coordinator**: State is `assumed_state` (write-only device). No polling
  or data coordinator needed.
- **DeviceInfo**: Defined inline in each entity's `__init__` with shared
  `identifiers` so HA groups entities under one device.
- **Sensor tracking**: When a preset mode is active, `fan.py` subscribes to
  temperature sensor state changes via `async_track_state_change_event` and
  unsubscribes on preset clear or entity removal.
- **Config flow + options flow**: `config_flow.py` contains both
  `ArgonOneConfigFlow` (case type selection, I2C validation) and
  `ArgonOneOptionsFlow` (temperature sensor selection for presets).

### Code Quality

- **Type hints**: All function signatures use type annotations. Use
  `from __future__ import annotations` in every module.
- **Logging**: Use `_LOGGER = logging.getLogger(__name__)` per module.
  Log I2C errors at `error` level, diagnostics at `warning`/`debug`.
- **Constants**: All magic numbers go in `const.py`. No inline hex values
  in business logic. Temperature curves are data-driven via `PRESET_CURVES`.
- **HA entity pattern**: Use `_attr_*` class attributes for static properties;
  use `@property` for dynamic state (`is_on`, `percentage`, `preset_mode`).
- **Pure logic as static methods**: `_compute_speed` is a `@staticmethod` —
  easy to test without HA runtime.

### CI/CD Security (GitHub Actions)

- **No `${{ }}` in `run:` for untrusted data**: Never interpolate GitHub
  context expressions (`github.event.pull_request.title`, `.body`, etc.)
  directly in `run:` blocks — this is a shell injection vector. Pass through
  `env:` instead and use `"$VAR"` in the script.
- **Validated outputs are safe**: Step outputs that passed regex validation
  (e.g., `^[0-9]+\.[0-9]+\.[0-9]+$`) contain only safe characters and may
  be used via `${{ }}` in `run:` blocks.
- **`type: choice` for workflow inputs**: Always use `type: choice` (not
  `type: string`) for `workflow_dispatch` inputs used in shell commands.
- **Double-quote all shell variables**: Always `"$VAR"`, never `$VAR`.
- **Least privilege permissions**: Each workflow declares only the permissions
  it needs. CI workflows (`lint.yml`, `test.yml`, `validate.yml`) use
  `permissions: {}`. Release workflows declare `contents: write` only where
  required.
- **No `pull_request_target`**: Tag workflow uses `pull_request` trigger
  (not `pull_request_target`) to avoid running untrusted PR code with write
  token.
- **Version source**: Tag workflow extracts version from `manifest.json` on
  the merged branch, never from PR title or other user-controlled fields.
- **CI scripts in `.github/scripts/`**: Reusable shell scripts called from
  workflows. Scripts must never accept unfiltered user-controlled input
  (PR title, body, etc.) as positional arguments — pass such data only via
  env variables with double-quoting. All scripts use `set -euo pipefail`.

### Testing

- **Framework**: `pytest` + `pytest-homeassistant-custom-component`
- **Coverage**: 92% (84 tests)
- **Mock strategy**: `conftest.py` patches `custom_components.argon_one.SMBus`
  and `smbus2.SMBus` via a `mock_smbus` fixture
- **Test files**:
  - `test_compute_speed.py` — `_compute_speed` with all curves and hysteresis
  - `test_config_flow.py` — success, I2C errors, single_instance_allowed
  - `test_options_flow.py` — set/clear temperature sensor
  - `test_fan.py` — speed control, presets, sensor tracking, I2C errors
  - `test_switch.py` — on/off, I2C errors, recovery
  - `test_init.py` — platform loading (Classic vs Pi 5), unload
