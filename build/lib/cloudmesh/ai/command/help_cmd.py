# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
import click
from cloudmesh.ai.cmc.main import cli

def entry_point(ctx, name):
    """Show help for a specific command or the general CMC help."""
    # Use ctx.parent to get the main cli group
    cli_group = ctx.parent
    if name:
        # Get the specific command object
        cmd = cli_group.get_command(name)
        if cmd:
            click.echo(cmd.get_help())
        else:
            click.echo(f"Error: Command '{name}' not found.", err=True)
            ctx.exit(1)
    else:
        # Print the general help text for the CLI
        click.echo(cli_group.get_help())
    
    ctx.exit(0)

# Create the command object explicitly to avoid decorator issues
help_command = click.Command(
    name="help",
    callback=lambda ctx, param_vars, args: entry_point(ctx, args[0] if args else None),
    help="Show help for a specific command or the general CMC help."
)
