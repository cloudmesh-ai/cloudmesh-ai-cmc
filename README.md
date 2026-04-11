# cloudmesh-ai-cmc

`cloudmesh-ai-cmc` is a highly extensible Command Line Interface (CLI) framework designed to integrate AI-driven tools and custom extensions seamlessly. It provides a robust registry system for managing commands and a developer-friendly environment for creating new extensions.

## Key Features

*   **Extensible CLI Architecture**: A modular command-line interface designed to be extended with custom plugins and AI-driven tools.
*   **Dynamic Extension Management**: 
    *   **Plug-and-Play**: Load extensions dynamically from local directories or pip-installed packages.
    *   **Command Registry**: Centralized management of extensions with the ability to activate, deactivate, load, and unload commands on the fly.
*   **High Performance**: Implements **Lazy Loading**, ensuring that extension code is only imported when the specific command is executed, maintaining near-instant CLI startup times.
*   **Developer-First Tooling**: 
    *   **Rapid Scaffolding**: Built-in `cmc command create` utility to instantly generate the required directory structure and boilerplate for new extensions.
    *   **Flexible Integration**: Supports both simple function-based entry points and advanced `register(cli)` patterns for complex command groups.
*   **Rich Documentation Experience**:
    *   **Integrated Docs**: A dedicated `docs` command that renders professional, formatted Markdown documentation directly in the terminal.
    *   **Man-Page Support**: Detailed manual pages for extensions via the `man` command.
    *   **Themed Output**: Custom terminal styling with syntax highlighting and a clean, readable layout.
*   **Enterprise-Ready Design**:
    *   **Namespace Compatible**: Utilizes `importlib.resources` for robust asset loading across different installation environments.
    *   **Shell Integration**: Full support for shell completion to improve user productivity.
    *   **Standardized Packaging**: Fully compatible with `pyproject.toml` and standard Python packaging workflows.

## Installation

```bash
cd cloudmesh-ai-cmc
pip install .
```

## Basic Usage

### General Help
```bash
cmc --help
```

### Managing Extensions
```bash
# List all registered commands
cmc command list

# Load a new extension from a directory
cmc command load /path/to/extension

# Activate/Deactivate a command
cmc command activate <command_name>
cmc command deactivate <command_name>

# Unload an extension
cmc command unload <command_name>
```

### Creating a New Extension
```bash
cmc command create <extension_name>
```

### Accessing Documentation
```bash
cmc docs
cmc man <command_name>
```

## Logging and Debugging

`cloudmesh-ai-cmc` uses a configurable logging system to help with troubleshooting and development. You can control the granularity of the output using the `CMC_LOG_LEVEL` environment variable.

### Log Levels
The following levels are supported (in order of increasing verbosity):
- `ERROR`: Only critical errors are shown.
- `WARNING`: Errors and potential issues are shown.
- `INFO`: General operational messages (Default).
- `DEBUG`: Detailed diagnostic information, including extension loading and validation steps.

### Usage
To enable debug logging, set the environment variable before running the command:

```bash
# Enable debug logging for a single command
CMC_LOG_LEVEL=DEBUG cmc speedtest run ...

# Set it for the current session
export CMC_LOG_LEVEL=DEBUG
cmc speedtest run ...
```
