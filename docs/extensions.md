# Extension Development Guide

`cloudmesh-ai-cmc` is designed as a modular framework, allowing developers to easily add new AI-driven capabilities through extensions.

## Overview

Extensions are the primary way to extend the functionality of the `cmc` tool. They are implemented as Python modules and can be distributed as part of the core package, installed via `pip`, or loaded from a local directory.

## Creating an Extension

### Using the Scaffolding Tool

The quickest way to start is by using the built-in scaffolding tool, which creates the necessary directory structure and template files:

```bash
cmc init-plugin myextension
```

### Manual Implementation

An extension is a Python module that defines a `click` command. To ensure proper integration and visibility in the registry, your module should include the following metadata:

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

### Advanced Extensions: The `register` Pattern

For complex tools that require multiple sub-commands, implement a `register(cli)` function. This allows the extension to attach a group of commands to the main `cmc` CLI.

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
```

## Distribution Comparison

Depending on your use case, you can distribute your extension in different ways:

| Feature          | Core Extension     | Pip Extension       |
|:-----------------|:-------------------|:--------------------|
| **Loading**      | Filesystem Scan    | Entry Points        |
| **Installation** | Copy to `command/` | `pip install`       |
| **Update Cycle** | Instant (on save)  | Requires re-install |
| **Use Case**     | Rapid Prototyping  | Production Release  |

## Plugin Lifecycle Management

Once an extension is created, you can manage it using the `plugins` command group:

- **Register**: `cmc plugins add <path>`
- **Activate**: `cmc plugins enable <name>`
- **Deactivate**: `cmc plugins disable <name>`
- **Remove**: `cmc plugins remove <name>`
- **Verify**: `cmc plugins check`
