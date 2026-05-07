# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import pkgutil
import importlib
import os
import sys
import functools
import traceback
import copy
from pathlib import Path
from typing import Any, Dict, Optional

from cloudmesh.ai.common import logging as ai_log
from cloudmesh.ai.common.io import console, load_yaml, dump_yaml, path_expand

class CMCError(Exception):
    """Base class for CMC exceptions."""
    pass

class PluginDependencyError(CMCError):
    """Raised when a plugin dependency is missing or inactive."""
    pass

class PluginVersionError(CMCError):
    """Raised when a plugin version is incompatible."""
    pass

logger = ai_log.get_logger("cmc.utils")

class Config:
    """Handles configuration for CMC from a YAML file."""
    
    DEFAULT_CONFIG_PATH = Path(path_expand("~/.config/cloudmesh/cmc.yaml"))
    
    DEFAULTS = {
        "telemetry": {
            "enabled": True,
            "path": "~/cmc_telemetry.jsonl",
            "backend": "json"
        },
        "logging": {
            "level": "WARNING"
        }
    }

    SCHEMA = {
        "telemetry.enabled": {"type": bool, "desc": "Enable or disable telemetry collection"},
        "telemetry.path": {"type": str, "desc": "Path to the telemetry log file"},
        "telemetry.backend": {"type": str, "desc": "Telemetry backend (e.g., 'json', 'text')"},
        "logging.level": {"type": str, "desc": "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"},
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initializes the Config object.

        Args:
            config_path (Optional[Path]): Path to the configuration file. 
                Defaults to DEFAULT_CONFIG_PATH if not provided.
        """
        self.path = config_path or self.DEFAULT_CONFIG_PATH
        self.data = copy.deepcopy(self.DEFAULTS)
        self._load_config()

    def _load_config(self):
        """Loads configuration from the YAML file on disk and updates defaults."""
        user_config = load_yaml(str(self.path))
        if user_config:
            self._deep_update(self.data, user_config)

    def _deep_update(self, base: Dict, update: Dict):
        """Recursively updates a dictionary.

        Args:
            base (Dict): The dictionary to be updated.
            update (Dict): The dictionary containing updates to apply.
        """
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def get(self, key_path: str, default: Any = None) -> Any:
        """Gets a value from the config using a dot-separated path.

        Environment variables can override config values. For example, 
        'telemetry.path' can be overridden by 'CMC_TELEMETRY_PATH'.

        Args:
            key_path (str): Dot-separated path to the configuration value.
            default (Any, optional): Value to return if the key is not found. Defaults to None.

        Returns:
            Any: The configuration value or the default value.
        """
        # 1. Check for environment variable override
        env_var = f"CMC_{key_path.replace('.', '_').upper()}"
        env_val = os.environ.get(env_var)
        if env_val is not None:
            # Try to cast to the type specified in SCHEMA
            if key_path in self.SCHEMA:
                expected_type = self.SCHEMA[key_path]["type"]
                try:
                    if expected_type is bool:
                        return env_val.lower() in ("true", "1", "yes")
                    return expected_type(env_val)
                except (ValueError, TypeError):
                    logger.warning(f"Environment variable {env_var} has invalid value '{env_val}' for type {expected_type.__name__}. Using config value.")
            else:
                return env_val

        # 2. Fallback to config data
        keys = key_path.split(".")
        val = self.data
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

    def validate(self, key_path: str, value: Any):
        """Validates a configuration value against the schema if it exists.

        Args:
            key_path (str): Dot-separated path to the configuration value.
            value (Any): The value to validate.

        Raises:
            TypeError: If the value does not match the expected type in the schema.
        """
        if key_path in self.SCHEMA:
            expected_type = self.SCHEMA[key_path]["type"]
            if not isinstance(value, expected_type):
                raise TypeError(f"Invalid type for '{key_path}'. Expected {expected_type.__name__}, got {type(value).__name__}.")
        # If not in SCHEMA, we allow it (dynamic plugin configuration)

    def set(self, key_path: str, value: Any):
        """Sets a value in the config using a dot-separated path.

        Args:
            key_path (str): Dot-separated path to the configuration value.
            value (Any): The value to set.
        """
        self.validate(key_path, value)
        keys = key_path.split(".")
        val = self.data
        for k in keys[:-1]:
            if k not in val or not isinstance(val[k], dict):
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value

    def save(self):
        """Saves the current configuration to the YAML file.

        Raises:
            Exception: If the configuration file cannot be saved.
        """
        dump_yaml(str(self.path), self.data)

def handle_errors(func):
    """Decorator to provide standardized error handling for CMC commands.

    Logs the full traceback for developers, emits a telemetry failure if 
    available, and displays a clean, user-friendly error message.

    Args:
        func (Callable): The function to be wrapped.

    Returns:
        Callable: The wrapped function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 1. Log the full traceback for developers
            logger.exception(f"Unhandled exception in {func.__name__}: {str(e)}")
            
            # 2. Try to emit telemetry failure if telemetry is available in the global scope
            try:
                from cloudmesh.ai.cmc.main import telemetry
                telemetry.fail(error=str(e), function=func.__name__)
            except ImportError:
                pass

            # 3. Show clean error to user
            if isinstance(e, PluginDependencyError):
                console.print(f"\n[bold red]Dependency Error:[/bold red] {str(e)}")
                console.print("[yellow]Action: Ensure all required plugins are installed and active using 'cmc plugins list'.[/yellow]")
            elif isinstance(e, PluginVersionError):
                console.print(f"\n[bold red]Version Error:[/bold red] {str(e)}")
                console.print("[yellow]Action: Please update your CMC installation to the required version.[/yellow]")
            else:
                console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
                console.print("[dim]Check logs for full traceback.[/dim]")
            
            sys.exit(1)
    return wrapper

def register_group_extensions(parent_group, group_package, child_target=None):
    """Iteratively loads all modules in a package and calls their register() function.

    Args:
        parent_group (Any): The parent group to register extensions to.
        group_package (Module): The package containing the extension modules.
        child_target (Any, optional): An alternative target for registration. 
            Defaults to parent_group if not provided.
    """
    target = child_target or parent_group

    for loader, module_name, is_pkg in pkgutil.iter_modules(group_package.__path__):
        full_name = f"{group_package.__name__}.{module_name}"
        try:
            module = importlib.import_module(full_name)
            if hasattr(module, "register"):
                module.register(target)
        except Exception as e:
            logger.error(f"Error loading extension {full_name}: {e}")