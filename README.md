# cloudmesh-ai-cmc

`cloudmesh-ai-cmc` is a professional-grade, highly extensible Command Line
Interface (CLI) framework designed to integrate AI-driven tools and custom
extensions seamlessly. It serves as the central orchestrator for the
Cloudmesh AI ecosystem, providing a robust registry system for managing
commands and a developer-friendly environment for rapid extension creation.

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

### Recommended: Using pipx
For the best experience with CLI tools, use `pipx` to install `cloudmesh-ai-cmc` in an isolated environment. This prevents dependency conflicts and automatically adds the `cmc` command to your PATH.

``` bash
pipx install cloudmesh-ai-cmc
```

To install from a local directory:
``` bash
pipx install .
```

### Using pip
If you prefer a standard installation in your current environment:

``` bash
pip install cloudmesh-ai-cmc
```

To install from a local directory:
``` bash
pip install .
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

``` bash
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

``` bash
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

``` bash
# View all available extensions and whether they are active
cmc command list

# Load a custom extension you are developing locally
cmc command load /Users/grey/work/my-ai-extension

# Toggle a command's availability
cmc command activate speedtest
cmc command deactivate speedtest
```

### Creating New AI Tools

To start a new extension, use the scaffolding command:

``` bash
cmc command create my-new-tool
```

## Developer's Guide

### Extension Patterns

#### 1. Simple Extension (Function-based)

Best for single-purpose tools. Define a `click` command in your module:

``` python
import click

@click.command()
def entry_point():
    click.echo("Hello from a simple extension!")
```

#### 2. Advanced Extension (The `register` Pattern)

Best for complex tools with sub-commands. Implement a `register` function:

``` python
import click

@click.group()
def my_tool_group():
    """Main group for my complex tool."""
    pass

@my_tool_group.command()
def run():
    click.echo("Running complex logic...")

def register(cli):
    cli.add_command(my_tool_group)
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

``` bash
# View the global AI documentation index
cmc docs

# View the specific manual for the speedtest tool
cmc man speedtest
```

### Sample Output: Version

``` text
cmc version 0.1.0
```

## Logging and Debugging

### Log Levels

Controlled via the `CMC_LOG_LEVEL` environment variable: - `ERROR`: Only critical failures. - `WARNING`: Potential issues and errors. - `INFO`: Standard operational messages (Default). - `DEBUG`: Full diagnostic trace, including lazy-loading events.

### Example

``` bash
# Run a command with full debug tracing
CMC_LOG_LEVEL=DEBUG cmc speedtest run my-server.com
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