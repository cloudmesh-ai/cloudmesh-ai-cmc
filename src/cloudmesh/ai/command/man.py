import click
import sys
from datetime import date

# ==============================================================================
# FORMATTERS: The "Engine"
# ==============================================================================

class BaseFormatter:
    """Base class for all formatters to ensure consistent interface."""
    def format_header(self, date_str): 
        return f"CME Manual\nGenerated on {date_str}\n{'='*30}\n\n"
    
    def format_single(self, ctx, name, cmd): 
        # Resolve LazyCommand if necessary
        if hasattr(cmd, 'module_name') and hasattr(cmd, 'entry_point_name'):
            # This is a LazyCommand, we need to resolve it.
            # Since we are in a formatter, we can't easily call the group's get_command.
            # But we can try to resolve it manually or rely on the group to have done it.
            # Actually, the best way is to let the group handle it.
            # If it's still a LazyCommand here, it means the group didn't resolve it.
            pass
            
        # Use the parent context or current context to avoid recursion depth issues
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            return f"{name.upper()}\n{'-'*len(name)}\n{cmd.help or ''}\n\n{cmd.get_help(sub_ctx)}\n\n"
    
    def format_footer(self): 
        return ""

class HTMLFormatter(BaseFormatter):
    def format_header(self, date_str):
        return (
            f"<!DOCTYPE html>\n<html>\n<head>\n"
            f"<title>CME Manual</title>\n"
            f"<style>\n"
            f"  body{{font-family:sans-serif; margin:40px; line-height:1.6; max-width:900px; color:#333;}}\n"
            f"  pre{{background:#f4f4f4; padding:15px; border-left:5px solid #007bff; overflow-x:auto; font-size:0.9em;}}\n"
            f"  h2{{color:#2c3e50; border-bottom:2px solid #eee; padding-bottom:10px; margin-top:40px; text-transform:uppercase;}}\n"
            f"  .date{{color:#777; font-style:italic;}}\n"
            f"</style>\n"
            f"</head>\n<body>\n<h1>CME Manual</h1><p class='date'>Generated on {date_str}</p>\n<hr>\n"
        )
    def format_single(self, ctx, name, cmd):
        # Remove the incorrect get_command call that crashes on DelegatingCommand
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return f"<section><h2>{name}</h2><p><strong>Description:</strong> {cmd.help or 'No description available.'}</p><pre>{help_text}</pre></section>\n"
    def format_footer(self):
        return "</body>\n</html>"

class MarkdownFormatter(BaseFormatter):
    def format_header(self, date_str):
        return f"# CME Manual\nGenerated on {date_str}\n\n---\n\n"
    def format_single(self, ctx, name, cmd):
        # Remove the incorrect get_command call that crashes on DelegatingCommand
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return f"## {name}\n\n{cmd.help or ''}\n\n```text\n{help_text}\n```\n\n"

class RSTFormatter(BaseFormatter):
    def format_header(self, date_str):
        title = "CME Manual"
        return f"{'='*len(title)}\n{title}\n{'='*len(title)}\nGenerated on {date_str}\n\n"
    def format_single(self, ctx, name, cmd):
        # Remove the incorrect get_command call that crashes on DelegatingCommand
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            indented_help = "    " + help_text.replace("\n", "\n    ")
            return f"{name}\n{'-'*len(name)}\n\n{cmd.help or ''}\n\n::\n\n{indented_help}\n\n"

class QMDFormatter(MarkdownFormatter):
    """Quarto Markdown Formatter."""
    def format_header(self, date_str):
        return f"---\ntitle: \"CME Manual\"\ndate: \"{date_str}\"\nformat: html\ntoc: true\n---\n\n"

class GroffFormatter(BaseFormatter):
    """Groff (Man page) Formatter."""
    def format_header(self, date_str):
        return f".TH CME 1 \"{date_str}\" \"CME\" \"User Commands\"\n.SH NAME\ncme \\- Custom Managed Extensions\n"
    def format_single(self, ctx, name, cmd):
        # Remove the incorrect get_command call that crashes on DelegatingCommand
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx).replace("-", "\\-")
            return f".SH {name.upper()}\n{cmd.help or ''}\n.PP\n.nf\n{help_text}\n.fi\n"

# ==============================================================================
# LOGIC: Generator
# ==============================================================================

def get_formatter(format_name):
    formatters = {
        "html": HTMLFormatter(),
        "markdown": MarkdownFormatter(),
        "md": MarkdownFormatter(),
        "rst": RSTFormatter(),
        "qmd": QMDFormatter(),
        "groff": GroffFormatter(),
        "text": BaseFormatter(),
        "txt": BaseFormatter()
    }
    return formatters.get(format_name.lower(), BaseFormatter())

def generate_manual(ctx, target_group, format_name="text"):
    """
    Iterates through a Click Group and produces documentation.
    """
    formatter = get_formatter(format_name)
    output = []
    
    output.append(formatter.format_header(date.today().strftime("%Y-%m-%d")))
    
    command_names = target_group.list_commands(ctx)

    if not command_names:
        return f"{output[0]}\nNo commands found in this group.\n"

    for name in sorted(command_names):
        # Prevent the 'man' command from documenting itself
        if name == ctx.command.name:
            continue
            
        cmd = target_group.get_command(ctx, name)
        if cmd and not cmd.hidden:
            output.append(formatter.format_single(ctx, name, cmd))
            
    output.append(formatter.format_footer())
    return "".join(output)

# ==============================================================================
# COMMAND DEFINITION
# ==============================================================================

@click.command(name="man")
@click.argument("command_name", required=False)
@click.option(
    "--format", "-f", 
    default="text", 
    type=click.Choice(["text", "md", "html", "rst", "qmd", "groff"], case_sensitive=False),
    help="The output format for the manual."
)
@click.pass_context
def man(ctx, command_name, format):
    """Generate a manual for all available commands."""
    
    # Ensure we have the root group to look up commands
    root_ctx = ctx.find_root()
    cli = root_ctx.command
    

    if command_name:
        # Look up a specific command within the group
        cmd = cli.get_command(ctx, command_name)
        if cmd:
            formatter = get_formatter(format)
            header = formatter.format_header(date.today().strftime("%Y-%m-%d"))
            content = formatter.format_single(ctx, command_name, cmd)
            footer = formatter.format_footer()
            click.echo(f"{header}{content}{footer}")
        else:
            click.echo(f"Error: Command '{command_name}' not found.", err=True)
    else:
        # Generate the full manual
        content = generate_manual(ctx, cli, format_name=format)
        click.echo(content)
