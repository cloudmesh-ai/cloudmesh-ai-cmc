# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
import click
import logging
import os
import sys
import subprocess
import pathlib
import shellingham
import pkgutil
import importlib
import importlib.resources
import shutil
from cloudmesh.ai.common import logging as ai_log
from cloudmesh.ai.common.telemetry import Telemetry, JSONFileBackend, TextBackend
from cloudmesh.ai.cmc.utils import Config, handle_errors, console
from rich.logging import RichHandler
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from rich.console import Group
from rich.text import Text
from rich import box
import cloudmesh.ai.command as extensions  # Import the extension package
from importlib.metadata import entry_points
from dataclasses import dataclass

@dataclass
class LazyCommand:
    name: str
    module_name: str
    entry_point_name: str
    hidden: bool = False

    def get_short_help_str(self, limit=None):
        return "Lazy-loaded extension"

from cloudmesh.ai.cmc.context import config, logger, telemetry


class DelegatingCommand(click.Group):
    """A command that delegates execution to another click object (e.g., a Group from a different click version)."""
    def __init__(self, name, delegate, **kwargs):
        # For a Group, ignore_unknown_options is a valid argument in many click versions
        # If it still fails, we can remove it and try another way.
        super().__init__(name, **kwargs)
        self.delegate = delegate

    def get_command(self, ctx, name):
        # Return None so that click doesn't try to find a subcommand within this group
        # and instead lets the invoke() method handle the arguments.
        return None

    def invoke(self, ctx):
        # We manually call the delegate's main method with the remaining arguments
        # This bypasses the need for the delegate to be a 'core' click object
        try:
            # If the delegate is a function (factory), call it first.
            # click.Group is also callable, so we check if it already has 'main' or 'commands'.
            if callable(self.delegate) and not hasattr(self.delegate, 'main') and not hasattr(self.delegate, 'commands'):
                logger.debug(f"Calling delegate factory {self.delegate}")
                actual_delegate = self.delegate()
                logger.debug(f"Factory returned {actual_delegate}")
            else:
                actual_delegate = self.delegate
            
            if actual_delegate is None:
                raise RuntimeError(f"Delegate for {self.name} resolved to None")

            # If the delegate is a click object (Group or Command), it doesn't have a .main() method.
            # We check for .main() first (for wrapper objects), otherwise we call it directly.
            if hasattr(actual_delegate, 'main') and callable(actual_delegate.main):
                actual_delegate.main(args=ctx.args, standalone_mode=True)
            elif callable(actual_delegate):
                # For click.Group/Command, we can't easily call them with args from here
                # without creating a new context. The safest way is to use a subprocess
                # or to use the click internal API.
                # However, since we are in a DelegatingCommand, we can try to invoke it.
                try:
                    # Try to use the click object's own entry point logic if it's a group
                    if hasattr(actual_delegate, 'cli'):
                        actual_delegate.cli(args=ctx.args, standalone_mode=True)
                    else:
                        # Fallback: call it as a function if it's a simple wrapper
                        actual_delegate(args=ctx.args, standalone_mode=True)
                except TypeError:
                    # If it doesn't accept args, it might be a standard click object
                    # In that case, we might need to use a different approach.
                    # For now, let's try to call it.
                    actual_delegate()
            else:
                raise RuntimeError(f"Delegate for {self.name} is not callable and has no .main() method")
        except Exception as e:
            logger.error(f"Delegation failed for {self.name}: {e}")
            sys.exit(1)

class SubcommandHelpGroup(click.Group):
    """Custom Click Group to show subcommands in help output with dynamic width."""

    def get_command(self, ctx, name):
        """Override to support lazy loading of extensions."""
        logger.debug(f"get_command called for {name}")
        cmd = super().get_command(ctx, name)
        logger.debug(f"initial cmd type for {name}: {type(cmd)}")
        
        # Use attribute check instead of isinstance to avoid Click version/instance mismatches
        if hasattr(cmd, 'path') and hasattr(cmd, 'entry_point_name'):
            # To prevent Click version mismatches between core and extensions,
            # we ensure the extension uses the same click module as the core.
            import click as core_click
            sys.modules['click'] = core_click

            # Load the actual command
            if getattr(cmd, 'module_name', None):
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
                # If the entry point is 'main', it's often just a wrapper that calls the real CLI.
                # We try to find the actual click object in the module.
                if getattr(cmd, '__name__', None) == 'main' and module:
                    for attr_name in ['cli', 'entry_point', 'group']:
                        attr = getattr(module, attr_name, None)
                        if attr and callable(attr):
                            logger.debug(f"Found actual click object or factory {attr_name} instead of main wrapper")
                            cmd = attr
                            break

                logger.debug(f"loaded cmd type for {name}: {type(cmd)}")
                # If the loaded command is seen as a function but is actually a click.Group from a different instance,
                # we wrap it in a DelegatingCommand to avoid Click version mismatches.
                if callable(cmd) and not hasattr(cmd, 'make_context'):
                    logger.debug(f"Wrapping {name} in DelegatingCommand due to Click version mismatch")
                    cmd = DelegatingCommand(name=name, delegate=cmd)
                
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




# Use standard click.Group during Sphinx builds to avoid issues with SubcommandHelpGroup
if os.getenv("SPHINX_BUILD") == "1":
    @click.group()
    @click.option("--debug", is_flag=True, help="Enable debug logging.")
    @click.pass_context
    def cli(ctx, debug):
        """cmc: Cloudmesh Commands."""
        pass
else:
    @click.group(cls=SubcommandHelpGroup)
    @click.option("--debug", is_flag=True, help="Enable debug logging.")
    @click.pass_context
    def cli(ctx, debug):
        """cmc: Cloudmesh Commands."""
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")








def load_core_extensions(cli):
    """
    Recursively iterates through the command directory and adds all click commands found.
    Handles sub-packages by creating groups for them.
    """
    found_any = False

    def register_recursive(current_cli, path, package_prefix, visited=None):
        nonlocal found_any
        if visited is None:
            visited = set()
        
        if package_prefix in visited:
            return
        visited.add(package_prefix)

        try:
            for _, module_name, is_pkg in pkgutil.iter_modules(path):
                full_module_name = f"{package_prefix}.{module_name}"
                if is_pkg:
                    # Create a group for the sub-package
                    group = click.Group(name=module_name)
                    current_cli.add_command(group)
                    # Recursively find commands inside this package
                    pkg = importlib.import_module(full_module_name)
                    register_recursive(group, pkg.__path__, full_module_name, visited)
                else:
                    try:
                        module = importlib.import_module(full_module_name)
                        # Find any click Command or Group in the module and add it
                        for attr in vars(module).values():
                            if isinstance(attr, (click.Command, click.Group)):
                                # Use the command's own name if it's explicitly set, otherwise use module_name
                                cmd_name = getattr(attr, 'name', module_name) or module_name
                                # Prevent adding the group to itself
                                if attr is not current_cli:
                                    current_cli.add_command(attr, name=cmd_name)
                                    found_any = True
                                break
                    except Exception as e:
                        logger.error(f"Could not load {full_module_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to iterate {package_prefix}: {e}")

    register_recursive(cli, extensions.__path__, "cloudmesh.ai.command")

    if not found_any:
        logger.warning("No core extensions found in cloudmesh.ai.command")


def load_pip_extensions(cli):
    """
    Loads extensions installed via pip using entry points lazily.
    """
    eps = entry_points().select(group="cloudmesh.ai.command")
    for entry_point in eps:
        # Avoid overwriting extensions already loaded from the registry
        if entry_point.name in cli.commands:
            logger.debug(f"Skipping pip extension {entry_point.name} as it is already registered")
            continue

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

# Eagerly load core extensions at module level so they are visible to sphinx-click
load_core_extensions(cli)

# --- Command Aliases ---
@cli.command(name="v", hidden=True)
@click.pass_context
def alias_version(ctx):
    """Alias for version."""
    ctx.invoke(cli.get_command("version"))

@cli.command(name="tel", hidden=True)
@click.pass_context
def alias_telemetry(ctx):
    """Alias for telemetry."""
    ctx.invoke(cli.get_command("telemetry"))

@cli.command(name="pl", hidden=True)
@click.pass_context
def alias_plugins_list(ctx):
    """Alias for plugins list."""
    plugins_group = cli.get_command("plugins")
    if plugins_group:
        ctx.invoke(plugins_group.get_command("list"))

@cli.command(name="pch", hidden=True)
@click.pass_context
def alias_plugins_check(ctx):
    """Alias for plugins check."""
    plugins_group = cli.get_command("plugins")
    if plugins_group:
        ctx.invoke(plugins_group.get_command("check"))






@handle_errors
def main():
    # Use telemetry to track the entire execution of the cmc tool
    with telemetry.track(message="Executing CMC command"):
        logger.debug("CMC main() is executing")

        # 1. Core extensions are now loaded at module level

        # 2. Load extensions installed via pip (entry points)
        load_pip_extensions(cli)
        cli()


if __name__ == "__main__":
    main()
