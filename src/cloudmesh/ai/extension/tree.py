"""
Cloudmesh AI Tree Extension
===========================

This extension provides tools to visualize file system hierarchies and
project structures in a tree-like format. It is designed to help users
and AI agents quickly understand the layout of a codebase or directory.

The tool includes an internal ignore list to filter out common noise
(like .git and __pycache__) and supports advanced glob-based filtering.

Usage Examples:
-------------------------------------------------------------------------------
1. Display the structure of the current directory:
   $ cme tree

2. Display a specific path and show previews of file contents:
   $ cme tree ./src --content

3. Exclude specific patterns (e.g., all .txt files):
   $ cme tree --exclude="*.txt"

4. Only show Python files using the include flag:
   $ cme tree --include="*.py"

5. Combine exclude and include for precise filtering:
   $ cme tree --include="*.py" --exclude="tests/*"
-------------------------------------------------------------------------------
"""

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
    """
    Handles the state and logic for directory traversal.

    This class manages the recursive traversal of the filesystem, applying
    internal and user-defined filters to determine which files and directories
    should be rendered in the final tree output.
    """

    def __init__(self, path, show_content, exclude, include):
        self.base_path = Path(path).resolve()
        self.show_content = show_content
        self.user_excludes = self._parse_patterns(exclude)
        self.user_includes = self._parse_patterns(include)
        self.internal_ignore = {
            "__pycache__",
            ".git",
            ".idea",
            ".DS_Store",
            "node_modules",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".pytest_cache",
            ".venv",
            "venv",
            "target",
            "dist",
            "build",
        }

    def _parse_patterns(self, pattern_str):
        """Splits a comma-separated string into a list of cleaned patterns."""
        if not pattern_str:
            return []
        return [p.strip() for p in pattern_str.split(",") if p.strip()]

    def should_ignore(self, path):
        """
        Determines if a file or directory should be hidden based on filter rules.

        Priority order:
        1. Internal Ignore List (Always hidden)
        2. User Excludes (Hidden if matched)
        3. User Includes (Hidden if provided but NOT matched)
        """
        rel_path = path.relative_to(self.base_path)
        name = path.name

        # 1. Check Internal Ignores (Always)
        for pattern in self.internal_ignore:
            if fnmatch.fnmatch(name, pattern):
                return True

        # 2. Check User Excludes
        for pattern in self.user_excludes:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(
                str(rel_path), pattern
            ):
                return True

        # 3. Check User Includes (If provided, only include matches)
        if self.user_includes:
            match = False
            for pattern in self.user_includes:
                if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(
                    str(rel_path), pattern
                ):
                    match = True
                    break
            if not match:
                return True

        return False

    def build_tree(self, current_path=None, prefix=""):
        """
        Recursively traverses the directory and prints the visual tree.

        Args:
            current_path (Path): The directory currently being scanned.
            prefix (str): The string prefix used for indentation and tree lines.
        """
        if current_path is None:
            current_path = self.base_path

        # List and filter contents
        try:
            items = sorted(list(current_path.iterdir()))
        except PermissionError:
            return

        items = [i for i in items if not self.should_ignore(i)]

        for index, item in enumerate(items):
            is_last = index == len(items) - 1
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
        """Prints the first 3 non-empty lines of a file as a preview."""
        try:
            with open(path, "r", encoding="utf-8") as f:
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
    """
    Display directory structure in a visual tree-like format.

    This command recursively scans the specified path and renders a hierarchy
    of folders and files. It uses 'Rich' to provide color-coded output and
    optional file content previews.

    Example:
        cme tree ./project --content --exclude="*.log"
    """
    console.print(f"[bold blue]{Path(path).resolve()}[/]")
    engine = TreeEngine(path, content, exclude, include)
    engine.build_tree()


def register(cli):
    """Registers the tree command with the main Cloudmesh AI CLI."""
    cli.add_command(cmd_tree, name="tree")
