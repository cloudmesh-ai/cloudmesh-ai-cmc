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


console = Console()

@click.command(name="version")
def entry_point():
    """Display the current version of cmc and active extensions."""
    try:
        core_version = get_version("cloudmesh-ai-cmc")
    except Exception:
        core_version = "Unknown"

    console.print(f"[bold blue]cmc version {core_version}[/bold blue]\n")

