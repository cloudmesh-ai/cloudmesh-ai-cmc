import click
import platform
import os
from rich.console import Console
from rich.table import Table
from rich import box


console = Console()


@click.command(name="info")
def sys_info():
    """
    Display a comprehensive summary of the current system environment.

    This command aggregates hardware, OS, and Python environment details into
    a formatted table for quick diagnostics.

    Information included:
    1. OS Details: Distribution, Kernel version, and Architecture.
    2. Hardware: Processor, Node name, and Machine type.
    3. Environment: Current working directory and User.

    Examples:
        cme sys info
    """
    try:
        # IDENTICAL STYLE CONFIGURATION
        table = Table(
            title="CME System Information",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
        )

        # Column 1: Cyan and width=20 for alignment
        table.add_column("Attribute", style="blue", width=20)
        # Column 2: White/Default for the value
        table.add_column("Value", style="black")

        # Data gathering
        table.add_row("OS", f"{platform.system()} {platform.release()}")
        table.add_row("Version", platform.version())
        table.add_row("Architecture", platform.machine())
        table.add_row("Processor", platform.processor())
        table.add_row("Node", platform.node())
        table.add_row("User", os.getlogin())
        table.add_row("CWD", os.getcwd())
        table.add_row("Python", platform.python_version())

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error gathering system info: {e}[/red]")


def register(group):
    """Registers the info command to the 'sys' group."""
    group.add_command(sys_info)
