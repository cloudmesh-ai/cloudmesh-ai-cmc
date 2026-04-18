# cmc: Cloudmesh AI Commands

`cmc` is a powerful command-line interface designed to extend the capabilities of Cloudmesh AI. It provides a modular architecture allowing users to easily add, manage, and execute AI-driven extensions.

## About

The `cmc` tool serves as a central hub for AI extensions. Whether you are performing system diagnostics, generating documentation, or running speed tests, `cmc` provides a consistent interface to interact with various AI models and tools.

Its core strength lies in its **Extension Registry**, which allows you to load plugins from:
- **Core**: Built-in extensions bundled with the package.
- **Pip**: Extensions installed via `pip` using entry points.
- **Registry**: Local extensions registered via a path on your filesystem.

---

## Install

> **Note:** `cmc` is primarily developed on Linux and macOS. As the developers do not use Windows (PowerShell), we strongly recommend using **Git Bash** or **WSL2** for the best experience on Windows.

### Linux / macOS / Git Bash
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

### WSL2 (Windows Subsystem for Linux)
Follow the Linux installation steps within your WSL2 distribution:
```bash
pip install cloudmesh-ai-cmc
```

---

## Quickstart

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

4. **Read the Documentation**:
   ```bash
   cmc docs
   ```

---

## Commands

### Core Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `version` | Displays the current version of `cmc` and a list of active extensions. | `cmc version` |
| `docs` | Displays this comprehensive documentation in the terminal. | `cmc docs` |
| `completion` | Generates shell completion scripts for Bash, Zsh, or Fish. | `cmc completion` |
| `shell` | Enters an interactive shell for executing CMC commands. | `cmc shell` |
| `doctor` | Performs a comprehensive health check of the CMC environment, including AI hardware (GPU/CUDA). | `cmc doctor` |

### Plugin Management

Manage local extensions using the `plugins` group.

| Command | Description | Example |
| :--- | :--- | :--- |
| `plugins list` | Lists all registered plugins and their status. | `cmc plugins list` |
| `plugins add <path>` | Registers a new plugin from a directory. | `cmc plugins add ./my-plugin` |
| `plugins enable <name>` | Activates a registered plugin. | `cmc plugins enable my-plugin` |
| `plugins disable <name>` | Deactivates a registered plugin. | `cmc plugins disable my-plugin` |
| `plugins remove <name>` | Completely removes a plugin from the registry. | `cmc plugins remove my-plugin` |
| `plugins check` | Verifies that all registered plugins are importable and valid. | `cmc plugins check` |
| `init-plugin <name>` | Scaffolds a new CMC plugin directory structure. | `cmc init-plugin my-new-tool` |

### Configuration & Telemetry

| Command | Description | Example |
| :--- | :--- | :--- |
| `config get <key>` | Retrieves a configuration value. | `cmc config get telemetry.enabled` |
| `config set <key> <val>` | Updates a configuration value. | `cmc config set logging.level DEBUG` |
| `config list` | Shows all current configurations. | `cmc config list` |
| `telemetry` | Analyzes CMC telemetry data with filtering and export options. | `cmc telemetry --status FAILURE` |

### Built-in Extensions

`cmc` comes with several core extensions:
- `cmc banner`: Displays a stylized banner.
- `cmc tree`: Generates a directory tree structure.
- `cmc man`: Provides manual-style help for commands.
- `cmc command`: Executes AI-assisted system commands.

---

## Interactive Shell

The `cmc shell` provides an immersive environment for interacting with the CMC ecosystem without needing to restart the CLI for every command.

### Key Features
- **Tab Completion**: Intelligent autocomplete for all registered CMC commands, sub-commands, and internal shell utilities.
- **Persistent History**: Command history is saved to `~/.config/cloudmesh/ai/cmc_history`, allowing you to recall previous commands across sessions.
- **Dynamic Updates**: The command completer is refreshed on every loop, meaning newly added or enabled plugins are immediately available for autocomplete.

### Internal Shell Commands
In addition to standard `cmc` commands, the shell supports several built-in utilities:

| Command | Description | Example |
| :--- | :--- | :--- |
| `help` | Displays the shell help menu. | `help` |
| `set <K>=<V>` | Sets a temporary environment variable for the current session. | `set API_KEY=secret123` |
| `h <num>` | Displays the last `<num>` commands from the history file. | `h 10` |
| `exit` / `quit` / `q` | Exits the interactive shell. | `exit` |

### Usage Example
Here is a typical workflow using the interactive shell:

```bash
# 1. Enter the interactive shell
cmc shell

# 2. Inside the shell, run a CMC command (with tab completion)
cmc> version

# 3. Set a session variable for a plugin
cmc> set MODEL_NAME=gpt-4o

# 4. Run a command that uses that variable
cmc> doctor

# 5. View recent history
cmc> h 5

# 6. Exit the shell
cmc> exit
```

### Technical Implementation (Developer Note)
The shell is implemented using `prompt_toolkit` for the frontend and `click` for command execution. 
- **Command Collection**: The shell recursively traverses the `click.Group` hierarchy of the main CLI to build a flat list of all available command paths.
- **Context Management**: To avoid recursion depth errors and `TypeError` during command discovery, a shared `click.Context` and a `visited` set are used during the recursive traversal of the command tree.
- **Execution**: Commands are executed via `cli.main(args=args, standalone_mode=False)`, which allows the shell to capture errors and usage warnings without terminating the process.

---

## Configuration & Environment

`cmc` uses a YAML configuration file located at `~/.config/cloudmesh/ai/cmc.yaml`.

### Environment Variable Overrides
You can override any configuration setting using environment variables with the `CMC_` prefix. Dot-separated keys are converted to underscores and uppercase.

**Example:**
- `telemetry.path` $\rightarrow$ `CMC_TELEMETRY_PATH`
- `logging.level` $\rightarrow$ `CMC_LOGGING_LEVEL`

```bash
# Override log level for a single execution
CMC_LOGGING_LEVEL=DEBUG cmc doctor
```

---

## Logging and Debugging

`cmc` uses a configurable logging system. You can control the granularity of the output using the `CMC_LOGGING_LEVEL` environment variable or the `--debug` flag.

### Log Levels
- `ERROR`: Only critical errors are shown.
- `WARNING`: Errors and potential issues are shown (Default).
- `INFO`: General operational messages.
- `DEBUG`: Detailed diagnostic information, including extension loading and validation steps.

### Usage
```bash
# Using the CLI flag
cmc --debug doctor
```

---

## Extensions

### Extension Creation

The easiest way to create a new extension is using the built-in scaffolding tool:
```bash
cmc init-plugin my-extension
```

### Manual Implementation
An extension is a Python module that defines a `click` command. To ensure proper integration, include the following metadata:

```python
import click

version = "0.1.0"
description = "My awesome AI extension"
dependencies = []  # List of other plugin names this plugin depends on

@click.command()
def entry_point():
    """Plugin description here."""
    click.echo("Hello from the new plugin!")
```

### Advanced Extensions: Using `register(cli)`
For complex extensions with multiple sub-commands, implement a `register(cli)` function:

```python
import click

@click.command()
def start():
    click.echo("Service started!")

def register(cli):
    @cli.group(name="myservice")
    def service_group():
        """Manage the custom service."""
        pass
    service_group.add_command(start)