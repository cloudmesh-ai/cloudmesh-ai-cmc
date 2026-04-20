# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
import click
import os
import io
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

try:
    from prompt_toolkit import PromptSession, HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.completion import WordCompleter
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

from cloudmesh.ai.cmc.context import logger

console = Console()

def get_command_completer():
    """Creates a completer based on all registered Click commands and internal shell commands."""
    if not HAS_PROMPT_TOOLKIT:
        return None
        
    try:
        from cloudmesh.ai.cmc.main import cli
        commands = set()
        
        # 1. Extract all commands from the Click CLI object
        def collect_commands(group, ctx, visited=None):
            if visited is None:
                visited = set()
            
            if group in visited:
                return
            visited.add(group)

            for cmd_name in group.list_commands(ctx):
                commands.add(cmd_name)
                # If the command is a group, recursively collect its sub-commands
                cmd = group.get_command(ctx, cmd_name)
                if isinstance(cmd, click.Group):
                    # We add the sub-commands as "parent child" for the completer
                    for sub_name in cmd.list_commands(ctx):
                        commands.add(f"{cmd_name} {sub_name}")
                    # Recurse deeper if needed
                    collect_commands(cmd, ctx, visited)

        collect_commands(cli, click.Context(cli))
        
        # 2. Add internal shell commands
        shell_commands = ["exit", "quit", "q", "help", "set", "h"]
        commands.update(shell_commands)
        
        
        return WordCompleter(list(commands), ignore_case=True)
    except Exception as e:
        logger.error(f"Failed to create command completer: {e}")
        return WordCompleter([])

@click.command(name="shell")
def entry_point():
    """Enter an interactive shell for CMC commands."""
    console.print(Panel("[bold blue]CMC Interactive Shell[/bold blue]\nType 'exit' or 'quit' to leave, or 'help' for commands."))
    
    # History file path: ~/.config/cloudmesh/ai/cmc_history
    history_dir = Path("~/.config/cloudmesh/ai").expanduser()
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "cmc_history"
    
    if HAS_PROMPT_TOOLKIT:
        session = PromptSession(history=FileHistory(str(history_file)))
    elif HAS_READLINE:
        # Load history into readline for the fallback input()
        if history_file.exists():
            try:
                readline.read_history_file(str(history_file))
            except Exception as e:
                logger.error(f"Failed to load readline history: {e}")
        session = None
    else:
        session = None
    
    while True:
        try:
            # Update completer every loop to reflect registry changes (e.g. after 'plugins add')
            completer = get_command_completer()
            
            if HAS_PROMPT_TOOLKIT:
                # Use prompt_toolkit's HTML formatting for the prompt to avoid raw ANSI codes
                prompt_text = HTML('<b fg="darkblue">cmc</b> > ')
                
                # Use prompt_toolkit for input to get history and autocomplete
                user_input = session.prompt(
                    prompt_text, 
                    completer=completer
                ).strip()
            else:
                # Fallback to Rich-captured ANSI for basic input()
                with console.capture() as capture:
                    console.print("[bold blue]cmc[/bold blue] > ", end="")
                prompt_ansi = capture.get()
                user_input = input(prompt_ansi).strip()
                
                # If readline is available, save the input to history
                if HAS_READLINE and user_input:
                    # Note: prompt_toolkit handles this automatically, 
                    # but for basic input() we must do it manually.
                    with open(history_file, "a") as f:
                        f.write(user_input + "\n")
            
            if not user_input:
                continue
            
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Exiting shell...[/yellow]")
                break

            # Handle history command: h <NUM>
            if user_input.startswith("h "):
                try:
                    num_str = user_input[2:].strip()
                    if num_str.isdigit():
                        num = int(num_str)
                        if history_file.exists():
                            with open(history_file, "r") as f:
                                lines = f.readlines()
                                last_lines = lines[-num:]
                                console.print(Panel(
                                    "".join(last_lines).rstrip(),
                                    title=f"Last {num} Commands"
                                ))
                        else:
                            console.print("[red]No history file found.[/red]")
                    else:
                        console.print("[red]Error:[/red] Please provide a number, e.g., 'h 10'")
                except Exception as e:
                    console.print(f"[red]Error reading history:[/red] {e}")
                continue

            # 1. Handle internal shell commands
            if user_input.startswith("set "):
                try:
                    # Format: set KEY=VALUE
                    kv_pair = user_input[4:].strip()
                    if "=" in kv_pair:
                        k, v = kv_pair.split("=", 1)
                        os.environ[k.strip()] = v.strip()
                        console.print(f"[green]Environment variable set:[/green] {k.strip()} = {v.strip()}")
                    else:
                        console.print("[red]Error:[/red] Use format 'set KEY=VALUE'")
                except Exception as e:
                    console.print(f"[red]Error setting environment variable:[/red] {e}")
                continue

            if user_input.lower() == "help":
                console.print(Panel(
                    "[bold cyan]CMC Shell Commands[/bold cyan]\n"
                    "  [bold]help[/bold]       : Show this help message\n"
                    "  [bold]set KEY=VAL[/bold] : Set a temporary environment variable\n"
                    "  [bold]h <NUM>[/bold]     : Show the last <NUM> history entries\n"
                    "  [bold]exit/quit/q[/bold] : Leave the shell\n\n"
                    "[bold]CMC CLI Commands[/bold]\n"
                    "  Type any registered CMC command (e.g., 'plugins list', 'config get key')\n"
                    "  Use [bold]Tab[/bold] for autocomplete."
                ))
                continue
            
            # 2. Execute CMC CLI commands
            # Split input into arguments for click
            args = user_input.split()
            
            # Execute the command using the existing cli group
            # We use standalone_mode=False to prevent sys.exit() on help or errors
            from cloudmesh.ai.cmc.main import cli
            cli.main(args=args, standalone_mode=False)
            
        except click.UsageError as e:
            console.print(f"[red]Usage Error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")