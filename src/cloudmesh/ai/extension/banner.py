import click

from rich.console import Console

# Initialize a global Rich console
# This automatically handles terminal detection and color support
console = Console()



@click.command()
@click.option("--char", "-c", default="#", help="The character to use")
@click.option("--width", "-n", default=70, type=int, help="The width of the banner")
@click.option("--indent", "-i", default=0, type=int, help="The indentation")
@click.option(
    "--color",
    "-r",
    default="black",
    help="Color name or hex (e.g., 'red', 'blue', '#ff00ff')",
)
@click.argument("text", nargs=-1, required=True)
def cmd_banner(char, width, indent, color, text):
    """
    BANNER: A simple command to print a text banner with customizable character,
    width, and color.
    """
    message = " ".join(text)
    
    # Calculate padding for centering
    padding = (width - len(message) - 2) // 2
    if padding < 0: padding = 0
    
    # Construction of parts
    line = char * width
    centered_text = f"{char}{' ' * padding}{message}{' ' * (width - len(message) - padding - 2)}{char}"
    
    # Indentation
    ind = " " * indent
    
    # Printing with Rich (using the console and style)
    style = f"bold {color}"
    console.print(f"{ind}{line}", style=style)
    console.print(f"{ind}{centered_text}", style=style)
    console.print(f"{ind}{line}", style=style)

def register(cli):
    cli.add_command(cmd_banner, name="banner")
