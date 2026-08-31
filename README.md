# cloudmesh-ai-cmc

**Quick Links:**
- [API Reference](API.md) - Full technical documentation of all modules.

`cloudmesh-ai-cmc` is an extensible Command Line
Interface (CLI) framework designed to integrate AI-driven tools and custom
extensions seamlessly. It serves as the central orchestrator for the
Cloudmesh AI ecosystem, providing a robust registry system for managing
commands and a developer-friendly environment for rapid extension creation.

## About

The `cmc` tool serves as a central hub for AI extensions. Whether you are performing system diagnostics, generating documentation, or running speed tests, `cmc` provides a consistent interface to interact with various AI models and tools.

Its core strength lies in its **Extension Registry**, which allows you to load plugins from:
- **Core**: Built-in extensions bundled with the package.
- **Pip**: Extensions installed via `pip` using entry points.
- **Registry**: Local extensions registered via a path on your filesystem.

## Usage

``` text
Usage:
    cmc [options] <command> [args]...
    cmc -h | --help

Options:
    -h, --help            Show this screen.
    --debug               Enable verbose debug logging for troubleshooting.

Commands:
    cmc command list                 List all registered AI extensions.
    cmc command load <path>          Register and load a new command.
    cmc command activate <name>      Activate a registered command.
    cmc command deactivate <name>    Deactivate a registered command.
    cmc command unload <name>        Remove a command from the registry.
    cmc command create <name>        Create or expand a CMC command.
    cmc command man <name>           Display the manual for CME commands.
    cmc version                      Display current version and extensions.
    cmc completion [--install]       Generate or install shell completion.
    cmc shell                        Enter an interactive CMC shell.
    cmc docs                         Display framework documentation.
    cmc logs [--command <name>] [--status <status>] [--since <days>]
              [--limit <n>] [--format <fmt>] [--summary]
                                      View and analyze telemetry logs.
    cmc doctor                       Perform a system health check.
    cmc tree                         Display directory structure visually.
    cmc time                         Stopwatch commands for execution time.
        cmc time start <id>          Start or resume a stopwatch.
        cmc time stop <id>           Stop a stopwatch.
        cmc time rm <id>             Remove a stopwatch.
        cmc time clean               Erase all stopwatches.
        cmc time list                List all stopwatches and elapsed times.
    cmc config                       Manage CMC configuration.
        cmc config get <key>         Retrieve a configuration value.
        cmc config set <key> <val>   Update a configuration value.
        cmc config list              Show all current configurations.
    cmc telemetry                    Manage and view AI telemetry data.
        cmc telemetry on             Enable telemetry collection.
        cmc telemetry off            Disable telemetry collection.
        cmc telemetry list [--command <name>] [--status <status>]
                        [--since <days>] [--export <fmt>]
                                      List and filter telemetry records.
    cmc markdown                     Markdown utility tools.
        cmc markdown fix <file>      Fix formatting issues in a file.
    cmc sys                          System information and diagnostics.
        cmc sys info                 Display system information.
```

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

## Key Features

### High-Performance Architecture

- **Lazy Loading**: To ensure near-instant startup times, `cloudmesh-ai-cmc`
  implements a lazy-loading mechanism. Extension code is only imported into
  memory at the moment the specific command is invoked.
- **Dynamic Extension Management**: Extensions can be loaded from
  pip-installed packages (via entry points) or dynamically from local
  filesystem paths.

### Developer-First Tooling

- **Rapid Scaffolding**: The `cmc command create` utility eliminates
  boilerplate friction by instantly generating the required directory
  structure.
- **Flexible Integration Patterns**: Supports multiple registration styles:
  - **Simple**: Function-based entry points for quick tools.
  - **Advanced**: The `register(cli)` pattern for complex, nested command groups using `click`.

### Rich Documentation Experience

- **Terminal-Native Docs**: The `docs` command renders formatted Markdown
  directly in the terminal using `rich`.
- **Integrated Man Pages**: Every extension can provide a detailed manual
  page accessible via `cmc man <command>`.

## Installation

> **Note:** `cmc` is primarily developed on Linux and macOS. As the developers do not use Windows (PowerShell), we strongly recommend using **Git Bash** or **WSL2** for the best experience on Windows.

### Recommended: Using pipx
For the best experience with CLI tools, use `pipx` to install `cloudmesh-ai-cmc` in an isolated environment. This prevents dependency conflicts and automatically adds the `cmc` command to your PATH.

```bash
pipx install cloudmesh-ai-cmc
```

To install from a local directory:
```bash
pipx install .
```

### Using pip
If you prefer a standard installation in your current environment:

```bash
pip install cloudmesh-ai-cmc
```

To install from a local directory:
```bash
pip install .
```

### Windows Specifics
**Git Bash / WSL2**: Follow the Linux installation steps.

**PowerShell/CMD**: It is recommended to use a Python virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install cloudmesh-ai-cmc
```

## Detailed Usage Guide

### Command Reference

For complex commands, the following options are available:

#### `cmc logs`
View and analyze the CMC telemetry logs.
- `--command <name>`: Filter logs to show only a specific command.
- `--status <status>`: Filter by execution status (e.g., `SUCCESS`, `FAILURE`).
- `--since <days>`: Show records from the last N days.
- `--limit <n>`: Limit the number of records displayed (default: 100).
- `--format <fmt>` or `-f`: Output format. Options: `table` (default),
  `json`, `csv`.
- `--summary`: Generate a performance summary including success rates and
  average durations.

#### `cmc telemetry list`
List and filter raw telemetry records.
- `--command <name>`: Filter by command name.
- `--status <status>`: Filter by status (e.g., `completed`, `failed`).
- `--since <days>`: Filter records from the last N days.
- `--export <fmt>`: Export results to a file. Options: `json`, `csv`.

#### `cmc config set <key> <val>`
Update a configuration value. The framework automatically casts values:
- `true`/`false` $\rightarrow$ Boolean
- Digits $\rightarrow$ Integer
- Decimals $\rightarrow$ Float
- Others $\rightarrow$ String

### Shell Completion Setup

CMC provides native shell completion for Bash, Zsh, and Fish to accelerate
command entry and discovery.

#### Automatic Installation

The easiest way to set up completion is to use the built-in install flag:

```bash
cmc completion --install
```

This command detects your current shell and appends the necessary activation
script to your profile (e.g., `~/.bashrc`, `~/.zshrc`, or `config.fish`).

#### Manual Activation

If you prefer to manage your profile manually, add the following line to your
shell configuration file:

- **Bash**: `eval "$(_CME_COMPLETE=bash_source cmc)"`
- **Zsh**: `eval "$(_CME_COMPLETE=zsh_source cmc)"`
- **Fish**: `eval (_CME_COMPLETE=fish_source cmc)`

#### Activating Changes

After installation or manual editing, reload your shell profile to activate
completion immediately:

```bash
# For Bash/Zsh
source ~/.bashrc  # or ~/.zshrc

# For Fish
source ~/.config/fish/config.fish
```

Alternatively, you can simply restart your terminal.

### Troubleshooting Shell Completion

If completion is not working after following the steps above:

1. **Verify Installation**: Run `cmc completion` to see the recommended
   activation string for your current shell.
2. **Manual Test**: Try running the activation string directly in your
   terminal (e.g., `eval "$(_CME_COMPLETE=zsh_source cmc)"`). If this
   produces an error, ensure `cmc` is in your system `PATH`.
3. **Zsh Specifics**: If you are using Zsh, ensure you have `compinit`
   initialized in your `.zshrc` (usually via `autoload -Uz compinit && compinit`).
4. **Shell Restart**: In some environments, a full terminal restart is
   required for the shell to recognize new completion functions.

### Managing the Extension Registry

The registry allows you to control which AI tools are available.

```bash
# View all available extensions and whether they are active
cmc command list

# Load a custom extension you are developing locally
cmc command load /Users/grey/work/myextension

# Toggle a command's availability
cmc command activate speedtest
cmc command deactivate speedtest
```

### Creating New AI Tools

To start a new extension, use the scaffolding command:

```bash
cmc command create myextension
```

For a detailed step-by-step guide, see the [Developer's Guide](#developers-guide) below.

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

## Developer's Guide

### Extension Patterns

#### Creating a Command with `cmc command create`

The easiest way to build a new extension is using the built-in scaffolding tool. This ensures your project has the correct directory structure and configuration for the CMC framework.

**1. Scaffold the project**
```bash
cmc command create myextension
```

**2. Implement your logic**
The tool generates a project in `./myextension`. Edit `src/cloudmesh/ai/command/myextension.py` to define your command group and subcommands. We recommend the **Advanced Pattern** for better scalability.

**3. Install for development**
Use an editable install to test your changes instantly:
```bash
cd myextension
pip install -e .
```

**4. Verify**
```bash
cmc myextension run
```

#### Publishing to GitHub with `cmc command upload`

Once your extension is tested and ready for distribution, you can upload it directly to GitHub using the `upload` command. This tool automates the repository creation and initial push process.

**Basic Usage**
If you are inside your project directory:
```bash
cmc command upload .
```

**Specifying a Path**
You can also upload from any directory by providing the path to the extension:
```bash
cmc command upload /Users/grey/work/cloudmesh-ai-myextension
```

**Custom Organization**
By default, the tool uploads to the `cloudmesh-ai` organization. To use a different one:
```bash
cmc command upload . --org=my-custom-org
```

**What this command does automatically:**
- **Git Initialization**: Initializes a local git repository if one doesn't exist.
- **Artifact Filtering**: Creates a `.gitignore` file to prevent uploading `__pycache__`, `.egg-info`, and other build artifacts.
- **GitHub Integration**: Uses the `gh` CLI to either create a new public repository or update an existing one.
- **Initial Commit**: Performs an initial commit to ensure the repository is ready for pushing.

#### 1. Simple Extension (Function-based)
Best for single-purpose tools. Define a `click` command in your module:

``` python
import click

version = "0.1.0"
description = "My awesome AI extension"
dependencies = []  # List of other plugin names this plugin depends on

@click.command()
def entry_point():
    """Plugin description here."""
    click.echo("Hello from the new plugin!")
```

#### 2. Advanced Extension (The `register` Pattern)
Best for complex tools with sub-commands. Implement a `register` function:

``` python
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
```

### Distribution Comparison

| Feature          | Core Extension     | Pip Extension       |
|:-----------------|:-------------------|:--------------------|
| **Loading**      | Filesystem Scan    | Entry Points        |
| **Installation** | Copy to `command/` | `pip install`       |
| **Update Cycle** | Instant (on save)  | Requires re-install |
| **Use Case**     | Rapid Prototyping  | Production Release  |

## Telemetry & Observability

CMC includes a built-in telemetry system to track AI tool performance and reliability.

### Tracked Metrics

Every command execution captures:
\* **Duration**: Total execution time in seconds (`duration_sec`).
\* **Status**: `started`, `completed`, or `failed`.
\* **System Context**: CPU model, GPU presence/model, and total memory.
\* **Custom KPIs**: Extension-specific metrics passed to the telemetry sink.

### Storage Backends

Telemetry can be routed to multiple sinks: \* **JSONL**: Structured logs for machine ingestion. \* **SQLite**: Relational storage for complex querying. \* **Text**: Human-readable logs for quick debugging.

### Control

To disable telemetry globally, set the following environment variable: `CLOUDMESH_AI_TELEMETRY_DISABLED=true`

## Documentation and Help

```bash
# View the global AI documentation index
cmc docs

# View the specific manual for the speedtest tool
cmc man speedtest
```

### Sample Output: Version

``` text
cmc version 0.1.0
```

## Architecture

The CMC framework uses a delegating registry to maintain a small memory footprint while supporting a vast library of tools.

``` mermaid
graph TD
    A[User Input: cmc <cmd>] --> B[SubcommandHelpGroup]
    B --> C{Is Command Lazy?}
    C -- Yes --> D[LazyCommand Registry]
    D --> E[importlib.import_module]
    E --> F[DelegatingCommand Wrapper]
    C -- No --> G[Direct Execution]
    F --> H[Extension Logic]
    G --> H
```

The `DelegatingCommand` wrapper is critical for enterprise stability; it
isolates the core framework from extensions that may have been compiled
against different versions of the `click` library, preventing runtime
type-mismatch crashes.

## Troubleshooting & FAQ

**Q: I installed a pip extension, but `cmc` doesn't see it.** A: Ensure the package defines the `cloudmesh.ai.command` entry point in its `pyproject.toml` or `setup.py`. Run `pip list` to verify installation.

**Q: I'm seeing "Click version mismatch" errors in debug logs.** A: This is normal. CMC uses `DelegatingCommand` to wrap these extensions, ensuring they still execute correctly despite version differences.

**Q: How do I debug a failing `command load`?** A: Run the command with `CMC_LOG_LEVEL=DEBUG`. The logs will show exactly where the `importlib` failure occurred during the lazy-load attempt.