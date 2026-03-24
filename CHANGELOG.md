# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Fan preset modes (Silent, Default, Performance) with automatic temperature-based speed control via a configurable HA sensor ([#7](https://github.com/fix-parrot/argon-one/issues/7))
- Complete development workflow overhaul: `uv` package management, 84 tests, CI/CD pipeline, static analysis tooling, mock dev environment, and infrastructure improvements ([#10](https://github.com/fix-parrot/argon-one/issues/10))

## [0.1.0] - 2026-03-21

### Added

- Home Assistant custom integration for Argon ONE Raspberry Pi cases with support for:
  - Argon ONE V1/V2 (Classic) cases with Pi 3/4
  - Argon ONE V3/V5 cases with Pi 5
- Fan speed control (0-100%) via I2C for all case types
- Always ON power mode control for Classic cases (Pi 3/4) via I2C switch
- UI-based configuration flow with case type selection and I2C bus validation
- HACS integration support with custom repository installation
- Temperature-based automation examples in documentation

[unreleased]: https://github.com/fix-parrot/argon-one/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fix-parrot/argon-one/releases/tag/v0.1.0
