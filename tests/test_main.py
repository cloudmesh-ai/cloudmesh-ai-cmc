import os
import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from cloudmesh.ai.cmc.main import cli, main
from cloudmesh.ai.cmc.utils import Config

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Mocks the CMC configuration file."""
    config_dir = tmp_path / ".config" / "cloudmesh" / "ai"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "cmc.yaml"
    
    # Default mock config
    config_data = {
        "logging": {"level": "DEBUG"},
        "telemetry": {
            "enabled": True,
            "path": str(tmp_path / "telemetry.jsonl")
        }
    }
    
    # Since Config class reads from a specific path, we might need to patch it
    # or ensure the environment is set up. 
    # For simplicity in tests, we can patch the Config.get method or the path.
    import cloudmesh.ai.cmc.utils
    monkeypatch.setattr(cloudmesh.ai.cmc.utils, "DEFAULT_CONFIG_PATH", str(config_file))
    
    # Write the config file (as YAML, though our simple Config class might just use json or simple key-value)
    # The current Config implementation in utils.py uses yaml.safe_load
    import yaml
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
        
    return config_data


def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "cmc: Cloudmesh Commands" in result.output

def test_version(runner):
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "cmc version" in result.output

def test_completion(runner):
    result = runner.invoke(cli, ["completion"])
    assert result.exit_code == 0
    assert "eval" in result.output or "Shell" in result.output


def test_telemetry_no_file(runner, tmp_path, monkeypatch):
    # Ensure no telemetry file exists by patching the global config instance in main
    import cloudmesh.ai.cmc.main
    def mock_get(key, default=None):
        if key == "telemetry.path": return str(tmp_path / "non_existent_telemetry.jsonl")
        return default
    
    monkeypatch.setattr(cloudmesh.ai.cmc.main.config, "get", mock_get)
    
    result = runner.invoke(cli, ["telemetry"])
    assert result.exit_code == 0
    assert "No telemetry file found" in result.output

def test_telemetry_analysis(runner, tmp_path, monkeypatch):
    # Create a dummy telemetry file
    t_file = tmp_path / "telemetry.jsonl"
    records = [
        {"command": "version", "status": "success", "metrics": {"duration_sec": 0.1}},
        {"command": "version", "status": "success", "metrics": {"duration_sec": 0.2}},
        {"command": "plugins", "status": "failure", "metrics": {"duration_sec": 0.5}},
    ]
    with open(t_file, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
    # Patch config to use this telemetry file
    import cloudmesh.ai.cmc.main
    def mock_get(key, default=None):
        if key == "telemetry.path": return str(t_file)
        return default

    monkeypatch.setattr(cloudmesh.ai.cmc.main.config, "get", mock_get)
    
    result = runner.invoke(cli, ["telemetry"])
    assert result.exit_code == 0
    assert "Telemetry Summary" in result.output
    assert "Total Events: 3" in result.output
    assert "version" in result.output
    assert "plugins" in result.output
    assert "success" in result.output
    assert "failure" in result.output

def test_error_handling(runner, monkeypatch):
    """Test that handle_errors catches exceptions and returns exit code 1."""
    import cloudmesh.ai.cmc.main
    
    # Create a command that raises an exception
    from cloudmesh.ai.cmc.utils import handle_errors
    @cli.command(name="fail")
    @handle_errors
    def fail_cmd():
        raise RuntimeError("Test failure")
        
    result = runner.invoke(cli, ["fail"])
    # handle_errors should catch this and sys.exit(1)
    assert result.exit_code == 1
    assert "Error" in result.output or "RuntimeError" in result.output