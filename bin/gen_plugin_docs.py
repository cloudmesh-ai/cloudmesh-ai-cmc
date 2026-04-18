import os
import sys
from cloudmesh.ai.cmc.registry import CommandRegistry

def generate_docs():
    registry = CommandRegistry()
    config = registry.load_config()
    
    if not config:
        print("No plugins registered in registry. Nothing to document.")
        return

    output_path = "cloudmesh-ai.github.io/sphinx-docs/plugins_gallery.rst"
    
    with open(output_path, "w") as f:
        f.write("Plugin Gallery\n")
        f.write("=============\n\n")
        f.write("This page provides an overview of all registered CMC plugins.\n\n")
        
        for name, info in config.items():
            path = info["path"]
            try:
                module = registry._load_extension(name, path)
                if module:
                    description = getattr(module, "description", "No description provided.")
                    version = getattr(module, "version", "unknown")
                    
                    # Extract docstring from entry_point
                    entry_point = getattr(module, "entry_point", None)
                    docstring = entry_point.__doc__ if entry_point and entry_point.__doc__ else "No detailed documentation provided."
                    
                    f.write(f"{name}\n")
                    f.write("-" * len(name) + "\n")
                    f.write(f"**Version:** {version}\n\n")
                    f.write(f"**Description:** {description}\n\n")
                    f.write(f"**Details:**\n\n    {docstring}\n\n")
                    f.write("\n")
                else:
                    f.write(f"{name}\n")
                    f.write("-" * len(name) + "\n")
                    f.write("Failed to load plugin for documentation.\n\n")
            except Exception as e:
                f.write(f"{name}\n")
                f.write("-" * len(name) + "\n")
                f.write(f"Error extracting documentation: {e}\n\n")

    print(f"Successfully generated plugin gallery at {output_path}")

if __name__ == "__main__":
    generate_docs()