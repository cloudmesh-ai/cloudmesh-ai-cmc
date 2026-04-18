import os
import pytest
import click
from cloudmesh.ai.cmc.registry import CommandRegistry
from cloudmesh.ai.cmc.utils import PluginDependencyError

def create_mock_plugin(path, name, version="1.0.0", description="Mock Plugin", dependencies=None, entry_point_code="def entry_point():\n    print('Hello from plugin')\nentry_point = entry_point"):
    """Helper to create a mock plugin directory structure."""
    os.makedirs(path, exist_ok=True)
    
    # Create VERSION file
    with open(os.path.join(path, "VERSION"), "w") as f:
        f.write(version)
    
    # Create cmd.py
    with open(os.path.join(path, "cmd.py"), "w") as f:
        f.write(f"version = '{version}'\n")
        f.write(f"description = '{description}'\n")
        f.write(entry_point_code + "\n")

def test_plugin_registration_and_loading(tmp_path):
    # Setup temporary registry
    registry_path = tmp_path / "registry.json"
    registry = CommandRegistry(config_path=str(registry_path))
    
    # Create mock plugin
    plugin_path = tmp_path / "plugin_a"
    create_mock_plugin(str(plugin_path), "plugin_a")
    
    # Register and load
    registry.register("plugin_a", str(plugin_path))
    commands = registry.get_active_commands()
    
    assert "plugin_a" in commands
    assert callable(commands["plugin_a"])

def test_plugin_dependency_resolution(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry = CommandRegistry(config_path=str(registry_path))
    
    # Plugin B (Dependency)
    path_b = tmp_path / "plugin_b"
    create_mock_plugin(str(path_b), "plugin_b")
    
    # Plugin A (Depends on B)
    path_a = tmp_path / "plugin_a"
    create_mock_plugin(str(path_a), "plugin_a")
    
    registry.register("plugin_b", str(path_b))
    registry.register("plugin_a", str(path_a), dependencies=["plugin_b"])
    
    # Should load without error
    commands = registry.get_active_commands()
    assert "plugin_a" in commands
    assert "plugin_b" in commands

def test_missing_dependency(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry = CommandRegistry(config_path=str(registry_path))
    
    path_a = tmp_path / "plugin_a"
    create_mock_plugin(str(path_a), "plugin_a")
    
    registry.register("plugin_a", str(path_a), dependencies=["non_existent"])
    
    # get_active_commands logs error and skips, but _load_extension raises PluginDependencyError
    with pytest.raises(PluginDependencyError):
        registry._load_extension("plugin_a", str(path_a))

def test_command_injection(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry = CommandRegistry(config_path=str(registry_path))
    
    path_a = tmp_path / "plugin_a"
    # Create a real click command for the mock plugin
    entry_point_code = (
        "import click\n"
        "@click.command()\n"
        "def entry_point():\n"
        "    click.echo('Plugin A executed')\n"
    )
    create_mock_plugin(str(path_a), "plugin_a", entry_point_code=entry_point_code)
    
    registry.register("plugin_a", str(path_a))
    
    @click.group()
    def cli():
        pass
    
    registry.inject_commands(cli)
    
    # Verify command is attached to the group
    assert "plugin_a" in cli.commands
