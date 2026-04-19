import pytest
from unittest.mock import patch, MagicMock
import click
from cloudmesh.ai.cmc.main import cli, load_core_extensions, load_pip_extensions, LazyCommand, SubcommandHelpGroup

def test_load_core_extensions():
    """Verify that core extensions are loaded into the CLI."""
    # Core extensions are loaded at module level in main.py, 
    # but we can call it again on a fresh group to verify.
    test_cli = click.Group(name="test_cli")
    load_core_extensions(test_cli)
    
    # Check if some known core commands are present
    # Based on ls -R, we have 'version', 'telemetry', 'shell', etc.
    assert "version" in test_cli.commands
    assert "telemetry" in test_cli.commands
    assert "shell" in test_cli.commands

def test_load_pip_extensions():
    """Verify that pip extensions are loaded as LazyCommands."""
    test_cli = click.Group(name="test_cli")
    
        # Mock entry_points().select()
    mock_ep = MagicMock()
    mock_ep.name = "pip_cmd"
    mock_ep.value = "some_module:entry_point"
    
    with patch("cloudmesh.ai.cmc.main.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = [mock_ep]
        load_pip_extensions(test_cli)
        
        assert "pip_cmd" in test_cli.commands
        assert isinstance(test_cli.commands["pip_cmd"], LazyCommand)
        assert test_cli.commands["pip_cmd"].module_name == "some_module"
        assert test_cli.commands["pip_cmd"].entry_point_name == "entry_point"

def test_lazy_command_resolution():
    """Verify that SubcommandHelpGroup resolves LazyCommand to a real command."""
    # Create a group using the custom SubcommandHelpGroup
    group = SubcommandHelpGroup(name="test_group")
    
    # Add a LazyCommand
    lazy_cmd = LazyCommand(
        name="lazy_cmd",
        module_name="cloudmesh.ai.command.version",
        entry_point_name="entry_point"
    )
    group.commands["lazy_cmd"] = lazy_cmd
    
    # Resolve the command
    resolved_cmd = group.get_command(None, "lazy_cmd")
    
    assert resolved_cmd is not None
    # It should no longer be a LazyCommand
    assert not isinstance(resolved_cmd, LazyCommand)
    # It should be a click object
    assert isinstance(resolved_cmd, (click.Command, click.Group))

def test_lazy_command_failure():
    """Verify that failure to load a LazyCommand is handled gracefully."""
    group = SubcommandHelpGroup(name="test_group")
    
    lazy_cmd = LazyCommand(
        name="fail_cmd",
        module_name="non_existent_module",
        entry_point_name="entry_point"
    )
    group.commands["fail_cmd"] = lazy_cmd
    
    # Should return None and log an error instead of crashing
    resolved_cmd = group.get_command(None, "fail_cmd")
    assert resolved_cmd is None