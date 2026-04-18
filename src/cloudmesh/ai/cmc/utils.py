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
import yaml
import functools
import traceback
from pathlib import Path
from typing import Any, Dict, Optional
from rich.console import Console

from cloudmesh.ai.common import logging as ai_log

class CMCError(Exception):
    """Base class for CMC exceptions."""
    pass

class PluginDependencyError(CMCError):
    """Raised when a plugin dependency is missing or inactive."""
    pass

class PluginVersionError(CMCError):
    """Raised when a plugin version is incompatible."""
    pass

console = Console()
logger = ai_log.get_logger("cmc.utils")

class Config:
    """Handles configuration for CMC from a YAML file."""
    
    DEFAULT_CONFIG_PATH = Path("~/.config/cloudmesh/ai/cmc.yaml").expanduser()
    
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
        self.path = config_path or self.DEFAULT_CONFIG_PATH
        self.data = self.DEFAULTS.copy()
        self._load_config()

    def _load_config(self):
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._deep_update(self.data, user_config)
            except Exception as e:
                logger.warning(f"Could not load config file {self.path}: {e}")

    def _deep_update(self, base: Dict, update: Dict):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a value from the config using a dot-separated path (e.g., 'telemetry.enabled').
        Environment variables can override config values (e.g., 'telemetry.path' -> 'CMC_TELEMETRY_PATH').
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
        """Validates a configuration value against the schema."""
        if key_path not in self.SCHEMA:
            raise KeyError(f"Configuration key '{key_path}' is not recognized.")
        
        expected_type = self.SCHEMA[key_path]["type"]
        if not isinstance(value, expected_type):
            raise TypeError(f"Invalid type for '{key_path}'. Expected {expected_type.__name__}, got {type(value).__name__}.")

    def set(self, key_path: str, value: Any):
        """Set a value in the config using a dot-separated path (e.g., 'telemetry.enabled')."""
        self.validate(key_path, value)
        keys = key_path.split(".")
        val = self.data
        for k in keys[:-1]:
            if k not in val or not isinstance(val[k], dict):
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value

    def save(self):
        """Saves the current configuration to the YAML file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w") as f:
                yaml.dump(self.data, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Could not save config file {self.path}: {e}")
            raise

def handle_errors(func):
    """
    Decorator to provide standardized error handling for CMC commands.
    Logs full traceback, emits telemetry failure, and shows clean error to user.
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
    """
    Generic helper to iteratively load all modules in a package
    and call their register() function.
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