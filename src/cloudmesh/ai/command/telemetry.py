# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import click
import os
import json
import csv
from collections import Counter
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cloudmesh.ai.cmc.context import config, logger

console = Console()

@click.command(name="telemetry")
@click.option("--command", help="Filter by command name")
@click.option("--status", help="Filter by status (e.g., SUCCESS, FAILURE)")
@click.option("--since", type=int, help="Filter records from the last N days")
@click.option("--export", type=click.Choice(["json", "csv"]), help="Export filtered results to a file")
def entry_point(command, status, since, export):
    """Analyze CMC telemetry data."""
    t_path = os.path.expanduser(config.get("telemetry.path", "~/cmc_telemetry.jsonl"))
    if not os.path.exists(t_path):
        console.print(f"[red]No telemetry file found at {t_path}[/red]")
        return

    records = []
    with open(t_path, "r") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not records:
        console.print("No telemetry records found.")
        return

    # Filtering
    filtered = records
    if command:
        filtered = [r for r in filtered if r.get("command") == command]
    if status:
        filtered = [r for r in filtered if r.get("status") == status]
    if since:
        cutoff = datetime.now() - timedelta(days=since)
        filtered = [r for r in filtered if r.get("timestamp") and datetime.fromisoformat(r["timestamp"]) >= cutoff]

    if not filtered:
        console.print("[yellow]No records match the specified filters.[/yellow]")
        return

    if export:
        filename = f"telemetry_export.{export}"
        if export == "json":
            with open(filename, "w") as f:
                json.dump(filtered, f, indent=4)
        elif export == "csv":
            if filtered:
                keys = filtered[0].keys()
                with open(filename, "w", newline="") as f:
                    dict_writer = csv.DictWriter(f, fieldnames=keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(filtered)
        console.print(f"[green]Exported {len(filtered)} records to {filename}[/green]")
        return

    # Aggregations on filtered set
    total = len(filtered)
    statuses = Counter([r["status"] for r in filtered])
    commands_counts = Counter([r["command"] for r in filtered])
    
    # Command-specific metrics
    cmd_metrics = {} # {cmd_name: {'durations': [], 'failures': 0, 'total': 0}}
    
    for r in filtered:
        cmd_name = r.get("command", "unknown")
        if cmd_name not in cmd_metrics:
            cmd_metrics[cmd_name] = {'durations': [], 'failures': 0, 'total': 0}
        
        cmd_metrics[cmd_name]['total'] += 1
        if r.get("status") == "FAILURE":
            cmd_metrics[cmd_name]['failures'] += 1
        
        dur = r.get("metrics", {}).get("duration_sec")
        if dur:
            cmd_metrics[cmd_name]['durations'].append(dur)

    all_durations = [d for m in cmd_metrics.values() for d in m['durations']]
    avg_dur = sum(all_durations) / len(all_durations) if all_durations else 0

    # Display
    title = "Telemetry Summary" if not (command or status or since) else "Filtered Telemetry Summary"
    console.print(Panel(f"[bold blue]{title}[/bold blue]\nTotal Events: {total}\nAvg Duration: {avg_dur:.4f}s", expand=False))
    
    status_table = Table(title="Status Distribution")
    status_table.add_column("Status")
    status_table.add_column("Count")
    for s, c in statuses.items():
        status_table.add_row(s, str(c))
    console.print(status_table)

    # Enhanced Command Analytics Table
    cmd_table = Table(title="Command Performance & Reliability")
    cmd_table.add_column("Command", style="cyan")
    cmd_table.add_column("Calls", style="magenta")
    cmd_table.add_column("Avg Duration", style="green")
    cmd_table.add_column("Error Rate", style="red")

    # Sort by most used
    sorted_cmds = sorted(cmd_metrics.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
    for cmd_name, m in sorted_cmds:
        avg = sum(m['durations']) / len(m['durations']) if m['durations'] else 0
        err_rate = (m['failures'] / m['total']) * 100 if m['total'] > 0 else 0
        cmd_table.add_row(
            cmd_name, 
            str(m['total']), 
            f"{avg:.4f}s", 
            f"{err_rate:.1f}%"
        )
    console.print(cmd_table)