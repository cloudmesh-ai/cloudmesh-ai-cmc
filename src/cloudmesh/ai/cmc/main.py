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
import io
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
    """Represents a command that is loaded lazily from a module.

    Attributes:
        name (str): The name of the command.
        module_name (str): The name of the module containing the command.
        entry_point_name (str): The name of the entry point function/object in the module.
        hidden (bool): Whether the command should be hidden from help output. Defaults to False.
    """
    name: str
    module_name: str
    entry_point_name: str
    hidden: bool = False

    def get_short_help_str(self, limit=None):
        """Returns a short help string for the lazy-loaded command.

        Args:
            limit (int, optional): Maximum length of the help string. Defaults to None.

        Returns:
            str: A short description of the command.
        """
        return "Lazy-loaded extension"

from cloudmesh.ai.cmc.context import config, logger, telemetry


class DelegatingCommand(click.Group):
    """A command that delegates execution to another click object.

    This is used to handle cases where a command is loaded from a different 
    Click version or instance, preventing version mismatch errors.
    """
    def __init__(self, name, delegate, **kwargs):
        """Initializes the DelegatingCommand.

        Args:
            name (str): The name of the command.
            delegate (Any): The actual click object or factory to delegate to.
            **kwargs: Additional arguments passed to the click.Group constructor.
        """
        # For a Group, ignore_unknown_options is a valid argument in many click versions
        # If it still fails, we can remove it and try another way.
        super().__init__(name, **kwargs)
        self.delegate = delegate

    def get_command(self, ctx, name):
        """Overrides get_command to delegate subcommand retrieval to the delegate.

        Args:
            ctx (click.Context): The Click context.
            name (str): The name of the command to retrieve.

        Returns:
            click.Command: The retrieved command from the delegate, or None.
        """
        if hasattr(self.delegate, 'get_command'):
            return self.delegate.get_command(ctx, name)
        return None

    def invoke(self, ctx):
        """Invokes the delegate object with the provided context.

        Args:
            ctx (click.Context): The Click context containing the arguments.

        Raises:
            RuntimeError: If the delegate cannot be resolved or is not callable.
        """
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
    """Custom Click Group to show subcommands in help output with dynamic width.

    This group overrides the default command retrieval and formatting to support
    lazy loading of extensions and to ensure help text utilizes the full terminal width.
    """

    def get_command(self, ctx, name):
        """Retrieves a command, supporting lazy loading of extensions.

        Args:
            ctx (click.Context): The Click context.
            name (str): The name of the command to retrieve.

        Returns:
            click.Command: The loaded command, or None if not found.
        """
        logger.debug(f"get_command called for {name}")
        cmd = super().get_command(ctx, name)
        logger.debug(f"initial cmd type for {name}: {type(cmd)}")
        
        # Use attribute check instead of isinstance to avoid Click version/instance mismatches
        if hasattr(cmd, 'module_name') and hasattr(cmd, 'entry_point_name'):
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
        """Overwrites the default command formatting for full terminal width.

        Ensures that help text is not prematurely truncated by syncing the 
        formatter width with the actual terminal size.

        Args:
            ctx (click.Context): The Click context.
            formatter (click.helpers.HelpFormatter): The formatter to use.
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
    @click.option("-v", "--debug", is_flag=True, help="Enable debug logging.")
    @click.pass_context
    def cli(ctx, debug):
        """cmc: Cloudmesh Commands."""
        pass
else:
    @click.group(cls=SubcommandHelpGroup)
    @click.option("-v", "--debug", is_flag=True, help="Enable debug logging.")
    @click.pass_context
    def cli(ctx, debug):
        """cmc: Cloudmesh Commands.

        The main entry point for the Cloudmesh AI CMC tool.

        Args:
            ctx (click.Context): The Click context.
            debug (bool): Whether to enable debug logging.
        """
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")








def load_core_extensions(cli):
    """Recursively loads all core extensions from the command directory.

    Iterates through the `cloudmesh.ai.command` package and adds any found 
    Click commands or groups to the provided CLI object.

    Args:
        cli (click.Group): The main CLI group to which extensions are added.
    """
    found_any = False
    
    # Handle namespace packages where __path__ is a list
    paths = getattr(extensions, '__path__', [])
    if isinstance(paths, str):
        paths = [paths]

    def register_recursive(current_cli, path, package_prefix, visited=None):
        nonlocal found_any
        if visited is None:
            visited = set()
        
        if package_prefix in visited:
            return
        visited.add(package_prefix)

        # Ensure path is a list for pkgutil.iter_modules
        search_path = path if isinstance(path, (list, tuple)) else [path]

        try:
            for _, module_name, is_pkg in pkgutil.iter_modules(search_path):
                full_module_name = f"{package_prefix}.{module_name}"
                logger.debug(f"Found module: {full_module_name} (pkg={is_pkg})")
                # Try to use the module/package's own register function if it exists
                try:
                    mod = importlib.import_module(full_module_name)
                    if hasattr(mod, 'register') and callable(mod.register):
                        mod.register(current_cli)
                        visited.add(full_module_name)
                        found_any = True
                        continue 
                except Exception as e:
                    logger.debug(f"Could not use register function for {full_module_name}: {e}")

                if is_pkg:
                    # Fallback: Create a group for the sub-package and recurse
                    group = click.Group(name=module_name)
                    current_cli.add_command(group)
                    try:
                        pkg = importlib.import_module(full_module_name)
                        register_recursive(group, pkg.__path__, full_module_name, visited)
                    except Exception as e:
                        logger.error(f"Failed to recurse into {full_module_name}: {e}")
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
                                    logger.debug(f"Adding command {cmd_name} to {current_cli}")
                                    current_cli.add_command(attr, name=cmd_name)
                                    found_any = True
                                break
                    except Exception as e:
                        logger.error(f"Could not load {full_module_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to iterate {package_prefix}: {e}")

    for path in paths:
        register_recursive(cli, path, "cloudmesh.ai.command")

    if not found_any:
        logger.warning("No core extensions found in cloudmesh.ai.command")


def load_pip_extensions(cli):
    """Loads extensions installed via pip using entry points lazily.

    Searches for entry points in the 'cloudmesh.ai.command' group and adds 
    them as LazyCommand objects to the CLI.

    Args:
        cli (click.Group): The main CLI group to which extensions are added.
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

def generate_completion_script(shell_type):
    """Prints the shell completion script for the specified shell type.

    Args:
        shell_type (str): The type of shell (e.g., 'bash_source', 'zsh_source', 'fish_source').
    """
    scripts = {
        "bash_source": (
            "_cmc() {\n"
            "    local cur=\"${COMP_WORDS[COMP_CWORD]}\"\n"
            "    local suggestions=$(CLICOMPLETE=1 cmc \"${COMP_WORDS[@]:1}\")\n"
            "    COMPREPLY=( $(compgen -W \"$suggestions\" -- \"$cur\") )\n"
            "}\n"
            "complete -F _cmc cmc"
        ),
        "zsh_source": (
            "autoload -Uz compinit && compinit\n"
            "_cmc() {\n"
            "    local -a opts\n"
            "    # In Zsh completion functions, $words contains the current command line\n"
            "    # We skip the first word (the command itself) and pass the rest to cmc\n"
            "    # We use \"${words[2,CURRENT]}\" to get the arguments up to the cursor\n"
            "    opts=($(CLICOMPLETE=1 cmc \"${words[2,CURRENT]}\"))\n"
            "    compadd -a opts\n"
            "}\n"
            "compdef _cmc cmc"
        ),
        "fish_source": (
            "complete -c cmc -f\n"
            "complete -c cmc -a \"(CLICOMPLETE=1 cmc)\""
        ),
    }
    script = scripts.get(shell_type, "")
    print(script)

def handle_completion():
    """Manually handles shell completion requests.

    This function is called when the environment variable CLICOMPLETE=1 is set.
    It determines the current word being typed and suggests matching commands 
    or subcommands.
    """
    # Suppress all logs except WARNING/ERROR during completion to avoid 
    # polluting the shell completion list.
    logging.getLogger().setLevel(logging.WARNING)
    logger.setLevel(logging.WARNING)

    try:
        # Ensure extensions are loaded before completing
        load_core_extensions(cli)
        load_pip_extensions(cli)
    except Exception as e:
        # We print to stderr so it doesn't pollute the completion list
        print(f"Error loading extensions during completion: {e}", file=sys.stderr)
    
    args = sys.argv[1:]
    
    # Support reading completion arguments from stdin (e.g., cat FILE | cmc)
    # if no arguments are provided via CLI.
    if not args and not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if stdin_content:
            # Split by whitespace to simulate argv
            args = stdin_content.split()
    
    # Determine the current word being typed and the preceding context
    if not args:
        current_word = ""
        context_args = []
    elif args[-1] == "":
        current_word = ""
        context_args = args[:-1]
    else:
        current_word = args[-1]
        context_args = args[:-1]

    if not context_args:
        # Root level completion: suggest top-level commands
        all_commands = list(cli.commands.keys())
        
        # If the user has already typed a full command name (possibly with trailing space) and hit TAB,
        # check if it's a group and suggest its subcommands instead.
        stripped_word = current_word.rstrip()
        if stripped_word in all_commands:
            cmd = cli.commands.get(stripped_word)
            # Use hasattr to avoid Click version mismatch issues with isinstance
            if cmd and hasattr(cmd, 'commands'):
                for sub_cmd in cmd.commands.keys():
                    print(sub_cmd)
                return

        # Otherwise, suggest commands that start with the current word
        # Strip trailing whitespace to allow matching (e.g., "ban " matches "banner")
        search_word = current_word.rstrip()
        for cmd_name in all_commands:
            if cmd_name.startswith(search_word):
                print(cmd_name)
    else:
        # Subcommand completion: suggest subcommands for the first argument
        group_name = context_args[0]
        group = cli.commands.get(group_name)
        
        # Use hasattr to avoid Click version mismatch issues with isinstance
        if group and hasattr(group, 'commands'):
            for sub_cmd in group.commands.keys():
                if sub_cmd.startswith(current_word):
                    print(sub_cmd)
        else:
            # If the first argument isn't a group, we can't suggest subcommands.
            # We print nothing, which allows the shell to potentially fall back
            # to other completion types, but we've tried our best.
            pass


# Check for shell completion script request at module level to ensure it's caught
# before any other logic (like telemetry or CLI execution) runs.
_complete_var = os.environ.get("_CME_COMPLETE")
if _complete_var:
    generate_completion_script(_complete_var)
    sys.exit(0)

# Check for actual completion suggestions request at module level
if os.environ.get("CLICOMPLETE") == "1":
    # Silence all logging immediately before doing anything else
    logging.getLogger().setLevel(logging.WARNING)
    # Also silence the specific cmc logger if it's already initialized
    try:
        logger.setLevel(logging.WARNING)
    except Exception:
        pass

    try:
        handle_completion()
    except Exception as e:
        print(f"Completion Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    sys.exit(0)

# Eagerly load core extensions at module level so they are visible to sphinx-click
load_core_extensions(cli)

# --- Command Aliases ---
@cli.command(name="v", hidden=True)
@click.pass_context
def alias_version(ctx):
    """Alias for version.

    Args:
        ctx (click.Context): The Click context.
    """
    ctx.invoke(cli.get_command("version"))

@cli.command(name="tel", hidden=True)
@click.pass_context
def alias_telemetry(ctx):
    """Alias for telemetry.

    Args:
        ctx (click.Context): The Click context.
    """
    ctx.invoke(cli.get_command("telemetry"))

@cli.command(name="pl", hidden=True)
@click.pass_context
def alias_plugins_list(ctx):
    """Alias for plugins list.

    Args:
        ctx (click.Context): The Click context.
    """
    plugins_group = cli.get_command("plugins")
    if plugins_group:
        ctx.invoke(plugins_group.get_command("list"))

@cli.command(name="pch", hidden=True)
@click.pass_context
def alias_plugins_check(ctx):
    """Alias for plugins check.

    Args:
        ctx (click.Context): The Click context.
    """
    plugins_group = cli.get_command("plugins")
    if plugins_group:
        ctx.invoke(plugins_group.get_command("check"))







def main():
    """Main entry point for the CMC application.

    Initializes pip extensions and invokes the Click CLI.
    """
    # Use telemetry to track the entire execution of the cmc tool
    with telemetry.track(message="Executing CMC command"):
        logger.debug("CMC main() is executing")

        # 1. Core extensions are now loaded at module level

        # 2. Load extensions installed via pip (entry points)
        load_pip_extensions(cli)
        cli()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
