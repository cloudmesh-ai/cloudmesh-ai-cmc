import click
import cloudmesh.ai.command.markdown as markdown_ext
from cloudmesh.ai.cmc.utils import register_group_extensions

@click.group(name="markdown", help="Markdown utility tools for cleaning and formatting.")
def markdown_group():
    """Markdown utility tools for cleaning and formatting."""
    pass

@markdown_group.group(name="fix")
def fix_group():
    """Fix common formatting issues in markdown files."""
    pass

def register(cli):
    """Registers the markdown group and its sub-commands to the main CLI."""
    cli.add_command(markdown_group)
    # Register children specifically to the 'fix' subgroup
    register_group_extensions(markdown_group, markdown_ext, child_target=fix_group)