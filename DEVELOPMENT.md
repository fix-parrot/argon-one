# Development Guide

## Prerequisites

- **Python**: 3.13.2+
- **Git**
- **[uv](https://docs.astral.sh/uv/)** — package manager and virtual
  environment tool
- **Docker** (recommended) — for the VS Code devcontainer workflow
- **Hardware** (for on-device testing): Raspberry Pi 3/4/5 with an Argon ONE
  case and I2C enabled (`/dev/i2c-1`)

The integration has no standalone build step — it is loaded by Home Assistant
at runtime. Dependencies are managed via `pyproject.toml` and `uv.lock`.

## Getting Started

### Option A: Devcontainer (recommended)

The repository includes a devcontainer that provides a complete HA development
environment with all dependencies pre-installed.

1. **Clone the repository**

   ```bash
   git clone https://github.com/fix-parrot/argon-one.git
   cd argon-one
   ```

2. **Open in VS Code** and select **Reopen in Container** when prompted (or run
   `Dev Containers: Reopen in Container` from the command palette). The
   container image is `mcr.microsoft.com/devcontainers/python:3.13`.

3. **Wait for setup** — the `scripts/setup` post-create command runs
   `uv sync` to install all dependencies into `.venv` automatically.

4. **Start Home Assistant**

   ```bash
   scripts/develop
   ```

   This starts HA in debug mode on port **8123** using `config/configuration.yaml`.
   The script prepends `testing/mock_smbus2/` and `custom_components/` to
   `PYTHONPATH`, so the integration loads with a fake I2C module.

5. **Add the integration** — open `http://localhost:8123`, go to Settings →
   Devices & Services → Add Integration → search **Argon ONE** → select case
   type.

6. **Test preset modes** — the dev config includes a mock temperature sensor
   (`sensor.mock_temperature`) backed by `input_number.mock_temperature`. Use
   the slider in the UI to change temperature and observe fan speed changes.

> **Note:** I2C hardware is not available inside the container. The
> `testing/mock_smbus2/` module provides a fake `SMBus` that logs all I2C
> calls instead of performing real I/O.

### Option B: Manual setup on Raspberry Pi

Use this when you need to test against real hardware.

1. **Clone the repository**

   ```bash
   git clone https://github.com/fix-parrot/argon-one.git
   cd argon-one
   ```

2. **Copy the integration** into your HA config directory:

   ```bash
   cp -r custom_components/argon_one /path/to/ha-config/custom_components/argon_one
   ```

   On HAOS the config directory is `/config/`. Via the
   [SSH & Web Terminal](https://github.com/hassio-addons/addon-ssh) add-on:

   ```bash
   cp -r custom_components/argon_one /config/custom_components/argon_one
   ```

3. **Restart Home Assistant**
   - **UI**: Settings → System → Restart
   - **CLI**: `ha core restart`

4. **Add the integration** — Settings → Devices & Services → Add Integration →
   search **Argon ONE** → select case type (Classic or Pi 5).

### Option C: Automated deployment

Deploy the integration to a remote Home Assistant instance via SSH:

```bash
./scripts/deploy                                  # default: root@homeassistant.local:2222
./scripts/deploy root@192.168.1.100:2222          # custom host/port
./scripts/deploy pi@ha.local                      # port defaults to 22
```

The script packs `custom_components/argon_one` with `tar`, uploads it over SSH,
and unpacks into `/config/custom_components/` on the target.

**Requirements:**
- SSH key authentication configured for the target host

## Environment Configuration

### Dev HA config

The devcontainer uses `config/configuration.yaml` with debug logging enabled
for the integration:

```yaml
logger:
  default: info
  logs:
    custom_components.argon_one: debug
```

### VS Code extensions (devcontainer)

Installed automatically inside the container:

- **charliermarsh.ruff** — Ruff linter/formatter
- **ms-python.python** + **ms-python.vscode-pylance** — Python support
- **ryanluker.vscode-coverage-gutters** — test coverage display
- **github.vscode-pull-request-github** — PR workflow

Python formatting on save is enabled by default (`editor.formatOnSave: true`).

### Dependencies

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

**Runtime:**

| Package | Version | Purpose |
|---|---|---|
| `homeassistant` | 2026.1.1 | HA Core (runtime) |
| `smbus2` | 0.6.0 | I2C communication |
| `colorlog` | 6.10.1 | HA logging dependency |

**Dev (dependency group `dev`):**

| Package | Purpose |
|---|---|
| `pytest` + `pytest-homeassistant-custom-component` | Test framework |
| `pytest-cov` + `pytest-asyncio` | Coverage and async support |
| `mypy` | Static type checking |
| `ruff` | Linter and formatter |
| `pre-commit` | Git hooks |

Install manually (outside devcontainer):

```bash
uv sync
```

## Project Structure

See [AGENTS.md → Project Structure](AGENTS.md#project-structure) for the full
directory tree and file descriptions.

Key files for development:

| File | Purpose |
|---|---|
| `custom_components/argon_one/__init__.py` | Entry point: opens I2C bus, forwards platform setup |
| `custom_components/argon_one/config_flow.py` | UI config flow: case type selection, I2C validation |
| `custom_components/argon_one/const.py` | All constants (domain, I2C addresses, case types) |
| `custom_components/argon_one/fan.py` | `FanEntity` — fan speed control via I2C |
| `custom_components/argon_one/switch.py` | `SwitchEntity` — Always ON mode (Classic only) |
| `custom_components/argon_one/manifest.json` | Integration metadata, dependencies, version |
| `custom_components/argon_one/translations/en.json` | English strings for config flow UI |

## Development Workflow

### Making changes

1. Edit files in `custom_components/argon_one/`
2. Restart Home Assistant to reload the integration

There is no hot-reload for custom integrations — a full HA restart is required
after every code change. In the devcontainer, stop `scripts/develop` with
`Ctrl+C` and re-run it.

### Linting and formatting

The project uses [Ruff](https://docs.astral.sh/ruff/) (v0.15.7) configured in
`.ruff.toml`. The rule set is `ALL` (all available rules) with a few
formatter-incompatible rules disabled.

Run locally:

```bash
scripts/lint
```

This executes `uv run ruff format .` followed by `uv run ruff check . --fix`.

To check without auto-fixing (same as CI):

```bash
uv run ruff check .
uv run ruff format . --check
```

### Type checking

The project uses [mypy](https://mypy-lang.org/) configured in `mypy.ini`.

```bash
uv run mypy custom_components/argon_one/
```

### Validating the manifest

If you have a [Home Assistant Core dev environment](https://developers.home-assistant.io/docs/development_environment)
set up:

```bash
python -m script.hassfest --integration-path custom_components/argon_one
```

This checks `manifest.json`, `translations/en.json`, and config flow
consistency. This validation also runs automatically in CI (see below).

### Running tests

The test suite uses `pytest` with `pytest-homeassistant-custom-component`.

```bash
scripts/test
```

This runs `uv run pytest tests/ --cov=custom_components/argon_one --cov-report=term-missing`.

Run a specific test file or test:

```bash
uv run pytest tests/test_fan.py -v
uv run pytest tests/test_fan.py::test_set_percentage -v
```

See [AGENTS.md → Testing](AGENTS.md#testing) for test guidelines and coverage.

### Pre-commit hooks

The project includes a `.pre-commit-config.yaml` with ruff and mypy hooks.

```bash
uv run pre-commit install          # one-time setup
uv run pre-commit run --all-files  # manual run
```

### Version bumping

The canonical version lives in `custom_components/argon_one/manifest.json` →
`"version"` field. HACS reads this file directly; `hacs.json` does not contain
a separate version.

Update the version and document changes in `CHANGELOG.md`.

## CI Pipelines

Three GitHub Actions workflows run automatically on pushes and PRs to `main`:

| Workflow | File | What it checks |
|---|---|---|
| **Lint** | `.github/workflows/lint.yml` | `ruff check .`, `ruff format . --check`, `mypy` |
| **Test** | `.github/workflows/test.yml` | `pytest` with coverage |
| **Validate** | `.github/workflows/validate.yml` | Hassfest manifest validation + HACS compliance |

The Validate workflow also runs daily on a schedule and can be triggered
manually via `workflow_dispatch`.

## Common Tasks

### Adding a new entity platform

1. Create `custom_components/argon_one/<platform>.py` with `async_setup_entry()`
2. Add `Platform.<PLATFORM>` to the appropriate list in `__init__.py`
   (`PLATFORMS_CLASSIC` and/or `PLATFORMS_PI5`)
3. Add translations for entity names in `translations/en.json` if needed

### Adding a new translation

1. Create `custom_components/argon_one/translations/<lang>.json` (BCP47 code)
2. Copy the structure from `translations/en.json` and translate the values
3. Do **not** create `strings.json` — custom integrations use translation files
   directly

### Debugging I2C on Raspberry Pi

Check I2C is enabled:

```bash
ls /dev/i2c-1
```

Scan for devices on the bus:

```bash
i2cdetect -y 1
```

The Argon ONE case should appear at address `0x1a`.

Test a fan command manually:

```bash
# Classic (Pi 3/4)
python3 -c "from smbus2 import SMBus; SMBus(1).write_byte(0x1A, 50)"

# Pi 5 (V3/V5)
python3 -c "from smbus2 import SMBus; SMBus(1).write_byte_data(0x1A, 0x80, 50)"
```

### Reading HA logs for the integration

In the UI: Settings → System → Logs → filter by `argon_one`.

Via SSH:

```bash
grep argon_one /config/home-assistant.log
```

## Troubleshooting

### `I2C bus not available` during config flow

I2C is not enabled on the Raspberry Pi. Enable it:

```bash
# HAOS
echo "dtparam=i2c_arm=on" >> /mnt/boot/config.txt
reboot
```

Verify after reboot: `ls /dev/i2c-1` should succeed.

### `Argon ONE case not detected on I2C bus`

The case is not responding at address `0x1A`. Check:

1. The Argon ONE board is properly seated on the GPIO header
2. Run `i2cdetect -y 1` — address `0x1a` should be visible
3. Try a different case type in the config flow (Classic vs Pi 5 use different
   I2C commands for probing)

### Integration loads but fan does not spin

- Fan does not physically spin below ~10% speed
- Check HA logs for I2C errors: `grep argon_one /config/home-assistant.log`
- Verify the correct case type was selected (Classic vs Pi 5 use different I2C
  protocols)

### `IOError` in logs after setup

The I2C bus may be busy or the case disconnected. The entity will show as
`unavailable` in HA. It recovers automatically on the next successful I2C
operation.

## Additional Resources

- [AGENTS.md](AGENTS.md) — code guidelines and contribution rules
- [README.md](README.md) — user-facing documentation and installation guide
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution workflow and guidelines
- [Home Assistant Developer Docs](https://developers.home-assistant.io/) — HA
  integration development reference
- [smbus2 documentation](https://smbus2.readthedocs.io/) — I2C library API
- [Argon40 I2C protocol](https://github.com/Argon40Tech/Argon-ONE-i2c-Codes) —
  official I2C command reference
