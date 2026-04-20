import subprocess
import os
import sys
import pytest

def run_completion(args):
    """Helper to run the cmc completion logic and return the output."""
    env = os.environ.copy()
    env["CLICOMPLETE"] = "1"
    
    # Add src directory to PYTHONPATH so the module can be found
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    
    # We use the module execution to simulate the binary
    cmd = [sys.executable, "-m", "cloudmesh.ai.cmc.main"] + args
    result = subprocess.run(
        cmd, 
        env=env, 
        capture_output=True, 
        text=True
    )
    return result

def test_root_completion_empty():
    """Test 'cmc <TAB>' returns all top-level commands."""
    result = run_completion([])
    stdout = result.stdout.splitlines()
    
    assert result.returncode == 0
    assert "version" in stdout
    assert "docs" in stdout
    assert "banner" in stdout
    assert "config" in stdout

def test_root_completion_partial():
    """Test 'cmc ban<TAB>' returns 'banner'."""
    result = run_completion(["ban"])
    stdout = result.stdout.splitlines()
    
    assert result.returncode == 0
    assert "banner" in stdout
    assert "version" not in stdout
    assert "docs" not in stdout

def test_root_completion_no_match():
    """Test 'cmc xyz<TAB>' returns nothing."""
    result = run_completion(["xyz"])
    stdout = result.stdout.splitlines()
    
    assert result.returncode == 0
    assert len(stdout) == 0

def test_root_completion_with_whitespace():
    """Test 'cmc ban <TAB>' (with trailing space) returns 'banner'."""
    # The shell might pass the current word with a trailing space
    result = run_completion(["ban "])
    stdout = result.stdout.splitlines()
    
    assert result.returncode == 0
    assert "banner" in stdout

def test_subcommand_completion_empty():
    """Test 'cmc config <TAB>' returns all config subcommands."""
    # To simulate 'cmc config <TAB>', we pass 'config' and an empty string
    result = run_completion(["config", ""])
    stdout = result.stdout.splitlines()
    
    assert result.returncode == 0
    # Based on cloudmesh-ai-cmc/src/cloudmesh/ai/command/config.py
    # It should have 'set', 'get', 'list' etc.
    # Let's check if at least one exists.
    assert len(stdout) > 0

def test_subcommand_completion_partial():
    """Test 'cmc config s<TAB>' returns 'set'."""
    result = run_completion(["config", "s"])
    stdout = result.stdout.splitlines()
    
    assert result.returncode == 0
    assert "set" in stdout
    assert "get" not in stdout

if __name__ == "__main__":
    # Allow running the test directly via python
    pytest.main([__file__])