import click
from rich.console import Console
from rich.table import Table
from rich import box
from cloudmesh.ai.common import sys as ai_sys


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
        # Use the improved systeminfo from cloudmesh.ai.common
        info = ai_sys.systeminfo()

        table = Table(
            title="CME System Information",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
        )

        table.add_column("Attribute", style="blue", width=25)
        table.add_column("Value", style="white")

        # Sort keys for consistent display
        for key in sorted(info.keys()):
            # Make keys more readable (e.g., uname.system -> Uname System)
            label = key.replace('.', ' ').replace('_', ' ').title()
            table.add_row(label, str(info[key]))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error gathering system info: {e}[/red]")


def register(group):
    """Registers the info command to the 'sys' group."""
    group.add_command(sys_info)
