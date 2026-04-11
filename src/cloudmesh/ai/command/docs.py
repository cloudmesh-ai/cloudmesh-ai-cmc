import click
import importlib.resources
import logging
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme

logger = logging.getLogger("cmc")

@click.command(name="docs")
def docs():
    """Display documentation for cmc and extension development."""
    # Load the guide from the DOCS.md file in the package first
    try:
        # Use importlib.resources for namespace package compatibility
        resource_path = importlib.resources.files("cloudmesh.ai.cmc").joinpath("DOCS.md")
        guide = resource_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Could not load documentation file: {e}")
        click.echo("Error: Documentation file could not be loaded.", err=True)
        return

    # 1. Define a rich Theme to force the light grey background for code blocks.
    # This handles the background for both plain and syntax-highlighted blocks
    # by styling the rich renderable containers.
    custom_theme = Theme(
        {
            "code": "black on #f0f0f0",
            "block": "black on #f0f0f0",
            "markdown.code": "black on #f0f0f0",
            "markdown.block": "black on #f0f0f0",
            "markdown.text": "black on #f0f0f0",
            "markdown.python": "black on #f0f0f0",
        }
    )
    console = Console(theme=custom_theme)

    # Render the guide as Markdown using a standard Pygments theme.
    # The rich Theme defined above will handle the background color.
    markdown_content = Markdown(guide, code_theme="default")

    console.print(
        Panel(
            markdown_content,
            title="[bold blue]cmc Documentation[/bold blue]",
            border_style="blue",
            expand=False,
        )
    )

def register(cli):
    """Register the docs command to the main CLI."""
    cli.add_command(docs)