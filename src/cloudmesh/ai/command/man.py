import click
import sys
import subprocess
import tempfile
import os
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
            pass
            
        # Use the parent context or current context to avoid recursion depth issues
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return (
                f"{name.upper()}\n"
                f"{'='*len(name)}\n\n"
                f"DESCRIPTION\n"
                f"-----------\n"
                f"{cmd.help or 'No description available.'}\n\n"
                f"USAGE\n"
                f"-----\n"
                f"{help_text}\n\n"
            )
    
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
            return (
                f"<section>\n"
                f"  <h2>{name.upper()}</h2>\n"
                f"  <h3>Description</h3>\n"
                f"  <p>{cmd.help or 'No description available.'}</p>\n"
                f"  <h3>Usage</h3>\n"
                f"  <pre>{help_text}</pre>\n"
                f"</section>\n"
            )
    def format_footer(self):
        return "</body>\n</html>"

class MarkdownFormatter(BaseFormatter):
    def format_header(self, date_str):
        return f"# CME Manual\nGenerated on {date_str}\n\n---\n\n"
    def format_single(self, ctx, name, cmd):
        # Remove the incorrect get_command call that crashes on DelegatingCommand
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return (
                f"## {name.upper()}\n\n"
                f"### Description\n"
                f"{cmd.help or 'No description available.'}\n\n"
                f"### Usage\n"
                f"```text\n{help_text}\n```\n\n"
            )

class RSTFormatter(BaseFormatter):
    def format_header(self, date_str):
        title = "CME Manual"
        return f"{'='*len(title)}\n{title}\n{'='*len(title)}\nGenerated on {date_str}\n\n"
    def format_single(self, ctx, name, cmd):
        # Remove the incorrect get_command call that crashes on DelegatingCommand
        with click.Context(cmd, info_name=name, parent=ctx) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            indented_help = "    " + help_text.replace("\n", "\n    ")
            return (
                f"{name.upper()}\n"
                f"{'='*len(name)}\n\n"
                f"**Description**\n\n"
                f"{cmd.help or 'No description available.'}\n\n"
                f"**Usage**\n\n"
                f"::\n\n"
                f"{indented_help}\n\n"
            )

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
            return (
                f".SH {name.upper()}\n"
                f".TP\n"
                f"Description\n"
                f"{cmd.help or 'No description available.'}\n"
                f".TP\n"
                f"Usage\n"
                f".nf\n"
                f"{help_text}\n"
                f".fi\n"
            )

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
@click.option(
    "--pager", 
    is_flag=True, 
    help="Use a system pager to display the manual."
)
@click.pass_context
def man(ctx, command_name, format, pager):
    """Generate a manual for all available commands."""
    
    # Ensure we have the root group to look up commands
    root_ctx = ctx.find_root()
    cli = root_ctx.command
    

    if command_name:
        # Special case: 'cmc man cmc' should show the full manual for the root tool
        if command_name.lower() == "cmc":
            content = generate_manual(ctx, cli, format_name=format)
        else:
            # Look up a specific command within the group
            cmd = cli.get_command(ctx, command_name)
            if cmd:
                formatter = get_formatter(format)
                header = formatter.format_header(date.today().strftime("%Y-%m-%d"))
                content = formatter.format_single(ctx, command_name, cmd)
                footer = formatter.format_footer()
                content = f"{header}{content}{footer}"
            else:
                click.echo(f"Error: Command '{command_name}' not found.", err=True)
                return
    else:
        # Generate the full manual
        content = generate_manual(ctx, cli, format_name=format)

    if pager:
        if format.lower() == "groff":
            # Use system 'man' for groff format
            with tempfile.NamedTemporaryFile(mode='w', suffix='.1', delete=False) as tf:
                tf.write(content)
                temp_path = tf.name
            try:
                subprocess.run(["man", temp_path], check=True)
            finally:
                os.remove(temp_path)
        else:
            # Use 'less' for other formats
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
                tf.write(content)
                temp_path = tf.name
            try:
                subprocess.run(["less", temp_path], check=True)
            finally:
                os.remove(temp_path)
    else:
        click.echo(content)
