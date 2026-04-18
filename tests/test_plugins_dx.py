import os
import pytest
from pathlib import Path
from click.testing import CliRunner
from cloudmesh.ai.command.plugins import entry_point as plugins_group
from cloudmesh.ai.cmc.registry import CommandRegistry

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_registry(tmp_path):
    registry_path = tmp_path / "registry.json"
    # We monkeypatch the registry used in the plugins command
    import cloudmesh.ai.command.plugins
    original_registry = cloudmesh.ai.command.plugins.registry
    
    new_registry = CommandRegistry(config_path=str(registry_path))
    cloudmesh.ai.command.plugins.registry = new_registry
    
    yield new_registry
    
    cloudmesh.ai.command.plugins.registry = original_registry

def test_init_default_flavor(runner, tmp_path):
    plugin_name = "test_plugin_default"
    plugin_dir = tmp_path / plugin_name
    
    with runner.isolated_filesystem():
        # We need to be in the tmp_path for the init command to create the dir there
        # but CliRunner.isolated_filesystem() changes CWD. 
        # Instead, we'll just use the name and check the current directory.
        result = runner.invoke(plugins_group, ["init", plugin_name])
        
        assert result.exit_code == 0
        assert (Path(plugin_name) / "cmd.py").exists()
        content = (Path(plugin_name) / "cmd.py").read_text()
        assert "Hello from the new plugin!" in content
        assert "version = '0.1.0'" in content

def test_init_benchmark_flavor(runner):
    plugin_name = "test_plugin_bench"
    
    with runner.isolated_filesystem():
        result = runner.invoke(plugins_group, ["init", plugin_name, "--flavor", "benchmark"])
        
        assert result.exit_code == 0
        content = (Path(plugin_name) / "cmd.py").read_text()
        assert "import time" in content
        assert "time.perf_counter()" in content
        assert "Starting benchmark..." in content

def test_init_sysinfo_flavor(runner):
    plugin_name = "test_plugin_sys"
    
    with runner.isolated_filesystem():
        result = runner.invoke(plugins_group, ["init", plugin_name, "--flavor", "sysinfo"])
        
        assert result.exit_code == 0
        content = (Path(plugin_name) / "cmd.py").read_text()
        assert "import platform" in content
        assert "import os" in content
        assert "platform.system()" in content

def test_init_existing_dir(runner):
    plugin_name = "existing_plugin"
    os.makedirs(plugin_name, exist_ok=True)
    
    try:
        with runner.isolated_filesystem():
            # Re-create dir inside isolated fs
            os.makedirs(plugin_name, exist_ok=True)
            result = runner.invoke(plugins_group, ["init", plugin_name])
            assert result.exit_code != 0
            assert "already exists" in result.output
    finally:
        if os.path.exists(plugin_name):
            import shutil
            shutil.rmtree(plugin_name)

def create_mock_plugin_with_tests(path, name, test_content):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "VERSION"), "w") as f:
        f.write("0.1.0")
    with open(os.path.join(path, "cmd.py"), "w") as f:
        f.write("version = '0.1.0'\nentry_point = lambda: None")
    
    test_dir = os.path.join(path, "tests")
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(test_dir, "test_plugin.py"), "w") as f:
        f.write(test_content)

def test_test_plugin_success(runner, temp_registry, tmp_path):
    plugin_name = "success_plugin"
    plugin_path = tmp_path / plugin_name
    test_content = "def test_pass():\n    assert True"
    create_mock_plugin_with_tests(str(plugin_path), plugin_name, test_content)
    
    temp_registry.register(plugin_name, str(plugin_path))
    
    result = runner.invoke(plugins_group, ["test", plugin_name])
    assert result.exit_code == 0
    assert "Tests passed" in result.output

def test_test_plugin_failure(runner, temp_registry, tmp_path):
    plugin_name = "fail_plugin"
    plugin_path = tmp_path / plugin_name
    test_content = "def test_fail():\n    assert False"
    create_mock_plugin_with_tests(str(plugin_path), plugin_name, test_content)
    
    temp_registry.register(plugin_name, str(plugin_path))
    
    result = runner.invoke(plugins_group, ["test", plugin_name])
    assert result.exit_code != 0
    assert "Tests failed" in result.output

def test_test_plugin_no_tests(runner, temp_registry, tmp_path):
    plugin_name = "no_test_plugin"
    plugin_path = tmp_path / plugin_name
    os.makedirs(plugin_path, exist_ok=True)
    with open(os.path.join(plugin_path, "VERSION"), "w") as f:
        f.write("0.1.0")
    with open(os.path.join(plugin_path, "cmd.py"), "w") as f:
        f.write("version = '0.1.0'\nentry_point = lambda: None")
    
    temp_registry.register(plugin_name, str(plugin_path))
    
    result = runner.invoke(plugins_group, ["test", plugin_name])
    assert result.exit_code == 0
    assert "No tests found" in result.output

def test_test_plugin_not_found(runner, temp_registry):
    result = runner.invoke(plugins_group, ["test", "ghost_plugin"])
    assert result.exit_code != 0
    assert "not found in registry" in result.output