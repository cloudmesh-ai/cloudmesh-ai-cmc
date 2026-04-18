import os
import json
import pytest
from unittest.mock import patch
from cloudmesh.ai.cmc.registry import CommandRegistry

@pytest.fixture
def temp_registry_path(tmp_path):
    """Provides a temporary path for the registry config file."""
    return str(tmp_path / ".cme_registry_test.json")

@pytest.fixture
def registry(temp_registry_path):
    """Provides a CommandRegistry instance with a mocked CONFIG_PATH."""
    with patch("cloudmesh.ai.cmc.registry.CONFIG_PATH", temp_registry_path):
        reg = CommandRegistry()
        yield reg

def test_register(registry, tmp_path):
    # Create a dummy path to register
    dummy_path = str(tmp_path / "dummy_ext")
    os.makedirs(dummy_path)
    
    registry.register("test_cmd", dummy_path)
    
    config = registry.load_config()
    assert "test_cmd" in config
    assert config["test_cmd"]["path"] == os.path.abspath(dummy_path)
    assert config["test_cmd"]["active"] is True

def test_set_status(registry, tmp_path):
    dummy_path = str(tmp_path / "status_ext")
    os.makedirs(dummy_path)
    registry.register("status_cmd", dummy_path)
    
    # Deactivate
    success = registry.set_status("status_cmd", False)
    assert success is True
    assert registry.load_config()["status_cmd"]["active"] is False
    
    # Activate
    registry.set_status("status_cmd", True)
    assert registry.load_config()["status_cmd"]["active"] is True
    
    # Non-existent command
    success = registry.set_status("non_existent", False)
    assert success is False

def test_unregister(registry, tmp_path):
    dummy_path = str(tmp_path / "unreg_ext")
    os.makedirs(dummy_path)
    registry.register("unreg_cmd", dummy_path)
    
    assert "unreg_cmd" in registry.load_config()
    registry.unregister("unreg_cmd")
    assert "unreg_cmd" not in registry.load_config()

def test_list_all_details(registry, tmp_path):
    # Create a dummy extension with a VERSION file
    ext_path = tmp_path / "version_ext"
    ext_path.mkdir()
    version_file = ext_path / "VERSION"
    version_file.write_text("1.2.3")
    
    registry.register("version_cmd", str(ext_path))
    
    details = registry.list_all_details()
    assert len(details) == 1
    assert details[0]["name"] == "version_cmd"
    assert details[0]["version"] == "1.2.3"
    assert details[0]["active"] is True

def test_get_version_unknown(registry, tmp_path):
    # Path without VERSION file
    empty_path = tmp_path / "empty_ext"
    empty_path.mkdir()
    
    registry.register("empty_cmd", str(empty_path))
    details = registry.list_all_details()
    assert details[0]["version"] == "unknown"

def test_validation_missing_entry_point(registry, tmp_path):
    # Create an extension without entry_point
    ext_path = tmp_path / "no_entry"
    ext_path.mkdir()
    (ext_path / "cmd.py").write_text("def not_an_entry_point(): pass")
    
    registry.register("no_entry_cmd", str(ext_path))
    
    # Should not be loaded
    cmds = registry.get_active_commands()
    assert "no_entry_cmd" not in cmds

def test_validation_non_callable_entry_point(registry, tmp_path):
    # Create an extension where entry_point is a string
    ext_path = tmp_path / "bad_entry"
    ext_path.mkdir()
    (ext_path / "cmd.py").write_text("entry_point = 'I am not a function'")
    
    registry.register("bad_entry_cmd", str(ext_path))
    
    # Should not be loaded
    cmds = registry.get_active_commands()
    assert "bad_entry_cmd" not in cmds

def test_validation_valid_entry_point(registry, tmp_path):
    # Create a valid extension
    ext_path = tmp_path / "valid_entry"
    ext_path.mkdir()
    (ext_path / "cmd.py").write_text("def entry_point(): pass")
    
    registry.register("valid_cmd", str(ext_path))
    
    # Should be loaded
    cmds = registry.get_active_commands()
    assert "valid_cmd" in cmds

def test_corrupt_config_validation(registry):
    """Test that corrupted registry JSON is handled gracefully."""
    # Create a corrupted config: one valid entry, one invalid (string instead of dict), one missing keys
    corrupt_data = {
        "valid_ext": {"path": "/tmp/valid", "active": True},
        "invalid_type": "this should be a dict",
        "missing_keys": {"path": "/tmp/missing"}
    }
    registry.save(corrupt_data)
    
    # load_config should filter out the invalid entries
    config = registry.load_config()
    
    assert "valid_ext" in config
    assert "invalid_type" not in config
    assert "missing_keys" not in config
    assert len(config) == 1
