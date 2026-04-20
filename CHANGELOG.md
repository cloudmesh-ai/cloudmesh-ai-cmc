# Changelog

All notable changes to `cloudmesh-ai-cmc` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.0.2.dev2] - 2026-04-19

### Fixed
- **Shell Completion**:
    - Fixed subcommand completion falling back to filename completion.
    - Suppressed debug logs and rogue stdout/stderr output during completion requests.
    - Improved Zsh completion script and provided activation instructions.
    - Added `stdin` support for completion testing.
- **Interactive Shell**:
    - Fixed ANSI escape codes appearing in the prompt.
    - Updated prompt color to dark blue.

## [7.0.2.dev1] - 2026-04-19

### Added
- **Core CMC Framework**: Established the central command-line interface for AI tool management.
    - Dynamic command registration and execution context.
    - Plugin-based architecture for easy extension.
- **Plugin Development Tooling**: 
    - Provided templates for `pyproject.toml`, `Makefile`, `LICENSE`, and `plugin.py`.
    - Added `gen_plugin_docs.py` for automated plugin documentation.
    - Added `version_mgmt.py` for streamlined version control.
- **Built-in System Commands**:
    - `doctor`: Comprehensive environment health check.
    - `sys info`: Detailed system and hardware diagnostics.
    - `config`: Centralized configuration management.
    - `version`: Version tracking for CMC and loaded extensions.
- **Operational Utilities**:
    - `shell`: Interactive command shell for rapid testing.
    - `completion`: Shell completion support for improved UX.
    - `man`: Automated manual generation for all registered commands.
    - `tree`: Visual directory structure tool.
    - `time`: Timing utilities for command execution.
- **AI & Content Tools**:
    - `markdown`: Gemini-powered markdown processing and formatting.
    - `banner`: Visual branding for the CLI.
- **Observability Integration**:
    - `telemetry` and `logs`: Direct integration with `cloudmesh-ai-common` for performance monitoring and log analysis.
- **Test Suite**: Implemented unit and integration tests for core CMC functionality and plugin integration.

### Changed
- Initial architecture designed to serve as the primary entry point for the entire `cloudmesh-ai` ecosystem.
