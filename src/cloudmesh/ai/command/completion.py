# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import click
import os
import sys
import shellingham

from cloudmesh.ai.cmc.context import logger

@click.command(name="completion")
@click.option("--install", is_flag=True, help="Automatically install completion to your shell profile.")
@click.pass_context
def entry_point(ctx, install):
    """Generate or install shell completion script for the current shell."""
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

    if install:
        profile_path = os.path.expanduser(shell_info["profile"])
        try:
            # Ensure directory exists
            profile_dir = os.path.dirname(profile_path)
            if profile_dir and not os.path.exists(profile_dir):
                os.makedirs(profile_dir, exist_ok=True)

            # Check if already installed to avoid duplicates
            if os.path.exists(profile_path):
                with open(profile_path, "r") as f:
                    if shell_info["eval"] in f.read():
                        click.echo(f"Completion already installed in {profile_path}")
                        return

            with open(profile_path, "a") as f:
                f.write(f"\n# Cloudmesh CMC Completion\n{shell_info['eval']}\n")
            
            click.echo(f"Successfully installed completion to {profile_path}")
            
            # Provide shell-specific reload instructions
            reload_cmd = {
                "bash": f"source {shell_info['profile']}",
                "zsh": f"source {shell_info['profile']}",
                "fish": f"source {shell_info['profile']}",
            }.get(shell, f"source {shell_info['profile']}")
            
            click.echo(f"\nTo activate completion now, run:\n  {reload_cmd}")
            click.echo("\nOr restart your terminal.")
        except Exception as e:
            click.echo(f"Failed to install completion: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("Current Session Activation:")
        click.echo(shell_info["eval"])
        click.echo("")
        click.echo(f"Permanent Activation (add to {shell_info['profile']}):")
        click.echo(f"echo '{shell_info['eval']}' >> {shell_info['profile']}")
        click.echo("")
        click.echo("Or run: cmc completion --install")