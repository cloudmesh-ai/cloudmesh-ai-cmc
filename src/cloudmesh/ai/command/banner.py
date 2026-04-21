import click
import io

from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED

from cloudmesh.ai.common.io import banner as banner_func


@click.command()
@click.option("--char", "-c", is_flag=True, default=False, help="Prefix each line with #")
@click.option("--comment-char", default="#", help="Character to use for comments when -c is used")
@click.argument("text", nargs=-1, required=True)
def banner(char, comment_char, text):
    """
    A simple command to print a text banner using the professional 
    cloudmesh-ai common panel.
    """
    if len(text) == 1:
        # Only one argument: use it as content, title is empty
        panel = banner_func("", text[0])
    else:
        # Multiple arguments: first is title, rest is content
        title = text[0]
        content = "\n".join(text[1:])
        panel = banner_func(title, content)

    if char:
        # Capture the rendered panel to a string to add the prefix
        # We subtract the length of the comment character from the terminal width
        # so that the final result (prefix + panel) fills exactly 100% of the terminal.
        term_width = Console().width
        adjusted_width = term_width - len(comment_char)
        console_buffer = Console(file=io.StringIO(), width=adjusted_width, force_terminal=False)
        console_buffer.print(panel)
        rendered_text = console_buffer.file.getvalue()
        
        # Prefix each line with the comment character
        lines = rendered_text.splitlines()
        prefixed_lines = [f"{comment_char}{line}" for line in lines]
        
        # Print the final result using the standard console
        Console().print("\n".join(prefixed_lines))
    else:
        # Just print the panel normally
        Console().print(panel)

def register(cli):
    cli.add_command(banner, name="banner")
