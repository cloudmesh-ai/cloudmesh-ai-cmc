# Cloudmesh AI CMC

`cloudmesh-ai-cmc` is an extensible Command Line Interface (CLI) framework designed to integrate AI-driven tools and custom extensions. It serves as the central orchestrator for the Cloudmesh AI ecosystem, providing a registry system for managing commands and a developer-friendly environment for rapid extension creation.

**Quick Links:**
- [Documentation Site](https://cloudmesh-ai.github.io/cloudmesh-ai-cmc) - Full user guides and API reference.
- [GitHub Repository](https://github.com/cloudmesh-ai/cloudmesh-ai-cmc) - Source code and issue tracker.

## Installation

`cmc` is primarily developed on Linux and macOS. For Windows, the use of **Git Bash** or **WSL2** is strongly recommended for the best experience.

### Linux / macOS / Git Bash / WSL2
```bash
pip install cloudmesh-ai-cmc
```

### Windows (PowerShell/CMD)
It is recommended to use a Python virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install cloudmesh-ai-cmc
```

## Quick Start

1. **Verify Installation**:
   ```bash
   cmc version
   ```

2. **Explore Available Commands**:
   ```bash
   cmc --help
   ```

3. **Enter Interactive Mode**:
   ```bash
   cmc shell
   ```

## Core Features

The CMC framework provides several key capabilities:

### Extension Registry
Load plugins from three sources:
- **Core**: Built-in extensions bundled with the package.
- **Pip**: Extensions installed via `pip` using entry points.
- **Registry**: Local extensions registered via a path on your filesystem.

### Unified Interface
A consistent interface to interact with various AI models and tools, whether for system diagnostics, documentation generation, or performance testing.

### Built-in Telemetry
Integrated system to track AI tool performance, reliability, and system context across all command executions.

### Interactive Shell
A powerful shell with tab completion and session variable management for efficient command execution.

For more detailed information, please refer to the [User Guide](cli.md).
