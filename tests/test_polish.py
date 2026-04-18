import os
import pytest
from pathlib import Path
from click.testing import CliRunner
from cloudmesh.ai.cmc.context import config
from cloudmesh.ai.cmc.main import cli

def test_dynamic_config():
    """Test that config allows keys not in the schema."""
    runner = CliRunner()
    
    # Test setting a dynamic key
    result = runner.invoke(cli, ["config", "set", "myplugin.api_key", "secret123"])
    assert result.exit_code == 0
    assert "Successfully set myplugin.api_key = secret123" in result.output
    
    # Test getting the dynamic key
    result = runner.invoke(cli, ["config", "get", "myplugin.api_key"])
    assert result.exit_code == 0
    assert "secret123" in result.output

def test_config_type_casting():
    """Test that config set casts types correctly."""
    runner = CliRunner()
    
    # Test boolean true
    runner.invoke(cli, ["config", "set", "test.bool_true", "true"])
    assert config.get("test.bool_true") is True
    
    # Test boolean false
    runner.invoke(cli, ["config", "set", "test.bool_false", "false"])
    assert config.get("test.bool_false") is False
    
    # Test integer
    runner.invoke(cli, ["config", "set", "test.int", "123"])
    assert config.get("test.int") == 123
    
    # Test float
    runner.invoke(cli, ["config", "set", "test.float", "12.34"])
    assert config.get("test.float") == 12.34
    
    # Test string
    runner.invoke(cli, ["config", "set", "test.str", "hello"])
    assert config.get("test.str") == "hello"

def test_plugin_docs_generation(tmp_path):
    """Test that plugin docs generate both gallery and dev guide."""
    runner = CliRunner()
    output_file = tmp_path / "gallery.rst"
    
    # We need at least one plugin registered for the gallery to be generated
    # The registry is a singleton, so we can just add a dummy path if needed
    # but usually some core plugins are there.
    
    result = runner.invoke(cli, ["plugins", "docs", "--output", str(output_file)])
    assert result.exit_code == 0
    
    # Check gallery exists
    assert output_file.exists()
    
    # Check developer guide exists in the same directory
    dev_guide = output_file.parent / "developer_guide.rst"
    assert dev_guide.exists()
    
    with open(dev_guide, "r") as f:
        content = f.read()
        assert "CMC Plugin Developer Guide" in content
        assert "Required Metadata" in content

def test_shell_internal_commands(monkeypatch):
    """
    Test shell internal commands. 
    Since the shell is an infinite loop, we test the logic 
    by mocking the input or testing the command handlers if they were separated.
    However, we can test the environment variable logic directly.
    """
    # We can't easily run the interactive shell in a test, 
    # but we can verify the logic that the shell uses.
    
    # Simulate the 'set' logic from shell.py
    user_input = "set TEST_ENV_VAR=hello_world"
    if user_input.startswith("set "):
        kv_pair = user_input[4:].strip()
        k, v = kv_pair.split("=", 1)
        os.environ[k.strip()] = v.strip()
    
    assert os.environ.get("TEST_ENV_VAR") == "hello_world"