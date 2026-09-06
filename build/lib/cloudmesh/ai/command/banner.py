import click
import io

from cloudmesh.ai.common.io import console


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
        panel = console.create_banner("", text[0])
    else:
        # Multiple arguments: first is title, rest is content
        title = text[0]
        content = "\n".join(text[1:])
        panel = console.create_banner(title, content)

    if char:
        # Capture the rendered panel to a string to add the prefix
        # We subtract the length of the comment character from the terminal width
        # so that the final result (prefix + panel) fills exactly 100% of the terminal.
        term_width = console.width
        adjusted_width = term_width - len(comment_char)
        # We still need a separate console for the buffer to capture the rendered panel
        from rich.console import Console as RichConsole
        console_buffer = RichConsole(file=io.StringIO(), width=adjusted_width, force_terminal=False)
        console_buffer.print(panel)
        rendered_text = console_buffer.file.getvalue()
        
        # Prefix each line with the comment character
        lines = rendered_text.splitlines()
        prefixed_lines = [f"{comment_char}{line}" for line in lines]
        
        # Print the final result using the shared console
        console.print("\n".join(prefixed_lines))
    else:
        # Just print the panel normally
        console.print(panel)

def register(cli):
    cli.add_command(banner, name="banner")
