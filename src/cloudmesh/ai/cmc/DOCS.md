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

### Linux
```bash
pip install cloudmesh-ai-cmc
```

### macOS
```bash
pip install cloudmesh-ai-cmc
```

### Windows
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

3. **Read the Documentation**:
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

### Extension Management

The `command` group allows you to manage local extensions without needing to package them as pip modules.

| Command | Description | Example |
| :--- | :--- | :--- |
| `command list` | Lists all available extensions (Core, Pip, and Registered). | `cmc command list` |
| `command load` | Registers and loads a new extension from a directory. | `cmc command load --dir /path/to/ext` |
| `command activate` | Enables a previously registered extension. | `cmc command activate my-extension` |
| `command deactivate` | Disables an extension, removing it from the active list. | `cmc command deactivate my-extension` |
| `command unload` | Completely removes an extension from the registry. | `cmc command unload my-extension` |

### Built-in Extensions

`cmc` comes with several core extensions:
- `cmc banner`: Displays a stylized banner.
- `cmc tree`: Generates a directory tree structure.
- `cmc man`: Provides manual-style help for commands.
- `cmc command`: Executes AI-assisted system commands.

---

## Logging and Debugging

`cmc` uses a configurable logging system to help with troubleshooting and development. You can control the granularity of the output using the `CMC_LOG_LEVEL` environment variable or the `--debug` flag.

### Log Levels
The following levels are supported (in order of increasing verbosity):
- `ERROR`: Only critical errors are shown.
- `WARNING`: Errors and potential issues are shown (Default).
- `INFO`: General operational messages.
- `DEBUG`: Detailed diagnostic information, including extension loading and validation steps.

### Usage
To enable debug logging, you can use either of the following methods:

**1. Using the environment variable:**
```bash
# Enable debug logging for a single command
CMC_LOG_LEVEL=DEBUG cmc speedtest run ...

# Set it for the current session
export CMC_LOG_LEVEL=DEBUG
cmc speedtest run ...
```

**2. Using the CLI flag:**
```bash
cmc --debug speedtest run ...
```

---

## Extensions

### Extension Management

Extensions are the heart of `cmc`. You can manage them using the `registry` commands. When you `add` a directory to the registry, `cmc` looks for a compatible entry point (a `click.Command` or a `register` function) within that directory to integrate it into the CLI.

### Extension Creation

The easiest way to create a new extension is using the built-in scaffolding tool.

#### 1. Automated Scaffolding
Use the `cmc command create` tool to generate a complete project structure, including `pyproject.toml` and the necessary source directories.

**Basic creation:**
```bash
cmc command create my-extension
```

**Creation with multiple sub-commands:**
If you want your extension to have multiple functions, use the `--groups` flag:
```bash
cmc command create my-tool -g analyze -g report -g clean
```

**Specify output path:**
```bash
cmc command create my-tool --path ~/projects/ai-plugins
```

This creates a directory `cloudmesh-ai-my-tool` with a ready-to-use Python plugin.

#### 2. Manual Implementation (Optional)
If you prefer to build it manually, an extension is simply a Python module that defines a `click` command.

**Basic Structure:**
```text
my-extension/
└── my_extension.py
```

**Implementation:**
```python
import click

@click.command()
def entry_point():
    """My awesome AI extension."""
    click.echo("Hello from my custom extension!")
```

#### 3. Registering and Using your extension
Once created (either via `command create` or manually), register the directory with `cmc`:

```bash
# Register the extension
cmc registry add /path/to/my-extension

# Use the extension
cmc my-extension
```

#### 4. Advanced Extensions: Using `register(cli)`

For complex extensions that require multiple sub-commands, you can implement a `register(cli)` function. This function is automatically called by `cmc` when the extension is loaded.

**Example Implementation:**

```python
import click

@click.command()
def start():
    """Start the service."""
    click.echo("Service started!")

@click.command()
def stop():
    """Stop the service."""
    click.echo("Service stopped!")

def register(cli):
    """Register multiple commands under a group."""
    @cli.group(name="myservice")
    def service_group():
        """Manage the custom service."""
        pass
    
    service_group.add_command(start)
    service_group.add_command(stop)
```

With this approach, your commands will be available as `cmc myservice start` and `cmc myservice stop`.
