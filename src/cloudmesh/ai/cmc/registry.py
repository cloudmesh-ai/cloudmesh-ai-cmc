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
import logging
from cloudmesh.ai.cmc.utils import PluginDependencyError, PluginVersionError

logger = logging.getLogger("cmc")

# Default path for the registry configuration
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/cloudmesh-ai/cmc-registry.json")
# Allow override via environment variable
CONFIG_PATH = os.getenv("CMC_REGISTRY_PATH", DEFAULT_CONFIG_PATH)

def get_version(path):
    """Reads the version from a VERSION file in the provided path."""
    version_file = os.path.join(path, "VERSION")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            return f.read().strip()
    return "unknown"

def version_ge(v1, v2):
    """Simple semantic version comparison: returns True if v1 >= v2."""
    def parse(v):
        return [int(x) for x in v.split('.') if x.isdigit()]
    return parse(v1) >= parse(v2)

import click

class LazyCommand(click.Command):
    """Proxy object that holds metadata for a command to be loaded lazily."""
    def __init__(self, name, path=None, module_name=None, entry_point_name="entry_point"):
        super().__init__(name=name, help=f"Lazy loaded command: {name}")
        self.name = name
        self.path = path
        self.module_name = module_name
        self.entry_point_name = entry_point_name

    def __repr__(self):
        return f"LazyCommand(name={self.name})"

class CommandRegistry:
    def __init__(self, config_path=None):
        self._loading_stack = set()
        self.config_path = config_path or CONFIG_PATH
        
        # Ensure the directory exists
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            
        if not os.path.exists(self.config_path):
            self.save({})
        
    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                return self._validate_config_structure(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _validate_config_structure(self, data):
        """
        Validates that the registry JSON has the expected structure:
        { "ext_name": { "path": "...", "active": bool, "dependencies": [] }, ... }
        """
        logger.debug(f"_validate_config_structure called with data: {data}")
        if not isinstance(data, dict):
            logger.error(f"Registry config at {self.config_path} is not a JSON object.")
            return {}

        valid_data = {}
        for name, info in data.items():
            if isinstance(info, dict) and "path" in info and "active" in info:
                # Ensure dependencies is always a list
                if "dependencies" in info and not isinstance(info["dependencies"], list):
                    logger.warning(f"Invalid dependencies for '{name}': expected list. Resetting to [].")
                    info["dependencies"] = []
                elif "dependencies" not in info:
                    info["dependencies"] = []
                valid_data[name] = info
            else:
                logger.warning(f"Skipping invalid registry entry for '{name}': expected dict with 'path' and 'active'.")
        
        logger.debug(f"_validate_config_structure returning valid_data: {valid_data}")
        return valid_data

    def save(self, data):
        """Saves the registry configuration atomically using a temporary file."""
        temp_path = f"{self.config_path}.tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, self.config_path)
        except Exception as e:
            logger.error(f"Failed to save registry atomically: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def register(self, name, path, dependencies=None):
        config = self.load_config()
        key = name if name else os.path.basename(os.path.abspath(path))
        
        # If dependencies aren't provided, try to extract them from the module
        if dependencies is None:
            try:
                # Temporary load to extract metadata
                module = self._load_extension_metadata(key, path)
                if module:
                    dependencies = getattr(module, "dependencies", [])
            except Exception:
                dependencies = []
        
        config[key] = {
            "path": os.path.abspath(path),
            "active": True,
            "dependencies": dependencies or []
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

    def _load_extension_metadata(self, name, path):
        """Loads a module without resolving dependencies to extract metadata."""
        module_name = f"cloudmesh.ai.cmc.meta_{name}"
        cmd_file = os.path.join(path, "cmd.py")
        if not os.path.exists(cmd_file):
            return None
        spec = importlib.util.spec_from_file_location(module_name, cmd_file)
        if spec is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _load_extension(self, name, path):
        """
        Helper to dynamically load an extension module from a path.
        Returns the module if successful and valid, otherwise None.
        Includes circular dependency detection and dependency resolution.
        """
        if name in self._loading_stack:
            logger.error(f"Circular dependency detected while loading extension '{name}'")
            return None
        
        # 1. Resolve and load dependencies first
        config = self.load_config()
        info = config.get(name, {})
        dependencies = info.get("dependencies", [])
        
        for dep_name in dependencies:
            dep_info = config.get(dep_name)
            if not dep_info:
                raise PluginDependencyError(
                    f"Dependency Missing: Extension '{name}' requires '{dep_name}', "
                    f"but '{dep_name}' is not registered in the CMC registry."
                )
            if not dep_info.get("active", True):
                raise PluginDependencyError(
                    f"Dependency Inactive: Extension '{name}' requires '{dep_name}', "
                    f"but '{dep_name}' is currently disabled. Please enable it first."
                )
            
            # Recursively load the dependency
            if not self._load_extension(dep_name, dep_info["path"]):
                raise PluginDependencyError(f"Load Failure: Failed to load dependency '{dep_name}' required by '{name}'.")

        self._loading_stack.add(name)
        try:
            module_name = f"cloudmesh.ai.cmc.ext_{name}"
            cmd_file = os.path.join(path, "cmd.py")
            
            if not os.path.exists(cmd_file):
                return None
            
            # Add the 'src' directory to sys.path if it exists, to allow imports from the extension
            src_path = os.path.join(path, "src")
            if os.path.exists(src_path):
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)
            
            # Debugging: log sys.path to verify the src_path is present
            logger.debug(f"sys.path[0] is {sys.path[0]}")

            spec = importlib.util.spec_from_file_location(module_name, cmd_file)
            if spec is None:
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            if self._validate_extension(name, module):
                return module
        except Exception as e:
            import traceback
            logger.debug(f"Error loading extension '{name}': {e}")
            logger.debug(traceback.format_exc())
        finally:
            self._loading_stack.remove(name)
        return None

    def _validate_extension(self, name, module):
        """
        Validates that the loaded module has a valid entry_point and recommended metadata.
        """
        logger.debug(f"_validate_extension called for {name}")
        
        # Check for minimum CMC version requirement
        if hasattr(module, 'min_cmc_version'):
            cmc_version = get_version(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            if not version_ge(cmc_version, module.min_cmc_version):
                raise PluginVersionError(f"Extension '{name}' requires CMC version {module.min_cmc_version} or higher (current: {cmc_version})")

        if not hasattr(module, 'entry_point'):
            logger.debug(f"Validation failed for {name}: Missing entry_point")
            logger.error(f"Validation failed for '{name}': Missing 'entry_point' in cmd.py")
            return False
        
        logger.debug(f"entry_point for {name} is {module.entry_point} (type: {type(module.entry_point)})")
        if not callable(module.entry_point):
            logger.debug(f"Validation failed for {name}: entry_point is not callable")
            logger.error(f"Validation failed for '{name}': 'entry_point' must be a callable (e.g., a Click command)")
            return False

        # Check for recommended metadata
        for attr in ['version', 'description']:
            if not hasattr(module, attr):
                logger.warning(f"Extension '{name}' is missing recommended metadata: {attr}")
            
        logger.debug(f"Validation succeeded for {name}")
        return True

    def get_active_commands(self):
        """Returns the actual command objects (eager loading)."""
        config = self.load_config()
        commands = {}
        for name, info in config.items():
            if not info.get("active", False):
                continue
            try:
                module = self._load_extension(name, info["path"])
                if module:
                    commands[name] = module.entry_point
            except (PluginDependencyError, PluginVersionError) as e:
                logger.error(f"Skipping plugin '{name}': {e}")
        return commands

    def get_lazy_commands(self):
        """Returns LazyCommand proxies instead of importing modules."""
        config = self.load_config()
        lazy_cmds = {}
        for name, info in config.items():
            if not info.get("active", True):
                continue
            lazy_cmds[name] = LazyCommand(
                name=name, 
                path=info["path"], 
                module_name=f"cloudmesh.ai.cmc.ext_{name}"
            )
        return lazy_cmds
    
    def inject_commands(self, cli):
        """
        The Click "Bridge": 
        Iterates through the registry, dynamically imports 'cmd.py' from 
        each path, and attaches the 'entry_point' to the main CLI group.
        """
        config = self.load_config()
        for name, info in config.items():
            if not info.get("active", True):
                continue
            try:
                module = self._load_extension(name, info["path"])
                if module:
                    cli.add_command(module.entry_point, name=name)
            except (PluginDependencyError, PluginVersionError) as e:
                logger.error(f"Skipping plugin '{name}': {e}")
