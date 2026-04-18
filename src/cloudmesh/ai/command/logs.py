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
from collections import defaultdict
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from cloudmesh.ai.cmc.context import config

console = Console()

@click.command(name="logs")
@click.option("--command", help="Filter by command name")
@click.option("--status", help="Filter by status (e.g., SUCCESS, FAILURE)")
@click.option("--since", type=int, help="Filter records from the last N days")
@click.option("--limit", type=int, default=100, help="Limit the number of records displayed (default: 100)")
@click.option("--format", "-f", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format for the logs.")
@click.option("--summary", is_flag=True, help="Show a summary of command performance and failure rates.")
def entry_point(command, status, since, limit, format, summary):
    """View, filter, and analyze CMC telemetry logs."""
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

    # Take the last N records (most recent)
    display_records = filtered[-limit:]
    if len(filtered) > limit:
        console.print(f"[dim]Showing last {limit} of {len(filtered)} records...[/dim]")

    if summary:
        stats = defaultdict(lambda: {"count": 0, "success": 0, "failure": 0, "total_time": 0.0})
        for r in filtered:
            cmd_name = r.get("command", "unknown")
            status_val = r.get("status", "UNKNOWN")
            duration = r.get("metrics", {}).get("duration_sec", 0)
            
            stats[cmd_name]["count"] += 1
            stats[cmd_name]["total_time"] += duration
            if status_val == "SUCCESS":
                stats[cmd_name]["success"] += 1
            elif status_val == "FAILURE":
                stats[cmd_name]["failure"] += 1

        summary_table = Table(title="Telemetry Summary", box=box.ROUNDED, header_style="bold magenta")
        summary_table.add_column("Command", style="cyan")
        summary_table.add_column("Runs", justify="right")
        summary_table.add_column("Success Rate", justify="right")
        summary_table.add_column("Avg Duration", justify="right")

        for cmd_name, s in stats.items():
            rate = (s["success"] / s["count"]) * 100 if s["count"] > 0 else 0
            avg = s["total_time"] / s["count"] if s["count"] > 0 else 0
            summary_table.add_row(
                cmd_name, 
                str(s["count"]), 
                f"{rate:.1f}%", 
                f"{avg:.4f}s"
            )
        console.print(summary_table)
        console.print("\n")

    if format == "json":
        print(json.dumps(display_records, indent=2))
    elif format == "csv":
        import sys
        writer = csv.writer(sys.stdout)
        writer.writerow(["timestamp", "command", "status", "duration_sec"])
        for r in display_records:
            writer.writerow([
                r.get("timestamp", "N/A"),
                r.get("command", "unknown"),
                r.get("status", "UNKNOWN"),
                r.get("metrics", {}).get("duration_sec", 0)
            ])
    else:
        # Default Table Display
        table = Table(title="CMC Telemetry Logs", box=box.ROUNDED)
        table.add_column("Timestamp", style="dim")
        table.add_column("Command", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="magenta")

        for r in reversed(display_records): # Show newest first
            status_val = r.get("status", "UNKNOWN")
            status_style = "[green]SUCCESS[/green]" if status_val == "SUCCESS" else "[red]FAILURE[/red]" if status_val == "FAILURE" else status_val
            duration = r.get("metrics", {}).get("duration_sec", 0)
            table.add_row(
                r.get("timestamp", "N/A"),
                r.get("command", "unknown"),
                status_style,
                f"{duration:.4f}s"
            )
        console.print(table)
