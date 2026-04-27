import click
import sys
import inspect
from cloudmesh.ai.common.io import console
from cloudmesh.ai.command.man import generate_manual, get_formatter
import os
from pathlib import Path
import re

# ==============================================================================
# COMMAND DEFINITIONS
# All functions starting with 'cmd_' will be automatically registered
# ==============================================================================


@click.command(name="load")
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "--name", "-n", help="Custom name for the extension"
)
def cmd_load(directory, name):
    """Register and load a new command."""
    from cloudmesh.ai.cmc.main import registry

    registry.register(name, directory)
    # Derive the name if not provided for the output message
    display_name = name or os.path.basename(os.path.abspath(directory))
    console.ok(f"Loaded and activated: {display_name}")


@click.command(name="activate")
@click.argument("name")
def cmd_activate(name):
    """Activate a registered command."""
    from cloudmesh.ai.cmc.main import registry

    if registry.set_status(name, True):
        console.ok(f"Activated: {name}")
    else:
        console.error(f"{name} not found in registry.")


@click.command(name="deactivate")
@click.argument("name")
def cmd_deactivate(name):
    """Deactivate a registered command."""
    from cloudmesh.ai.cmc.main import registry

    if registry.set_status(name, False):
        console.ok(f"Deactivated: {name}")
    else:
        console.error(f"{name} not found in registry.")


@click.command(name="list")
def cmd_list():
    """List all registered commands using a professional Rich table."""
    from cloudmesh.ai.cmc.main import registry

    details = registry.list_all_details()

    if not details:
        console.warning("Registry is empty.")
        return

    data = [
        (item["name"], item["version"], "[green]active[/green]" if item["active"] else "[red]inactive[/red]", item["path"])
        for item in details
    ]
    console.table(["COMMAND", "VERSION", "STATUS", "SOURCE PATH"], data, title="CME Command Registry")


@click.command(name="unload")
@click.argument("name")
def cmd_unload(name):
    """Remove a command from the registry."""
    from cloudmesh.ai.cmc.main import registry

    registry.unregister(name)
    console.ok(f"Unloaded: {name}")


@click.command(name="create")
@click.argument("name")
@click.option(
    "--groups", "-g", multiple=True, help="Additional sub-commands to create."
)
@click.option("--path", "-p", default=".", help="Path to create the command in.")
def cmd_create(name, groups, path):
    """
    Create or expand a CMC command.
    """
    root_name = name
    all_subs = list(groups)

    if not all_subs:
        all_subs = [root_name]

    current_dir = Path(__file__).parent
    templates_dir = current_dir.parent / "cmc" / "templates"
    base_dir = Path(path).expanduser().resolve()
    target_dir = base_dir / f"cloudmesh-ai-{root_name}"
    plugin_file = target_dir / "src" / "cloudmesh" / "ai" / "command" / f"{root_name}.py"

    if target_dir.exists():
        console.warning(f"The command '{root_name}' in the directory '{target_dir.name}' already exists.")
        if click.confirm("Do you want to erase it and create a new one?", default=False):
            import shutil
            shutil.rmtree(target_dir)
        elif plugin_file.exists():
            # Directory exists and is a valid command, proceed to expand
            content = plugin_file.read_text()
            existing_cmds = re.findall(rf'@{root_name}_group\.command\(name="([^"]+)"\)', content)

            new_additions_code = []
            added_names = []

            for sub in all_subs:
                if sub in existing_cmds:
                    console.warning(f"'{sub}' already exists. Skipping.")
                else:
                    code = f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} command added via CMC."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
                    new_additions_code.append(code)
                    added_names.append(sub)

            if not added_names:
                return

                if "def register(cli):" in content:
                    parts = content.split("def register(cli):")
                    new_content = parts[0] + "".join(new_additions_code) + "def register(cli):" + parts[1]
                    plugin_file.write_text(new_content)
                    console.ok(f"Updated extension {root_name} with {added_names}")
                return

    try:
        command_dir = target_dir / "src" / "cloudmesh" / "ai" / "command"
        command_dir.mkdir(parents=True, exist_ok=True)

        commands_code_list = [
            f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} created by CMC."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
            for sub in all_subs
        ]

        pyproject_content = (templates_dir / "pyproject.toml.tmpl").read_text().format(name=root_name)
        plugin_content = (templates_dir / "plugin.py.tmpl").read_text().format(
            root_name=root_name, commands_code="".join(commands_code_list)
        )

        # Collect created files for the banner
        created_files = []
        try:
            rel_target = target_dir.relative_to(Path.cwd())
            created_files.append(f"./{rel_target}/")
        except ValueError:
            created_files.append(f"{target_dir}/")

        (target_dir / "VERSION").write_text("0.1.0")
        created_files.append("    - VERSION")

        (target_dir / "pyproject.toml").write_text(pyproject_content)
        created_files.append("    - pyproject.toml")

        plugin_file.write_text(plugin_content)
        created_files.append(f"    - {plugin_file.relative_to(target_dir)}")
        
        # Write additional templates
        if (templates_dir / "Makefile").exists():
            (target_dir / "Makefile").write_text((templates_dir / "Makefile").read_text().format(name=root_name))
            created_files.append("    - Makefile")
        if (templates_dir / "LICENSE.tmpl").exists():
            (target_dir / "LICENSE").write_text((templates_dir / "LICENSE.tmpl").read_text())
            created_files.append("    - LICENSE")
            
        console.banner("Extension Created", "\n".join(created_files))
        console.ok(f"Created new command at {target_dir}")

    except Exception as e:
        console.error(f"Failed to create extension: {e}")


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
            console.print(formatter.format_single(ctx, command_name, cmd))
            ctx.exit()
        else:
            console.error(f"Command '{command_name}' not found.")
            sys.exit(1)

    # If nothing specific requested, show the help for 'man'
    console.print(ctx.get_help())


# ==============================================================================
# DYNAMIC REGISTRATION
# ==============================================================================

def register(cli):
    """
    Attaches the 'command' management group to the main CLI.
    """
    @cli.group(name="command")
    def command_group():
        """Manage CMC commands."""
        pass

    module_members = globals()
    for name, obj in module_members.items():
        if name.startswith("cmd_") and isinstance(obj, click.Command):
            command_group.add_command(obj)