# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
import click
import json
import os
import time
from cloudmesh.ai.cmc.utils import console
from rich.table import Table

STOPWATCH_FILE = os.path.expanduser("~/.cmc_stopwatches.json")

def load_stopwatches():
    """Loads stopwatches from the persistence file."""
    if not os.path.exists(STOPWATCH_FILE):
        return {"timers": {}, "order": []}
    try:
        with open(STOPWATCH_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"timers": {}, "order": []}

def save_stopwatches(data):
    """Saves stopwatches to the persistence file."""
    try:
        with open(STOPWATCH_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        console.print(f"[red]Error saving stopwatches: {e}[/red]")

def _start_timer(name):
    """Internal helper to start a timer.
    
    The 'sum' field acts as the accumulator for all previous segments (the 'original time').
    The 'start' and 'end' fields track the current active segment (the 'new timer').
    """
    data = load_stopwatches()
    
    if name is None:
        # Auto-generate name: timer-N where N is last timer number + 1
        max_n = 0
        for timer_name in data["timers"]:
            if timer_name.startswith("timer-"):
                try:
                    n = int(timer_name.split("-")[1])
                    max_n = max(max_n, n)
                except (ValueError, IndexError):
                    pass
        name = f"timer-{max_n + 1}"
        console.print(f"No name provided, using auto-generated name: [bold]{name}[/bold]")

    if name in data["timers"]:
        timer = data["timers"][name]
        # If it's currently running, close the current segment and add to sum
        if timer["end"] is None:
            elapsed = time.time() - timer["start"]
            data["timers"][name]["sum"] += elapsed
        
        console.print(f"Resuming stopwatch [bold]{name}[/bold].")
    else:
        data["timers"][name] = {"start": 0.0, "end": None, "sum": 0.0, "status": None}
        data["order"].append(name)

    # Start a new segment
    data["timers"][name]["start"] = time.time()
    data["timers"][name]["end"] = None
    save_stopwatches(data)
    console.print(f"[green]Stopwatch [bold]{name}[/bold] started.[/green]")

@click.group(name="time")
def time_group():
    """Stopwatch commands to measure execution time across sessions."""
    pass

@time_group.command(name="start")
@click.argument("name", required=False)
def start(name):
    """Starts a stopwatch with the given name. If no name is provided, it is auto-generated.
    Existing timers are resumed.
    """
    _start_timer(name)

@time_group.command(name="+")
@click.argument("name", required=False)
def start_alias(name):
    """Alias for start: starts a stopwatch with the given name. If no name is provided, it is auto-generated.
    Existing timers are resumed.
    """
    _start_timer(name)

@time_group.command(name="stop")
@click.argument("identifier", required=False)
def stop(identifier):
    """Stops a stopwatch. If no identifier is provided, stops the last started stopwatch.
    Identifier can be the timer name or its index from the list.
    """
    _stop_timer(identifier)

@time_group.command(name="-")
@click.argument("identifier", required=False)
def stop_alias(identifier):
    """Alias for stop."""
    _stop_timer(identifier)
def _stop_timer(identifier):
    """Internal helper to stop a timer."""
    data = load_stopwatches()
    
    if identifier is None:
        running_timers = [n for n in data["order"] if data["timers"][n]["end"] is None]
        if not running_timers:
            console.print("[red]No running stopwatches found.[/red]")
            return
        name = running_timers[-1]
        console.print(f"No identifier provided, stopping last started stopwatch: [bold]{name}[/bold]")
    else:
        if identifier.isdigit():
            idx = int(identifier) - 1
            if 0 <= idx < len(data["order"]):
                name = data["order"][idx]
                console.print(f"Using index {identifier}, resolving to stopwatch: [bold]{name}[/bold]")
            else:
                console.print(f"[red]Index [bold]{identifier}[/bold] is out of range.[/red]")
                return
        else:
            name = identifier

    if name not in data["timers"] or data["timers"][name]["end"] is not None:
        console.print(f"[red]Stopwatch [bold]{name}[/bold] not found or not running.[/red]")
        return

    timer = data["timers"][name]
    end_time = time.time()
    elapsed = end_time - timer["start"]
    timer["end"] = end_time
    timer["sum"] += elapsed
    timer["status"] = "ok"
    save_stopwatches(data)
    console.print(f"[green]Stopwatch [bold]{name}[/bold] stopped. Elapsed time: [bold]{elapsed:.4f}[/bold] s[/green]")

@time_group.command(name="rm")
@click.argument("identifier")
def remove(identifier):
    """Removes a stopwatch by name or index."""
    data = load_stopwatches()
    
    if identifier.isdigit():
        idx = int(identifier) - 1
        if 0 <= idx < len(data["order"]):
            name = data["order"][idx]
        else:
            console.print(f"[red]Index [bold]{identifier}[/bold] is out of range.[/red]")
            return
    else:
        name = identifier

    if name not in data["timers"]:
        console.print(f"[red]Stopwatch [bold]{name}[/bold] not found.[/red]")
        return

    del data["timers"][name]
    data["order"].remove(name)
    save_stopwatches(data)
    console.print(f"[yellow]Stopwatch [bold]{name}[/bold] removed.[/yellow]")

@time_group.command(name="clean")
def clean():
    """Erases all stopwatches."""
    _clean_timers()

@time_group.command(name="c")
def clean_alias():
    """Alias for clean."""
    _clean_timers()

def _clean_timers():
    save_stopwatches({"timers": {}, "order": []})
    console.print("[yellow]All stopwatches cleared.[/yellow]")

@time_group.command(name="list")
def list_timers():
    """Lists all stopwatches and their elapsed times."""
    _list_timers()

@time_group.command(name="=")
@click.argument("identifier", required=False)
def print_timer_time(identifier):
    """Prints the time of a specific timer. 
    If no identifier is provided, prints the last timer.
    Identifier can be the timer name or its index.
    """
    data = load_stopwatches()
    if not data["order"]:
        console.print("[red]No stopwatches recorded.[/red]")
        return

    if identifier is None:
        name = data["order"][-1]
    elif identifier.isdigit():
        idx = int(identifier) - 1
        if 0 <= idx < len(data["order"]):
            name = data["order"][idx]
        else:
            console.print(f"[red]Index [bold]{identifier}[/bold] is out of range.[/red]")
            return
    else:
        name = identifier

    if name not in data["timers"]:
        console.print(f"[red]Stopwatch [bold]{name}[/bold] not found.[/red]")
        return

    timer = data["timers"][name]
    if timer["end"] is not None:
        elapsed = timer["end"] - timer["start"]
        status = "Stopped"
    else:
        elapsed = time.time() - timer["start"]
        status = "Running"
    
    console.print(f"Stopwatch [bold]{name}[/bold] ({status}): [green][bold]{elapsed:.4f}[/bold][/green] s")

def _list_timers():
    data = load_stopwatches()
    timers = data["timers"]
    
    if not timers:
        console.print("No stopwatches recorded.")
        return

    table = Table(title="Stopwatches")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="cyan")
    table.add_column("Last Elapsed (s)", style="magenta")
    table.add_column("Total Sum (s)", style="green")
    table.add_column("Status", style="yellow")

    for i, name in enumerate(data["order"], 1):
        timer = timers[name]
        if timer["end"] is not None:
            last_elapsed = timer["end"] - timer["start"]
            status = "Stopped"
        else:
            last_elapsed = time.time() - timer["start"]
            status = "Running"
        
        table.add_row(
            str(i),
            name, 
            f"{last_elapsed:.4f}", 
            f"{timer['sum']:.4f}", 
            status
        )

    console.print(table)

# Export the group for registration
cli = time_group