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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from cloudmesh.ai.cmc.context import config, telemetry_enabled
from cloudmesh.ai.cmc.utils import handle_errors

def check_system_dependency(command: list):
    """Runs a system command and returns (success, output)."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

@click.command(name="doctor")
@handle_errors
def doctor():
    """Perform a comprehensive health check of the CMC environment."""
    console = Console()
    console.print(Panel("[bold blue]CMC Doctor: System Diagnostic[/bold blue]"))

    # 1. Check Configuration
    console.print("\n[bold]1. Configuration Check[/bold]")
    if config.path.exists():
        console.print(f"  [green]✓[/green] Config file found at {config.path}")
    else:
        console.print(f"  [yellow]![yellow] Using default configuration (no file at {config.path})")

    # 2. Check Telemetry
    console.print("\n[bold]2. Telemetry Check[/bold]")
    t_path = os.path.expanduser(config.get("telemetry.path", "~/cmc_telemetry.jsonl"))
    try:
        if telemetry_enabled:
            # Check if we can write to the telemetry path
            with open(t_path, "a") as f:
                f.write("")
            console.print(f"  [green]✓[/green] Telemetry enabled and writable at {t_path}")
        else:
            console.print("  [blue]i[/blue] Telemetry is disabled in config")
    except Exception as e:
        console.print(f"  [red]✗[/red] Telemetry path not writable: {e}")

    # 3. Check Extensions (Reuse plugin check logic)
    console.print("\n[bold]3. Extension Health Check[/bold]")
    ext_table = Table(show_header=True, header_style="bold magenta")
    ext_table.add_column("Extension")
    ext_table.add_column("Version")
    ext_table.add_column("Source")
    ext_table.add_column("Status")

    # Core
    try:
        from importlib.metadata import version as get_version
        core_version = get_version("cloudmesh-ai-cmc")
    except Exception:
        core_version = "Unknown"

    core_modules = ["banner", "tree", "man", "command", "docs", "doctor", "plugins", "telemetry", "config", "version", "shell", "completion"]
    for mod in core_modules:
        try:
            importlib.import_module(f"cloudmesh.ai.command.{mod}")
            status = "[green]OK[/green]" if core_version != "Unknown" else "[yellow]Warning: Missing Version[/yellow]"
            ext_table.add_row(mod, core_version, "Core", status)
        except Exception as e:
            ext_table.add_row(mod, core_version, "Core", f"[red]Error: {e}[/red]")


    # Pip
    eps = entry_points().select(group="cloudmesh.ai.command")
    for ep in eps:
        try:
            module_path, func_name = ep.value.rsplit(":", 1)
            mod = importlib.import_module(module_path)
            getattr(mod, func_name)
            version = getattr(mod, "version", "Unknown")
            status = "[green]OK[/green]" if version != "Unknown" else "[yellow]Warning: Missing Version[/yellow]"
            ext_table.add_row(ep.name, version, "Pip", status)
        except Exception as e:
            ext_table.add_row(ep.name, "Unknown", "Pip", f"[red]Error: {e}[/red]")

    console.print(ext_table)


    # 4. Environment Check
    console.print("\n[bold]4. Environment Check[/bold]")
    console.print(f"  Python Version: {sys.version.split()[0]}")
    console.print(f"  Platform: {sys.platform}")

    # Connectivity Check
    console.print("\n[bold]5. Connectivity Check[/bold]")
    # Check connectivity to a reliable host to ensure network access for AI backends
    net_ok, net_out = check_system_dependency(["curl", "-Is", "https://www.google.com", "--connect-timeout", "5"])
    if net_ok:
        console.print("  [green]✓[/green] Network connectivity verified (reachable: google.com)")
    else:
        console.print("  [red]✗[/red] Network connectivity issue: Unable to reach google.com")

    # GPU / CUDA Checks
    console.print("\n[bold]5. AI Hardware & Software Check[/bold]")
    
    # NVIDIA GPU
    gpu_ok, gpu_out = check_system_dependency(["nvidia-smi", "-L"])
    if gpu_ok:
        console.print(f"  [green]✓[/green] NVIDIA GPU detected: {gpu_out.splitlines()[0]}")
    else:
        console.print("  [yellow]![yellow] No NVIDIA GPU detected via nvidia-smi")

    # CUDA
    cuda_ok, cuda_out = check_system_dependency(["nvcc", "--version"])
    if cuda_ok:
        # Extract version from output like "Cuda compilation tools, release 12.1..."
        version_line = [l for l in cuda_out.splitlines() if "release" in l]
        version = version_line[0] if version_line else "Detected"
        console.print(f"  [green]✓[/green] CUDA Toolkit found: {version}")
    else:
        console.print("  [yellow]![yellow] CUDA Toolkit (nvcc) not found in PATH")

    # PyTorch
    try:
        import torch
        torch_ver = torch.__version__
        cuda_avail = torch.cuda.is_available()
        status = "[green]OK[/green]" if cuda_avail else "[yellow]CPU only[/yellow]"
        console.print(f"  [green]✓[/green] PyTorch {torch_ver} installed ({status})")
    except ImportError:
        console.print("  [blue]i[/blue] PyTorch not installed")

    # Docker
    docker_ok, docker_out = check_system_dependency(["docker", "--version"])
    if docker_ok:
        console.print(f"  [green]✓[/green] Docker detected: {docker_out.splitlines()[0]}")
    else:
        console.print("  [yellow]![yellow] Docker not found in PATH")
    
    console.print("\n[bold green]Diagnostic Complete.[/bold green]")

entry_point = doctor