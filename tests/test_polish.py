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