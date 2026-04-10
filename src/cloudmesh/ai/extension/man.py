import click
import sys
from datetime import date

# ==============================================================================
# FORMATTERS: The "Engine"
# ==============================================================================

class BaseFormatter:
    """Base class for all formatters to ensure consistent interface."""
    def format_header(self, date): return ""
    def format_single(self, ctx, name, cmd): 
        with click.Context(cmd, info_name=name, parent=ctx.parent) as sub_ctx:
            return f"{name.upper()}\n{'-'*len(name)}\n{cmd.help or ''}\n\n{cmd.get_help(sub_ctx)}\n\n"
    def format_footer(self): return ""

class HTMLFormatter(BaseFormatter):
    def format_header(self, date):
        return (
            f"<!DOCTYPE html>\n<html>\n<head>\n"
            f"<title>CME Manual</title>\n"
            f"<style>body{{font-family:sans-serif; margin:40px;}} pre{{background:#f4f4f4; padding:10px;}}</style>\n"
            f"</head>\n<body>\n<h1>CME Manual</h1><p>Generated on {date}</p>\n<hr>\n"
        )
    def format_single(self, ctx, name, cmd):
        with click.Context(cmd, info_name=name, parent=ctx.parent) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return f"<section><h2>{name}</h2><p>{cmd.help or ''}</p><pre>{help_text}</pre></section>\n"
    def format_footer(self):
        return "</body>\n</html>"

class MarkdownFormatter(BaseFormatter):
    def format_header(self, date):
        return f"# CME Manual\nGenerated on {date}\n\n"
    def format_single(self, ctx, name, cmd):
        with click.Context(cmd, info_name=name, parent=ctx.parent) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return f"## {name}\n\n{cmd.help or ''}\n\n```text\n{help_text}\n```\n\n"

class RSTFormatter(BaseFormatter):
    def format_header(self, date):
        title = "CME Manual"
        return f"{'='*len(title)}\n{title}\n{'='*len(title)}\nGenerated on {date}\n\n"
    def format_single(self, ctx, name, cmd):
        with click.Context(cmd, info_name=name, parent=ctx.parent) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            return f"{name}\n{'-'*len(name)}\n\n{cmd.help or ''}\n\n::\n\n    " + help_text.replace("\n", "\n    ") + "\n\n"

class QMDFormatter(MarkdownFormatter):
    """Quarto Markdown Formatter."""
    def format_header(self, date):
        return f"---\ntitle: \"CME Manual\"\ndate: \"{date}\"\nformat: html\n---\n\n"

class GroffFormatter(BaseFormatter):
    """Groff (Man page) Formatter."""
    def format_header(self, date):
        return f".TH CME 1 \"{date}\" \"CME\" \"User Commands\"\n.SH NAME\ncme \\- Custom Managed Extensions\n"
    def format_single(self, ctx, name, cmd):
        with click.Context(cmd, info_name=name, parent=ctx.parent) as sub_ctx:
            help_text = cmd.get_help(sub_ctx)
            # Basic escaping for groff
            help_text = help_text.replace("-", "\\-")
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

def generate_manual(ctx, cli, format_name="text"):
    """
    The CORE function that iterates through the Click CLI 
    and produces formatted documentation.
    """
    formatter = get_formatter(format_name)
    output = []
    
    # 1. Header
    output.append(formatter.format_header(date.today().strftime("%Y-%m-%d")))
    
    # 2. Commands
    # We sort to keep it deterministic
    sorted_commands = sorted(cli.list_commands(ctx))
    
    for name in sorted_commands:
        cmd = cli.get_command(ctx, name)
        if cmd:
            output.append(formatter.format_single(ctx, name, cmd))
            
    # 3. Footer
    output.append(formatter.format_footer())
    
    return "".join(output)

def register(cli):
    """
    Placeholder register function. 
    Man is currently called from cloudmesh.ai.extension.command.cmd_man
    """
    pass
