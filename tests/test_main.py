import os
import pytest
from click.testing import CliRunner
from cloudmesh.ai.main import cli, main
from cloudmesh.ai.registry import CommandRegistry

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture(autouse=True)
def init_cli():
    """Ensure the CLI is initialized with core extensions before each test."""
    from cloudmesh.ai.main import cli, load_core_extensions, load_pip_extensions
    # Clear existing commands to avoid duplicates between tests if necessary
    # but since cli is a global object, we just ensure extensions are loaded.
    load_core_extensions(cli)
    load_pip_extensions(cli)

@pytest.fixture
def mock_registry(tmp_path):
    """Provides a CommandRegistry instance with a mocked CONFIG_PATH."""
    temp_path = str(tmp_path / ".cme_registry_main_test.json")
    with pytest.MonkeyPatch().context() as mp:
        # We need to patch the CONFIG_PATH in the registry module
        import cloudmesh.ai.registry
        mp.setattr(cloudmesh.ai.registry, "CONFIG_PATH", temp_path)
        reg = CommandRegistry()
        yield reg

def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "cmc: Cloudmesh Commands" in result.output

def test_completion(runner):
    result = runner.invoke(cli, ["completion"])
    assert result.exit_code == 0
    # It should output a shell completion command
    assert "eval" in result.output or "Shell" in result.output

def test_dynamic_extension_loading(runner, tmp_path):
    # 1. Create a dummy extension directory with a cmd.py
    ext_dir = tmp_path / "test_ext"
    ext_dir.mkdir()
    cmd_file = ext_dir / "cmd.py"
    
    # The extension must have an 'entry_point' which is a click command
    cmd_file.write_text(
        "import click\n"
        "@click.command()\n"
        "def entry_point():\n"
        "    click.echo('Hello from dynamic extension!')\n"
    )
    
    # 2. Mock the registry to include this extension
    # We need to patch the registry instance used in main.py
    import cloudmesh.ai.main
    import cloudmesh.ai.registry
    
    temp_config = str(tmp_path / ".cme_registry_dynamic.json")
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(cloudmesh.ai.registry, "CONFIG_PATH", temp_config)
        
        # Create a new registry and register the dummy extension
        reg = CommandRegistry()
        reg.register("hello", str(ext_dir))
        
        # Patch the registry object in main.py to use our test registry
        mp.setattr(cloudmesh.ai.main, "registry", reg)
        
        # Now run the main() function which calls registry.get_active_commands() 
        # and adds them to the cli
        with runner.isolated_filesystem():
            # We invoke the main function logic
            # Since main() calls cli(), we can just call main()
            # But main() calls cli() which is a click group.
            # To test it with CliRunner, we can use runner.invoke(cli) 
            # after main's setup logic.
            
            # Manually trigger the setup part of main()
            active_cmds = reg.get_active_commands()
            for name, obj in active_cmds.items():
                cli.add_command(obj, name=name)
            
            result = runner.invoke(cli, ["hello"])
            assert result.exit_code == 0
            assert "Hello from dynamic extension!" in result.output

def test_registry_list(runner, tmp_path):
    # Setup: register a dummy extension
    import cloudmesh.ai.main
    import cloudmesh.ai.registry
    temp_config = str(tmp_path / ".cme_registry_list.json")
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(cloudmesh.ai.registry, "CONFIG_PATH", temp_config)
        reg = cloudmesh.ai.registry.CommandRegistry()
        mp.setattr(cloudmesh.ai.main, "registry", reg)
        
        reg.register("list_ext", str(tmp_path / "list_ext"))
        
        result = runner.invoke(cli, ["command", "list"])
        assert result.exit_code == 0
        assert "list_ext" in result.output
        # Use a more flexible check for 'active' as Rich output can be complex
        assert "active" in result.output.lower() or "STATUS" in result.output

def test_registry_add(runner, tmp_path):
    import cloudmesh.ai.main
    import cloudmesh.ai.registry
    temp_config = str(tmp_path / ".cme_registry_add.json")
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(cloudmesh.ai.registry, "CONFIG_PATH", temp_config)
        reg = cloudmesh.ai.registry.CommandRegistry()
        mp.setattr(cloudmesh.ai.main, "registry", reg)
        
        ext_dir = tmp_path / "new_ext"
        ext_dir.mkdir()
        
        result = runner.invoke(cli, ["command", "load", str(ext_dir)])
        assert result.exit_code == 0
        assert "Loaded and activated" in result.output
        assert "new_ext" in reg.load_config()

def test_registry_enable_disable(runner, tmp_path):
    import cloudmesh.ai.main
    import cloudmesh.ai.registry
    temp_config = str(tmp_path / ".cme_registry_status.json")
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(cloudmesh.ai.registry, "CONFIG_PATH", temp_config)
        reg = cloudmesh.ai.registry.CommandRegistry()
        mp.setattr(cloudmesh.ai.main, "registry", reg)
        
        reg.register("status_ext", str(tmp_path))
        
        # Disable
        result = runner.invoke(cli, ["command", "deactivate", "status_ext"])
        assert result.exit_code == 0
        assert "Deactivated" in result.output
        assert reg.load_config()["status_ext"]["active"] is False
        
        # Enable
        result = runner.invoke(cli, ["command", "activate", "status_ext"])
        assert result.exit_code == 0
        assert "Activated" in result.output
        assert reg.load_config()["status_ext"]["active"] is True

def test_registry_remove(runner, tmp_path):
    import cloudmesh.ai.main
    import cloudmesh.ai.registry
    temp_config = str(tmp_path / ".cme_registry_remove.json")
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(cloudmesh.ai.registry, "CONFIG_PATH", temp_config)
        reg = cloudmesh.ai.registry.CommandRegistry()
        mp.setattr(cloudmesh.ai.main, "registry", reg)
        
        reg.register("remove_ext", str(tmp_path))
        
        result = runner.invoke(cli, ["command", "unload", "remove_ext"])
        assert result.exit_code == 0
        assert "Unloaded" in result.output
        assert "remove_ext" not in reg.load_config()
