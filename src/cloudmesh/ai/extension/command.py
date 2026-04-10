import click
import sys
import inspect
from rich.console import Console
from rich.table import Table
from rich import box
from cloudmesh.ai.extension.man import generate_manual, get_formatter
import os
from pathlib import Path
import re

console = Console()

# ==============================================================================
# COMMAND DEFINITIONS
# All functions starting with 'cmd_' will be automatically registered
# ==============================================================================


@click.command(name="load")
@click.option(
    "--dir", "directory", type=click.Path(exists=True), help="Load from directory"
)
@click.argument("name", required=False)
def cmd_load(name, directory):
    """Register and load a new command."""
    from cloudmesh.ai.main import registry

    if not directory:
        directory = "."
    registry.register(name, directory)
    click.echo(f"Loaded and activated: {name or directory}")


@click.command(name="activate")
@click.argument("name")
def cmd_activate(name):
    """Activate a registered command."""
    from cloudmesh.ai.main import registry

    if registry.set_status(name, True):
        click.echo(f"Activated: {name}")
    else:
        click.echo(f"Error: {name} not found in registry.")


@click.command(name="deactivate")
@click.argument("name")
def cmd_deactivate(name):
    """Deactivate a registered command."""
    from cloudmesh.ai.main import registry

    if registry.set_status(name, False):
        click.echo(f"Deactivated: {name}")
    else:
        click.echo(f"Error: {name} not found in registry.")


@click.command(name="list")
def cmd_list():
    """List all registered commands using a professional Rich table."""
    from cloudmesh.ai.main import registry

    details = registry.list_all_details()

    if not details:
        console.print("[yellow]Registry is empty.[/yellow]")
        return

    # IDENTICAL STYLE CONFIGURATION
    table = Table(
        title="CME Command Registry",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
    )

    # Column 1: Blue for command names
    table.add_column("COMMAND", style="blue", width=30)
    # Column 2: Dim for the version
    table.add_column("VERSION", style="dim")
    # Column 3: Centered status
    table.add_column("STATUS", justify="center")
    # Column 4: Black for paths
    table.add_column("SOURCE PATH", style="black")

    for item in details:
        # Using Rich tags for the status color
        status = "[green]active[/green]" if item["active"] else "[red]inactive[/red]"

        table.add_row(item["name"], item["version"], status, item["path"])

    console.print(table)


@click.command(name="unload")
@click.argument("name")
def cmd_unload(name):
    """Remove a command from the registry."""
    from cloudmesh.ai.main import registry

    registry.unregister(name)
    click.echo(f"Unloaded: {name}")


import os
import re
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


@click.command(name="create")
@click.argument("name")
@click.option(
    "--groups", "-g", multiple=True, help="Additional sub-commands to create."
)
@click.option("--path", "-p", default=".", help="Path to create the extension in.")
def cmd_create(name, groups, path):
    """
    Create or expand a cme extension.
    Example:
        cme command create hello           -> creates root group 'hello'
        cme command create hello -g one    -> adds command 'one' to group 'hello'
    """

    root_name = name
    all_subs = list(groups)

    if not all_subs:
        all_subs = [root_name]

    current_dir = Path(__file__).parent
    templates_dir = current_dir.parent / "templates"
    base_dir = Path(path).expanduser().resolve()
    target_dir = base_dir / f"cloudmesh-ai-{root_name}"
    plugin_file = target_dir / "src" / "cloudmesh" / "ai" / "extension" / f"{root_name}.py"

    # --- CASE 1: EXTENSION EXISTS (APPEND MODE) ---
    if target_dir.exists():
        if not plugin_file.exists():
            console.print(
                f"[red]Error: {target_dir} exists but is not a valid CME extension.[/red]"
            )
            return

        content = plugin_file.read_text()
        existing_cmds = re.findall(
            rf'@{root_name}_group\.command\(name="([^"]+)"\)', content
        )

        new_additions_code = []
        added_names = []

        for sub in all_subs:
            if sub in existing_cmds:
                console.print(
                    f"[yellow]Warning: Command '{sub}' already exists in {root_name}. Skipping.[/yellow]"
                )
            else:
                code = f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} command added via CME."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
                new_additions_code.append(code)
                added_names.append(sub)

        if not added_names:
            console.print("[yellow]No new commands were added.[/yellow]")
            return

        if "def register(cli):" in content:
            parts = content.split("def register(cli):")
            new_content = (
                parts[0] + "".join(new_additions_code) + "def register(cli):" + parts[1]
            )
            plugin_file.write_text(new_content)

            # --- PRINT AS A RICH TABLE ---
            table = Table(
                title=f"Extension Updated: {root_name}",
                box=box.ROUNDED,
                header_style="bold magenta",
            )
            table.add_column("Extension", style="cyan")
            table.add_column("Group/Command", style="white")

            for sub in added_names:
                table.add_row(root_name, sub)

            console.print("\n", table)
        else:
            console.print(
                "[red]Error: Could not find register(cli) function in plugin file.[/red]"
            )
        return

    # --- CASE 2: EXTENSION DOES NOT EXIST (NEW MODE) ---
    try:
        extension_dir = target_dir / "src" / "cloudmesh" / "ai" / "extension"
        extension_dir.mkdir(parents=True, exist_ok=True)

        commands_code_list = []
        for sub in all_subs:
            code = f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} command created by CME."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
            commands_code_list.append(code)

        pyproject_content = (
            (templates_dir / "pyproject.toml.tmpl").read_text().format(name=root_name)
        )
        plugin_content = (
            (templates_dir / "plugin.py.tmpl")
            .read_text()
            .format(root_name=root_name, commands_code="".join(commands_code_list))
        )
        license_content = (templates_dir / "LICENSE.tmpl").read_text()

        (target_dir / "VERSION").write_text("0.1.0")
        (target_dir / "pyproject.toml").write_text(pyproject_content)
        (target_dir / "LICENSE").write_text(license_content)
        plugin_file.write_text(plugin_content)

        # --- PRINT NEW CREATION AS A RICH TABLE ---
        table = Table(
            title=f"Extension Created: {root_name}",
            box=box.ROUNDED,
            header_style="bold magenta",
        )
        table.add_column("Extension", style="blue")
        table.add_column("Group/Command", style="black")

        for sub in all_subs:
            table.add_row(root_name, sub)

        console.print("\n", table)
        console.print(f"Location: [blue]{target_dir}[/blue]")
        console.print("\nTo install it, run:")
        console.print(
            f"  [yellow]cd {target_dir}[/yellow]\n  [yellow]pip install -e .[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Failed to create extension: {e}[/red]")


@click.command(name="man")
@click.option("--all", is_flag=True, help="Generate a manual for all commands.")
@click.option(
    "--format",
    type=click.Choice(["md", "rst", "txt", "text", "qmd", "groff", "html"]),
    default="text",
)
@click.argument("command_name", required=False)
@click.pass_context
def cmd_man(ctx, all, format, command_name):
    """Display or generate the manual for CME commands."""
    cli = ctx.parent.parent
    if all:
        generate_manual(ctx, cli, format)
        ctx.exit()
    if command_name:
        cmd = cli.get_command(ctx, command_name)
        if cmd:
            formatter = get_formatter(format)
            click.echo(formatter.format_single(ctx, command_name, cmd))
            ctx.exit()
        else:
            click.echo(f"Error: Command '{command_name}' not found.")
            sys.exit(1)
    click.echo("Usage: cme command man [COMMAND_NAME] or cme command man --all")


# ==============================================================================
# DYNAMIC REGISTRATION
# ==============================================================================


def register(cli):
    """
    Attaches the 'command' management group to the main CLI
    and dynamically discovers all 'cmd_' functions in this module.
    """

    @cli.group(name="command")
    def command_group():
        """Manage cme extensions."""
        pass

    # 1. Get all members of the current module (this file)
    # We use globals() to see everything defined in this file
    module_members = globals()

    # 2. Loop through and find functions that start with 'cmd_' AND are Click commands
    for name, obj in module_members.items():
        if name.startswith("cmd_") and isinstance(obj, click.Command):
            command_group.add_command(obj)
