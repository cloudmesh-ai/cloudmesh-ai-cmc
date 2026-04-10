import os
import fnmatch
import click
from pathlib import Path
from rich.console import Console

console = Console()

# ==============================================================================
# LOGIC ENGINE (The "Worker" Class)
# ==============================================================================
class TreeEngine:
    """Handles the state and logic for directory traversal."""
    def __init__(self, path, show_content, exclude, include):
        self.base_path = Path(path).resolve()
        self.show_content = show_content
        self.user_excludes = self._parse_patterns(exclude)
        self.user_includes = self._parse_patterns(include)
        
        self.internal_ignore = {
            "__pycache__", ".git", ".idea", ".DS_Store", "node_modules",
            "*.pyc", "*.pyo", "*.pyd", ".pytest_cache", ".venv", "venv",
            "target", "dist", "build"
        }

    def _parse_patterns(self, pattern_str):
        if not pattern_str: return []
        return [p.strip() for p in pattern_str.split(",") if p.strip()]

    def should_ignore(self, path):
        rel_path = path.relative_to(self.base_path)
        name = path.name
        
        # 1. Check Internal Ignores (Always)
        for pattern in self.internal_ignore:
            if fnmatch.fnmatch(name, pattern): return True
            
        # 2. Check User Excludes
        for pattern in self.user_excludes:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(str(rel_path), pattern):
                return True
                
        # 3. Check User Includes (If provided, only include matches)
        if self.user_includes:
            match = False
            for pattern in self.user_includes:
                if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(str(rel_path), pattern):
                    match = True
                    break
            if not match: return True

        return False

    def build_tree(self, current_path=None, prefix=""):
        if current_path is None: current_path = self.base_path
        
        # List and filter contents
        try:
            items = sorted(list(current_path.iterdir()))
        except PermissionError:
            return

        items = [i for i in items if not self.should_ignore(i)]
        
        for index, item in enumerate(items):
            is_last = (index == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            # Print item name
            style = "[bold blue]" if item.is_dir() else "[green]"
            console.print(f"{prefix}{connector}{style}{item.name}[/]")

            # Optional: Print file content summary
            if self.show_content and item.is_file():
                self._print_file_preview(item, prefix + ("    " if is_last else "│   "))

            # Recurse if directory
            if item.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                self.build_tree(item, new_prefix)

    def _print_file_preview(self, path, prefix):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = [f.readline().strip() for _ in range(3)]
                lines = [l for l in lines if l]
                if lines:
                    for line in lines:
                        console.print(f"{prefix}[dim italic white]  {line}[/]")
        except (UnicodeDecodeError, PermissionError):
            pass

# ==============================================================================
# CLI COMMAND DEFINITION
# ==============================================================================
@click.command(name="tree")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--content", "-c", is_flag=True, help="Show first few lines of files")
@click.option("--exclude", "-e", help="Comma-separated glob patterns to exclude")
@click.option("--include", "-i", help="Comma-separated glob patterns to include")
def cmd_tree(path, content, exclude, include):
    """Display directory structure in a tree-like format."""
    console.print(f"[bold blue]{Path(path).resolve()}[/]")
    engine = TreeEngine(path, content, exclude, include)
    engine.build_tree()

def register(cli):
    cli.add_command(cmd_tree, name="tree")
