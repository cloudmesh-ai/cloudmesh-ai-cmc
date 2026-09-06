# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import click
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from cloudmesh.ai.cmc.utils import Config, console
from cloudmesh.ai.common.io import path_expand
from cloudmesh.ai.common.aggregation import TelemetryAggregator
from rich.table import Table
from rich import box

@click.group(name="telemetry")
def telemetry_group():
    """Manage and view AI telemetry data."""
    pass

@telemetry_group.command(name="on")
def telemetry_on():
    """Enable telemetry collection."""
    config = Config()
    config.set("telemetry.enabled", True)
    config.save()
    console.print("[bold green]Telemetry has been enabled.[/bold green]")

@telemetry_group.command(name="off")
def telemetry_off():
    """Disable telemetry collection."""
    config = Config()
    config.set("telemetry.enabled", False)
    config.save()
    console.print("[bold green]Telemetry has been disabled.[/bold green]")

@telemetry_group.command(name="list")
@click.option("--command", type=str, help="Filter by command name")
@click.option("--status", type=str, help="Filter by status (e.g., completed, failed)")
@click.option("--since", type=int, help="Filter records from the last N days")
@click.option("--export", type=click.Choice(["json", "csv"]), help="Export filtered results to a file")
def telemetry_list(command, status, since, export):
    """List and filter telemetry records."""
    # Default telemetry DB path
    db_path = Path(path_expand("telemetry.db"))
    if not db_path.exists():
        console.print("[yellow]No telemetry database found at telemetry.db[/yellow]")
        return

    agg = TelemetryAggregator(db_path)
    records = agg.records

    if not records:
        console.print("[yellow]No telemetry records found.[/yellow]")
        return

    # Filtering
    filtered_records = []
    now = datetime.now()

    for r in records:
        # Filter by command
        if command and r.get("command") != command:
            continue
        
        # Filter by status
        if status and r.get("status", "").lower() != status.lower():
            continue
        
        # Filter by since (days)
        if since:
            ts_str = r.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < now - timedelta(days=since):
                        continue
                except ValueError:
                    continue
            else:
                continue
        
        filtered_records.append(r)

    if not filtered_records:
        console.print("[yellow]No records matched the filters.[/yellow]")
        return

    if export == "json":
        out_file = "telemetry_export.json"
        with open(out_file, "w") as f:
            json.dump(filtered_records, f, indent=4)
        console.print(f"[green]Exported {len(filtered_records)} records to {out_file}[/green]")
        return

    if export == "csv":
        out_file = "telemetry_export.csv"
        if filtered_records:
            keys = filtered_records[0].keys()
            with open(out_file, "w", newline="") as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(filtered_records)
        console.print(f"[green]Exported {len(filtered_records)} records to {out_file}[/green]")
        return

    # Display as Rich Table
    table = Table(
        title="Telemetry Records",
        box=box.ROUNDED,
        header_style="bold magenta"
    )
    
    table.add_column("Timestamp", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Message", style="white")

    for r in filtered_records:
        table.add_row(
            r.get("timestamp", "N/A"),
            r.get("command", "unknown"),
            r.get("status", "unknown").upper(),
            r.get("message", "")
        )

    console.print(table)
