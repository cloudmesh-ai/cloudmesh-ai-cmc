# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
import click
import shellingham
import pkgutil
import importlib
import shutil
import cloudmesh.ai.extension as extensions  # Import the extension package
from cloudmesh.ai.registry import CommandRegistry
from importlib.metadata import entry_points


class SubcommandHelpGroup(click.Group):
    """Custom Click Group to show subcommands in help output with dynamic width."""

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
def cli():
    """CME: Custom Managed Extensions."""
    pass


def load_core_extensions(cli):
    """
    Iteratively finds all modules in the cloudmesh.ai.extension package
    and calls their register(cli) function.
    """
    for loader, module_name, is_pkg in pkgutil.iter_modules(extensions.__path__):
        full_module_name = f"cloudmesh.ai.extension.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
            if hasattr(module, "register"):
                module.register(cli)
        except Exception as e:
            print(f"Failed to load core extension {module_name}: {e}")


def load_pip_extensions(cli):
    """
    Loads extensions installed via pip using entry points.
    """
    eps = entry_points().select(group="cloudmesh.ai.extension")
    for entry_point in eps:
        try:
            register_func = entry_point.load()
            register_func(cli)
        except Exception as e:
            print(f"Failed to load pip extension {entry_point.name}: {e}")


# 1. Iteratively load all core extensions (Banner, Command, Man)
load_core_extensions(cli)


@cli.command(name="activate-shell")
@click.pass_context
def activate_shell(ctx):
    """Generate shell completion script for the current shell."""
    try:
        shell, _ = shellingham.detect_shell()
    except Exception:
        shell = "bash"
    completion_map = {
        "bash": 'eval "$(_CME_COMPLETE=bash_source cmc)"',
        "zsh": 'eval "$(_CME_COMPLETE=zsh_source cmc)"',
        "fish": "eval (_CME_COMPLETE=fish_source cmc)",
    }
    click.echo(completion_map.get(shell, f"# Shell {shell} not supported."))


def main():
    # 2. Inject active plugin commands from the JSON registry
    active_cmds = registry.get_active_commands()
    for name, obj in active_cmds.items():
        cli.add_command(obj, name=name)

    # 3. Load extensions installed via pip (entry points)
    load_pip_extensions(cli)
    cli()


if __name__ == "__main__":
    main()
