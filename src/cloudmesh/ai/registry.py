# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import json
import os
import importlib.util
import sys

CONFIG_PATH = os.path.expanduser("~/.cme_registry.json")

def get_version(path):
    """Reads the version from a VERSION file in the provided path."""
    version_file = os.path.join(path, "VERSION")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            return f.read().strip()
    return "unknown"

class CommandRegistry:
    def __init__(self):
        if not os.path.exists(CONFIG_PATH):
            self.save({})
        
    def load_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self, data):
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def register(self, name, path):
        config = self.load_config()
        key = name if name else os.path.basename(os.path.abspath(path))
        config[key] = {
            "path": os.path.abspath(path),
            "active": True
        }
        self.save(config)

    def set_status(self, name, status):
        config = self.load_config()
        if name in config:
            config[name]["active"] = status
            self.save(config)
            return True
        return False

    def unregister(self, name):
        config = self.load_config()
        if name in config:
            del config[name]
            self.save(config)

    def list_all_details(self):
        config = self.load_config()
        details = []
        for name, info in config.items():
            version = get_version(info["path"])
            details.append({
                "name": name,
                "active": info["active"],
                "version": version,
                "path": info["path"]
            })
        return details

    def get_active_commands(self):
        config = self.load_config()
        commands = {}
        for name, info in config.items():
            if not info.get("active", False):
                continue
            try:
                module_name = f"cloudmesh.ai.ext_{name}"
                cmd_file = os.path.join(info["path"], "cmd.py")
                if not os.path.exists(cmd_file):
                    continue
                
                spec = importlib.util.spec_from_file_location(module_name, cmd_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                commands[name] = module.entry_point
            except Exception as e:
                print(f"Error loading {name}: {e}")
        return commands
    
    def inject_commands(self, cli):
        """
        The Click "Bridge": 
        Iterates through the registry, dynamically imports 'cmd.py' from 
        each path, and attaches the 'entry_point' to the main CLI group.
        """
        config = self.load_config()
        
        for name, info in config.items():
            # Skip if deactivated
            if not info.get("active", True):
                continue
                
            try:
                # Create a unique internal module name to avoid collisions
                module_name = f"cloudmesh.ai.ext_{name}"
                
                # Extensions MUST have a cmd.py file in their directory
                cmd_file = os.path.join(info["path"], "cmd.py")
                
                if not os.path.exists(cmd_file):
                    # Silently skip if the file was deleted but is still in registry
                    continue
                
                # Dynamic Python Import Logic
                spec = importlib.util.spec_from_file_location(module_name, cmd_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Attach to Click
                # We look for a function/object named 'entry_point' in the loaded file
                if hasattr(module, 'entry_point'):
                    cli.add_command(module.entry_point, name=name)
                    
            except Exception as e:
                # Log error but don't crash the entire CLI for one bad plugin
                print(f"Error loading extension '{name}': {e}")
