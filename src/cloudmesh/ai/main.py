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
        """Enhanced version of format_commands to match user request."""
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue
            commands.append((subcommand, cmd))

        if commands:
            # Explicitly get the terminal width using shutil
            term_width, _ = shutil.get_terminal_size()

            # Click's default formatter width might be stuck at 80
            # Let's ensure the formatter uses the actual width if it's larger
            if term_width > formatter.width:
                formatter.width = term_width

            # Calculate the max name length (including indentation)
            all_names = []
            for name, cmd in commands:
                all_names.append(name)
                if isinstance(cmd, click.Group):
                    for sub_name in cmd.list_commands(ctx):
                        all_names.append(f"  {sub_name}")

            max_name_len = max([len(n) for n in all_names]) if all_names else 0

            # Available width for help text is terminal width minus name column and margins
            # Click write_dl uses 2 spaces margin + name + 2 spaces padding
            available_help_width = term_width - max_name_len - 6

            # Ensure a sane minimum
            if available_help_width < 20:
                available_help_width = 45

            with formatter.section("Commands"):
                rows = []
                for name, cmd in commands:
                    # Pass the dynamically calculated limit to avoid premature '...'
                    help_text = cmd.get_short_help_str(limit=available_help_width)
                    rows.append((name, help_text))

                    if isinstance(cmd, click.Group):
                        for sub_name in cmd.list_commands(ctx):
                            sub_cmd = cmd.get_command(ctx, sub_name)
                            if sub_cmd is None or sub_cmd.hidden:
                                continue
                            sub_help = sub_cmd.get_short_help_str(
                                limit=available_help_width
                            )
                            rows.append((f"  {sub_name}", sub_help))

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
    # extensions.__path__ is the directory where banner, command, man live
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
        "bash": 'eval "$(_CME_COMPLETE=bash_source cme)"',
        "zsh": 'eval "$(_CME_COMPLETE=zsh_source cme)"',
        "fish": "eval (_CME_COMPLETE=fish_source cme)",
    }
    click.echo(completion_map.get(shell, f"# Shell {shell} not supported."))


def main():
    # 2. Inject active plugin commands from the JSON registry (~/.cme_registry.json)
    active_cmds = registry.get_active_commands()
    for name, obj in active_cmds.items():
        cli.add_command(obj, name=name)

    # 3. Load extensions installed via pip (entry points)
    load_pip_extensions(cli)

    cli()


if __name__ == "__main__":
    main()
