# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import click
from importlib.metadata import version as get_version
from rich.console import Console
from rich.table import Table

from cloudmesh.ai.cmc.context import registry

console = Console()

@click.command(name="version")
def entry_point():
    """Display the current version of cmc and active extensions."""
    try:
        core_version = get_version("cloudmesh-ai-cmc")
    except Exception:
        core_version = "Unknown"

    console.print(f"[bold blue]cmc version {core_version}[/bold blue]\n")

    details = registry.list_all_details()
    if not details:
        console.print("No active extensions registered.")
        return

    table = Table(title="Active Extensions")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Path", style="green")

    for item in details:
        table.add_row(item["name"], item["version"], item["path"])

    console.print(table)