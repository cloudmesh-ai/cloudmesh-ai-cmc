# CLI Reference

The `cmc` tool provides a powerful command-line interface to manage and execute AI-driven extensions.

## General Usage

```bash
cmc [options] <command> [args]...
```

### Global Options

| Option | Description |
| :--- | :--- |
| `-h, --help` | Show this help screen. |
| `--debug` | Enable verbose debug logging for troubleshooting. |

## Commands

### Core Framework Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `version` | Displays the current version of `cmc` and a list of active extensions. | `cmc version` |
| `docs` | Displays the documentation index. | `cmc docs` |
| `completion` | Generates shell completion scripts for Bash, Zsh, or Fish. | `cmc completion --install` |
| `shell` | Enters an interactive shell for executing CMC commands. | `cmc shell` |
| `doctor` | Performs a comprehensive health check of the CMC environment, including AI hardware (GPU/CUDA). | `cmc doctor` |

### Plugin Management

Manage local extensions and their lifecycle.

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

Manage framework settings and observability.

| Command | Description | Example |
| :--- | :--- | :--- |
| `config get <key>` | Retrieves a configuration value. | `cmc config get telemetry.enabled` |
| `config set <key> <val>` | Updates a configuration value. | `cmc config set logging.level DEBUG` |
| `config list` | Shows all current configurations. | `cmc config list` |
| `telemetry on` | Enables telemetry collection. | `cmc telemetry on` |
| `telemetry off` | Disables telemetry collection. | `cmc telemetry off` |
| `telemetry list` | Lists and filters telemetry records. | `cmc telemetry list --status FAILURE` |

## Interactive Shell

The `cmc shell` provides an immersive environment for interacting with the CMC ecosystem without needing to restart the framework for every command.

### Features
- **Auto-completion**: Full tab-completion for all registered CMC commands, sub-commands, and internal shell utilities.
- **Persistent History**: Command history is saved to `~/.config/cloudmesh/ai/cmc_history`.
- **Dynamic Updates**: Newly added or enabled plugins are immediately available for autocomplete.

### Internal Shell Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `help` | Displays the shell help menu. | `help` |
| `set <K>=<V>` | Sets a temporary environment variable for the current session. | `set API_KEY=secret123` |
| `h <num>` | Displays the last `<num>` commands from the history file. | `h 10` |
| `exit` / `quit` / `q` | Exits the interactive shell. | `exit` |

### Usage Example

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
- **Context Management**: A shared `click.Context` and a `visited` set are used during the recursive traversal of the command tree to avoid recursion depth errors.
- **Execution**: Commands are executed via `cli.main(args=args, standalone_mode=False)`, which allows the shell to capture errors without terminating the process.

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

## Logging and Debugging

You can control the granularity of the output using the `CMC_LOGGING_LEVEL` environment variable or the `--debug` flag.

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
