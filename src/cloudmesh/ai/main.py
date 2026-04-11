# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
import click
import os
import shellingham
import pkgutil
import importlib
import importlib.resources
import shutil
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from rich.console import Group
from rich.text import Text
import cloudmesh.ai.extension as extensions  # Import the extension package
from cloudmesh.ai.registry import CommandRegistry
from importlib.metadata import entry_points

# Setup Rich Logging
logging.basicConfig(
    level="WARNING",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("cmc")


from cloudmesh.ai.registry import CommandRegistry, LazyCommand


class SubcommandHelpGroup(click.Group):
    """Custom Click Group to show subcommands in help output with dynamic width."""

    def get_command(self, ctx, name):
        """Override to support lazy loading of extensions."""
        cmd = super().get_command(ctx, name)
        if isinstance(cmd, LazyCommand):
            # Load the actual command
            if cmd.path:
                # Registry-based extension
                module = registry._load_extension(cmd.name, cmd.path)
                if module:
                    cmd = getattr(module, cmd.entry_point_name, None)
            elif cmd.module_name:
                # Core or Pip extension
                try:
                    module = importlib.import_module(cmd.module_name)
                    cmd = getattr(module, cmd.entry_point_name, None)
                except Exception as e:
                    logger.error(
                        f"Failed to lazy-load extension {cmd.module_name}: {e}"
                    )
                    cmd = None

            if cmd:
                # Cache the loaded command in the group
                self.commands[name] = cmd
        return cmd

    def format_commands(self, ctx, formatter):
        """
        Overwrites the default command formatting to ensure help text
        is not prematurely truncated and utilizes the full terminal width.
        """
        # 1. Sync formatter width with actual terminal width
        term_width, _ = shutil.get_terminal_size()
        formatter.width = term_width

        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
            commands.append((subcommand, cmd))

        if not commands:
            return

        # 2. Calculate the column width for the command names
        # We find the longest command name to align the help text column
        max_name_len = max([len(name) for name, _ in commands]) if commands else 0

        # 3. Calculate available width for the help text
        # Margin (2) + Name + Padding (2)
        available_help_width = term_width - max_name_len - 6

        with formatter.section("Commands"):
            rows = []
            for name, cmd in commands:
                # We use a larger limit for the help string to ensure
                # the docstrings we wrote in speedtest.py and tree.py are visible
                help_text = cmd.get_short_help_str(limit=available_help_width)
                rows.append((name, help_text))

            formatter.write_dl(rows)


# Initialize registry globally so extensions can import it
registry = CommandRegistry()


@click.group(cls=SubcommandHelpGroup)
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx, debug):
    """cmc: Cloudmesh Commands."""
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")






@cli.command(name="version")
def version():
    """Display the current version of cmc and active extensions."""
    from importlib.metadata import version as get_version

    console = Console()

    try:
        core_version = get_version("cloudmesh-ai-cmc")
    except Exception:
        core_version = "Unknown"

    console.print(f"[bold blue]cmc version {core_version}[/bold blue]\n")

    details = registry.list_all_details()
    if not details:
        console.print("No active extensions registered.")
        return

    table = Table(title="Active Extensions")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Path", style="green")

    for item in details:
        table.add_row(item["name"], item["version"], item["path"])

    console.print(table)


def load_core_extensions(cli):
    """
    Iteratively finds all modules in the cloudmesh.ai.extension package
    and registers them eagerly to ensure they always appear in help.
    """
    found_any = False

    # We use a list of known core extensions to be absolutely sure they are loaded
    # if dynamic discovery fails.
    core_modules = ["banner", "tree", "man", "command", "docs"]

    for module_name in core_modules:
        try:
            full_module_name = f"cloudmesh.ai.extension.{module_name}"
            module = importlib.import_module(full_module_name)

            # 1. Try the new 'entry_point' pattern
            if hasattr(module, "entry_point"):
                cli.add_command(module.entry_point, name=module_name)
                found_any = True
            # 2. Try the old 'register(cli)' pattern
            elif hasattr(module, "register"):
                module.register(cli)
                found_any = True
            # 3. Fallback: Look for any click.Command in the module
            else:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, click.Command):
                        cli.add_command(attr, name=module_name)
                        found_any = True
                        break
                if not found_any:
                    logger.warning(
                        f"Core extension {module_name} has no compatible entry point"
                    )
        except Exception as e:
            logger.debug(f"Could not eagerly load core extension {module_name}: {e}")

    # Also try dynamic discovery for any new core extensions added to the package
    try:
        for loader, module_name, is_pkg in pkgutil.iter_modules(extensions.__path__):
            if is_pkg or module_name in core_modules:
                continue
            try:
                full_module_name = f"cloudmesh.ai.extension.{module_name}"
                module = importlib.import_module(full_module_name)

                if hasattr(module, "entry_point"):
                    cli.add_command(module.entry_point, name=module_name)
                    found_any = True
                elif hasattr(module, "register"):
                    module.register(cli)
                    found_any = True
                else:
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, click.Command):
                            cli.add_command(attr, name=module_name)
                            found_any = True
                            break
            except Exception:
                continue
    except Exception:
        pass

    if not found_any:
        logger.debug("No core extensions were successfully loaded")
        logger.warning("No core extensions were successfully loaded")
    else:
        logger.debug("Successfully loaded core extensions")


def load_pip_extensions(cli):
    """
    Loads extensions installed via pip using entry points lazily.
    """
    eps = entry_points().select(group="cloudmesh.ai.extension")
    for entry_point in eps:
        # We use the entry point's value as the module name
        # entry_point.value is usually 'module.function'
        module_path, func_name = entry_point.value.rsplit(":", 1)
        cli.add_command(
            LazyCommand(
                name=entry_point.name,
                module_name=module_path,
                entry_point_name=func_name,
            ),
            name=entry_point.name,
        )




@cli.command(name="completion")
@click.pass_context
def completion(ctx):
    """Generate shell completion script for the current shell."""
    try:
        shell, _ = shellingham.detect_shell()
    except Exception:
        shell = "bash"

    completion_map = {
        "bash": {
            "eval": 'eval "$(_CME_COMPLETE=bash_source cmc)"',
            "profile": "~/.bashrc",
        },
        "zsh": {
            "eval": 'eval "$(_CME_COMPLETE=zsh_source cmc)"',
            "profile": "~/.zshrc",
        },
        "fish": {
            "eval": "eval (_CME_COMPLETE=fish_source cmc)",
            "profile": "~/.config/fish/config.fish",
        },
    }

    shell_info = completion_map.get(shell)
    if not shell_info:
        click.echo(f"# Shell {shell} not supported.")
        return

    click.echo("Current Session Activation:")
    click.echo(shell_info["eval"])
    click.echo("")
    click.echo(f"Permanent Activation (add to {shell_info['profile']}):")
    click.echo(f"echo '{shell_info['eval']}' >> {shell_info['profile']}")


def main():
    logger.debug("CMC main() is executing")
    # 1. Load core extensions bundled with the package
    load_core_extensions(cli)

    # 2. Inject active plugin commands from the JSON registry lazily
    lazy_cmds = registry.get_lazy_commands()
    for name, obj in lazy_cmds.items():
        cli.add_command(obj, name=name)

    # 3. Load extensions installed via pip (entry points)
    load_pip_extensions(cli)
    cli()


if __name__ == "__main__":
    main()
