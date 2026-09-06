import click
import cloudmesh.ai.command.sys as sys_ext
from cloudmesh.ai.cmc.utils import register_group_extensions

@click.group(name="sys", help="System information and diagnostic tools.")
def sys_group():
    """System information and diagnostic tools."""
    pass

def register(cli):
    """Registers the sys group to the main CLI."""
    cli.add_command(sys_group)
    # Dynamically load all sub-commands in cme/extension/sys/
    register_group_extensions(sys_group, sys_ext)