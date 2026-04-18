# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import click
import sys
from rich.console import Console
from rich.table import Table

from cloudmesh.ai.cmc.context import config

@click.group(name="config")
def entry_point():
    """Manage CMC configuration."""
    pass

@entry_point.command(name="get")
@click.argument("key")
def config_get(key):
    """Retrieve a configuration value. Supports dot-notation (e.g., 'telemetry.enabled')."""
    val = config.get(key)
    if val is not None:
        click.echo(val)
    else:
        click.echo(f"Key '{key}' not found in configuration.", err=True)
        click.echo("Tip: Use 'cmc config list' to see all available keys.", err=True)
        sys.exit(1)

@entry_point.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Update a configuration value. Supports dot-notation (e.g., 'myplugin.api_key')."""
    # Robust type casting
    val_lower = value.lower()
    if val_lower == "true":
        casted_value = True
    elif val_lower == "false":
        casted_value = False
    elif value.isdigit():
        casted_value = int(value)
    else:
        try:
            casted_value = float(value)
        except ValueError:
            casted_value = value
    
    try:
        config.set(key, casted_value)
        config.save()
        click.echo(f"Successfully set {key} = {casted_value}")
    except Exception as e:
        click.echo(f"Configuration Error: {e}", err=True)
        sys.exit(1)

@entry_point.command(name="list")
def config_list():
    """Show all current configurations."""
    console = Console()
    table = Table(title="CMC Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    
    def flatten_config(d, prefix=""):
        for k, v in d.items():
            key = f"{prefix}{k}"
            if isinstance(v, dict):
                flatten_config(v, f"{key}.")
            else:
                table.add_row(key, str(v))
    
    flatten_config(config.data)
    console.print(table)