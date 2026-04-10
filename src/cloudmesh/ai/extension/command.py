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

    table = Table(
        title="CME Command Registry",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
    )

    table.add_column("COMMAND", style="blue", width=30)
    table.add_column("VERSION", style="dim")
    table.add_column("STATUS", justify="center")
    table.add_column("SOURCE PATH", style="black")

    for item in details:
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


@click.command(name="create")
@click.argument("name")
@click.option(
    "--groups", "-g", multiple=True, help="Additional sub-commands to create."
)
@click.option("--path", "-p", default=".", help="Path to create the extension in.")
def cmd_create(name, groups, path):
    """
    Create or expand a cme extension.
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

    if target_dir.exists():
        if not plugin_file.exists():
            console.print(f"[red]Error: {target_dir} is not a valid CME extension.[/red]")
            return

        content = plugin_file.read_text()
        existing_cmds = re.findall(rf'@{root_name}_group\.command\(name="([^"]+)"\)', content)

        new_additions_code = []
        added_names = []

        for sub in all_subs:
            if sub in existing_cmds:
                console.print(f"[yellow]Warning: '{sub}' already exists. Skipping.[/yellow]")
            else:
                code = f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} command added via CME."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
                new_additions_code.append(code)
                added_names.append(sub)

        if not added_names:
            return

        if "def register(cli):" in content:
            parts = content.split("def register(cli):")
            new_content = parts[0] + "".join(new_additions_code) + "def register(cli):" + parts[1]
            plugin_file.write_text(new_content)
            console.print(f"[green]Updated extension {root_name} with {added_names}[/green]")
        return

    try:
        extension_dir = target_dir / "src" / "cloudmesh" / "ai" / "extension"
        extension_dir.mkdir(parents=True, exist_ok=True)

        commands_code_list = [
            f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} created by CME."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
            for sub in all_subs
        ]

        pyproject_content = (templates_dir / "pyproject.toml.tmpl").read_text().format(name=root_name)
        plugin_content = (templates_dir / "plugin.py.tmpl").read_text().format(
            root_name=root_name, commands_code="".join(commands_code_list)
        )

        (target_dir / "VERSION").write_text("0.1.0")
        (target_dir / "pyproject.toml").write_text(pyproject_content)
        plugin_file.write_text(plugin_content)
        console.print(f"[green]Created new extension at {target_dir}[/green]")

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
    
    # Navigation: Find the root 'cmc' group
    # ctx.parent is 'command' group context
    # ctx.parent.parent is the root 'cmc' context
    root_cli = None
    if ctx.parent and ctx.parent.parent:
        root_cli = ctx.parent.parent.command # This is the root Group object
    elif ctx.parent:
        root_cli = ctx.parent.command
    else:
        root_cli = ctx.command

    if all:
        # Generate manual for everything under root
        content = generate_manual(ctx, root_cli, format)
        click.echo(content)
        ctx.exit()

    if command_name:
        # Use root_cli (Group) to find the command
        cmd = root_cli.get_command(ctx, command_name)
        if cmd:
            formatter = get_formatter(format)
            click.echo(formatter.format_single(ctx, command_name, cmd))
            ctx.exit()
        else:
            click.echo(f"Error: Command '{command_name}' not found.")
            sys.exit(1)

    # If nothing specific requested, show the help for 'man'
    click.echo(ctx.get_help())


# ==============================================================================
# DYNAMIC REGISTRATION
# ==============================================================================

def register(cli):
    """
    Attaches the 'command' management group to the main CLI.
    """
    @cli.group(name="command")
    def command_group():
        """Manage cme extensions."""
        pass

    module_members = globals()
    for name, obj in module_members.items():
        if name.startswith("cmd_") and isinstance(obj, click.Command):
            command_group.add_command(obj)