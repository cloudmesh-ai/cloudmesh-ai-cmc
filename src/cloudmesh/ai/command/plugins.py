# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import click
import os
import sys
import subprocess
import importlib
from importlib.metadata import entry_points
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

from cloudmesh.ai.cmc.context import logger, registry

console = Console()

@click.group(name="plugins")
def entry_point():
    """Manage and verify CMC plugins."""
    pass

@entry_point.command(name="list")
def list_plugins():
    """List all registered plugins."""
    details = registry.list_all_details()
    if not details:
        console.print("[yellow]No plugins registered.[/yellow]")
        return

    table = Table(title="Registered Plugins", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version", style="magenta")
    table.add_column("Path", style="dim")

    for item in details:
        status = "[green]Active[/green]" if item["active"] else "[red]Inactive[/red]"
        table.add_row(item["name"], status, item["version"], item["path"])

    console.print(table)

@entry_point.command(name="add")
@click.argument("path")
def add_plugin(path):
    """Add a new plugin to the registry."""
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        console.print(f"[red]Error: {abs_path} is not a directory.[/red]")
        sys.exit(1)
    
    registry.register(None, abs_path)
    console.print(f"[green]Successfully registered plugin from {abs_path}[/green]")

@entry_point.command(name="remove")
@click.argument("name")
def remove_plugin(name):
    """Remove a plugin from the registry."""
    details = registry.list_all_details()
    if not any(item["name"] == name for item in details):
        console.print(f"[red]Error: Plugin '{name}' not found in registry.[/red]")
        sys.exit(1)
    
    registry.unregister(name)
    console.print(f"[green]Successfully removed plugin '{name}' from registry.[/green]")

@entry_point.command(name="enable")
@click.argument("name")
def enable_plugin(name):
    """Enable a plugin in the registry."""
    if registry.set_status(name, True):
        console.print(f"Plugin '{name}' has been [green]enabled[/green].")
    else:
        console.print(f"[red]Error: Plugin '{name}' not found in registry.[/red]")
        sys.exit(1)

@entry_point.command(name="disable")
@click.argument("name")
def disable_plugin(name):
    """Disable a plugin in the registry."""
    if registry.set_status(name, False):
        console.print(f"Plugin '{name}' has been [red]disabled[/red].")
    else:
        console.print(f"[red]Error: Plugin '{name}' not found in registry.[/red]")
        sys.exit(1)

@entry_point.command(name="check")
def check_plugins():
    """Verify that all registered plugins are importable and valid."""
    table = Table(title="Plugin Health Check", box=box.ROUNDED)
    table.add_column("Plugin", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Status", style="green")

    # 1. Check Core Extensions
    core_modules = ["banner", "tree", "man", "command", "docs", "doctor", "plugins", "telemetry", "config", "version", "shell", "completion"]
    for mod in core_modules:
        try:
            importlib.import_module(f"cloudmesh.ai.command.{mod}")
            table.add_row(mod, "Core", "[green]OK[/green]")
        except Exception as e:
            table.add_row(mod, "Core", f"[red]Error: {e}[/red]")

    # 2. Check Registry Extensions
    details = registry.list_all_details()
    for item in details:
        name = item["name"]
        path = item["path"]
        try:
            module = registry._load_extension(name, path)
            if module:
                # Deep validation of metadata
                missing = []
                if not hasattr(module, "version"):
                    missing.append("version")
                if not hasattr(module, "description"):
                    missing.append("description")
                if not hasattr(module, "dependencies"):
                    missing.append("dependencies")
                
                if missing:
                    table.add_row(name, "Registry", f"[yellow]Missing: {', '.join(missing)}[/yellow]")
                else:
                    table.add_row(name, "Registry", "[green]OK[/green]")
            else:
                table.add_row(name, "Registry", "[red]Failed to load[/red]")
        except Exception as e:
            table.add_row(name, "Registry", f"[red]Error: {e}[/red]")

    # 3. Check Pip Extensions
    eps = entry_points().select(group="cloudmesh.ai.command")
    for ep in eps:
        try:
            module_path, func_name = ep.value.rsplit(":", 1)
            mod = importlib.import_module(module_path)
            getattr(mod, func_name)
            table.add_row(ep.name, "Pip", "[green]OK[/green]")
        except Exception as e:
            table.add_row(ep.name, "Pip", f"[red]Error: {e}[/red]")

    console.print(table)

@entry_point.command(name="manage")
def manage_plugins():
    """Interactively enable or disable plugins."""
    details = registry.list_all_details()
    if not details:
        console.print("[yellow]No plugins registered to manage.[/yellow]")
        return

    while True:
        table = Table(title="Plugin Management", box=box.ROUNDED)
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")

        for idx, item in enumerate(details):
            status = "[green]Active[/green]" if item["active"] else "[red]Inactive[/red]"
            table.add_row(str(idx), item["name"], status)

        console.print(table)
        console.print("\n[bold]Options:[/bold]")
        console.print("  [cyan]<id>[/cyan] : Toggle plugin status")
        console.print("  [cyan]q[/cyan]   : Quit")

        choice = Prompt.ask("Enter ID to toggle or 'q' to quit")

        if choice.lower() == 'q':
            break

        try:
            idx = int(choice)
            if 0 <= idx < len(details):
                plugin_name = details[idx]["name"]
                current_status = details[idx]["active"]
                new_status = not current_status
                
                if registry.set_status(plugin_name, new_status):
                    status_text = "enabled" if new_status else "disabled"
                    console.print(f"[green]Successfully {status_text} {plugin_name}[/green]")
                    # Refresh details for the next loop
                    details = registry.list_all_details()
                else:
                    console.print(f"[red]Error updating status for {plugin_name}[/red]")
            else:
                console.print("[red]Invalid ID.[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number or 'q'.[/red]")

@entry_point.command(name="init")
@click.argument("name")
@click.option("--flavor", type=click.Choice(["default", "benchmark", "sysinfo"]), default="default", help="Template flavor for the plugin.")
def init_plugin(name, flavor):
    """Scaffold a new CMC plugin directory structure."""
    plugin_dir = Path(name).absolute()
    
    if plugin_dir.exists():
        console.print(f"[red]Error: Directory {plugin_dir} already exists.[/red]")
        sys.exit(1)

    # Flavor-specific templates
    templates = {
        "default": {
            "cmd.py": (
                "import click\n\n"
                "version = '0.1.0'\n"
                "description = 'A new CMC plugin'\n"
                "dependencies = []\n\n"
                "@click.command()\n"
                "def entry_point():\n"
                "    \"\"\"Main entry point for the plugin.\"\"\"\n"
                "    click.echo('Hello from the new plugin!')\n\n"
                "def register(cli):\n"
                "    \"\"\"Register complex command groups here.\"\"\"\n"
                "    # Example: \n"
                "    # @cli.group(name='myplugin')\n"
                "    # def group(): pass\n"
                "    # group.add_command(entry_point)\n"
                "    pass\n"
            ),
        },
        "benchmark": {
            "cmd.py": (
                "import click\n"
                "import time\n\n"
                "version = '0.1.0'\n"
                "description = 'A CMC benchmark plugin'\n"
                "dependencies = []\n\n"
                "@click.command()\n"
                "def entry_point():\n"
                "    \"\"\"Run a performance benchmark.\"\"\"\n"
                "    click.echo('Starting benchmark...')\n"
                "    start = time.perf_counter()\n"
                "    # TODO: Implement benchmark logic\n"
                "    time.sleep(1)\n"
                "    end = time.perf_counter()\n"
                "    click.echo(f'Benchmark completed in {end - start:.4f} seconds')\n"
            ),
        },
        "sysinfo": {
            "cmd.py": (
                "import click\n"
                "import platform\n"
                "import os\n\n"
                "version = '0.1.0'\n"
                "description = 'A CMC system info plugin'\n"
                "dependencies = []\n\n"
                "@click.command()\n"
                "def entry_point():\n"
                "    \"\"\"Display system information.\"\"\"\n"
                "    click.echo(f'OS: {platform.system()} {platform.release()}')\n"
                "    click.echo(f'Processor: {platform.processor()}')\n"
                "    click.echo(f'Current User: {os.getlogin()}')\n"
            ),
        }
    }

    selected_template = templates.get(flavor)
    
    # Common structure
    structure = {
        "cmd.py": selected_template["cmd.py"],
        "VERSION": "0.1.0\n",
        "README.md": (
            f"# {name}\n\n"
            f"## Description\n"
            f"This is a {flavor} flavor CMC plugin.\n\n"
            f"## Installation\n"
            f"1. Clone this directory to your plugins folder\n"
            f"2. Run `cmc plugins add /path/to/{name}`\n\n"
            f"## Usage\n"
            f"```bash\n"
            f"cmc {name} [options]\n"
            f"```\n\n"
            f"## Configuration\n"
            f"Configure this plugin via `cmc config set`.\n"
        ),
        "src/__init__.py": "",
        "tests/__init__.py": "",
        "tests/test_plugin.py": (
            "import pytest\n"
            "from click.testing import CliRunner\n"
            "from cmd import entry_point\n\n"
            "def test_entry_point():\n"
            "    runner = CliRunner()\n"
            "    result = runner.invoke(entry_point)\n"
            "    assert result.exit_code == 0\n"
            "    assert 'Hello' in result.output\n"
        ),
    }

    try:
        for path_str, content in structure.items():
            full_path = plugin_dir / path_str
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        console.print(Panel(f"[bold green]Successfully scaffolded {flavor} plugin '{name}'[/bold green]\n\n"
                            f"Location: {plugin_dir}\n\n"
                            f"Next steps:\n"
                            f"1. cd {name}\n"
                            f"2. Edit cmd.py to implement your logic\n"
                            f"3. Run 'cmc plugins add .'", 
                            title=f"Plugin Created ({flavor})"))
    except Exception as e:
        console.print(f"[red]Error creating plugin structure: {e}[/red]")
        sys.exit(1)

@entry_point.command(name="check-deps")
def check_deps():
    """Verify if all dependencies for registered plugins are installed and active."""
    details = registry.list_all_details()
    if not details:
        console.print("[yellow]No plugins registered to check dependencies for.[/yellow]")
        return

    table = Table(title="Plugin Dependency Check", box=box.ROUNDED)
    table.add_column("Plugin", style="cyan")
    table.add_column("Dependency", style="magenta")
    table.add_column("Status", style="green")

    for item in details:
        name = item["name"]
        path = item["path"]
        try:
            module = registry._load_extension(name, path)
            deps = getattr(module, "dependencies", [])
            if not deps:
                table.add_row(name, "None", "[dim]N/A[/dim]")
                continue
            
            for dep in deps:
                # Check if dependency is in registry and active
                dep_details = next((d for d in details if d["name"] == dep), None)
                if dep_details and dep_details["active"]:
                    status = "[green]OK[/green]"
                elif dep_details:
                    status = "[yellow]Inactive[/yellow]"
                else:
                    status = "[red]Missing[/red]"
                table.add_row(name, dep, status)
        except Exception as e:
            table.add_row(name, "N/A", f"[red]Error loading plugin: {e}[/red]")

    console.print(table)

@entry_point.command(name="docs")
@click.option("--output", "-o", default="cloudmesh-ai.github.io/sphinx-docs/plugins_gallery.rst", help="Output path for the plugin gallery RST file.")
def generate_plugin_docs(output):
    """Automatically generate documentation for all registered plugins and a developer guide."""
    details = registry.list_all_details()
    
    # 1. Generate Plugin Gallery
    if details:
        try:
            with open(output, "w") as f:
                f.write("Plugin Gallery\n")
                f.write("=============\n\n")
                f.write("This page provides an overview of all registered CMC plugins.\n\n")
                
                for item in details:
                    name = item["name"]
                    path = item["path"]
                    try:
                        module = registry._load_extension(name, path)
                        if module:
                            description = getattr(module, "description", "No description provided.")
                            version = getattr(module, "version", "unknown")
                            entry_point_func = getattr(module, "entry_point", None)
                            docstring = entry_point_func.__doc__ if entry_point_func and entry_point_func.__doc__ else "No detailed documentation provided."
                            
                            f.write(f"{name}\n")
                            f.write("-" * len(name) + "\n")
                            f.write(f"**Version:** {version}\n\n")
                            f.write(f"**Description:** {description}\n\n")
                            f.write(f"**Details:**\n\n    {docstring}\n\n")
                            f.write("\n")
                        else:
                            f.write(f"{name}\n")
                            f.write("-" * len(name) + "\n")
                            f.write("Failed to load plugin for documentation.\n\n")
                    except Exception as e:
                        f.write(f"{name}\n")
                        f.write("-" * len(name) + "\n")
                        f.write(f"Error extracting documentation: {e}\n\n")
            console.print(f"[green]Successfully generated plugin gallery at {output}[/green]")
        except Exception as e:
            console.print(f"[red]Error writing gallery: {e}[/red]")
    else:
        console.print("[yellow]No plugins registered. Skipping gallery generation.[/yellow]")

    # 2. Generate Developer Guide
    dev_guide_path = Path(output).parent / "developer_guide.rst"
    try:
        with open(dev_guide_path, "w") as f:
            f.write("CMC Plugin Developer Guide\n")
            f.write("========================\n\n")
            f.write("This guide explains how to create and integrate plugins into the Cloudmesh AI CMC.\n\n")
            
            f.write("Plugin Architecture\n")
            f.write("------------------\n\n")
            f.write("CMC plugins are Python packages or directories that provide a `register()` function "
                    "and an `entry_point()` command. They are dynamically loaded by the CMC registry.\n\n")
            
            f.write("Required Metadata\n")
            f.write("-----------------\n\n")
            f.write("Every plugin must define the following top-level variables in its main module:\n\n")
            f.write("- **version**: (str) The semantic version of the plugin (e.g., '1.0.0').\n")
            f.write("- **description**: (str) A brief summary of what the plugin does.\n")
            f.write("- **dependencies**: (list) A list of other plugin names that must be active for this plugin to work.\n\n")
            
            f.write("Creating a Plugin\n")
            f.write("-----------------\n\n")
            f.write("The easiest way to start is using the built-in scaffolding command:\n\n")
            f.write(".. code-block:: bash\n\n    cmc plugins init my-plugin --flavor default\n\n")
            f.write("This creates a directory with a template `cmd.py`, `VERSION`, and a test suite.\n\n")
            
            f.write("Registration\n")
            f.write("------------\n\n")
            f.write("To add your plugin to the CMC, run:\n\n")
            f.write(".. code-block:: bash\n\n    cmc plugins add /path/to/my-plugin\n\n")
            f.write("You can then verify its health using `cmc plugins check`.\n")
            
        console.print(f"[green]Successfully generated developer guide at {dev_guide_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error writing developer guide: {e}[/red]")

@entry_point.command(name="test")
@click.argument("name")
def test_plugin(name):
    """Run tests for a specific registered plugin."""
    details = registry.list_all_details()
    plugin = next((item for item in details if item["name"] == name), None)
    
    if not plugin:
        console.print(f"[red]Error: Plugin '{name}' not found in registry.[/red]")
        sys.exit(1)
    
    plugin_path = Path(plugin["path"])
    test_dir = plugin_path / "tests"
    
    if not test_dir.exists() or not any(test_dir.iterdir()):
        console.print(f"[yellow]No tests found in {test_dir}. Skipping.[/yellow]")
        return

    console.print(f"Running tests for plugin [bold cyan]{name}[/bold cyan]...")
    
    try:
        # Run pytest on the plugin's test directory
        result = subprocess.run(
            ["pytest", str(test_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print(f"[green]Tests passed for {name}![/green]")
        else:
            console.print(f"[red]Tests failed for {name}:[/red]\n{result.stdout}\n{result.stderr}")
            sys.exit(result.returncode)
    except Exception as e:
        console.print(f"[red]Error running tests: {e}[/red]")
        sys.exit(1)
