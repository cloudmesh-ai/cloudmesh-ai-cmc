# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
import os
import json
import pytest
import time
from click.testing import CliRunner
from cloudmesh.ai.cmc.main import cli
from unittest.mock import patch

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_stopwatch_file(tmp_path):
    """Provides a temporary file path for stopwatches to avoid touching user data."""
    return str(tmp_path / "test_stopwatches.json")

@pytest.fixture(autouse=True)
def mock_stopwatch_file(temp_stopwatch_file):
    """Mocks the STOPWATCH_FILE path in the time command module."""
    with patch("cloudmesh.ai.command.time.STOPWATCH_FILE", temp_stopwatch_file):
        yield

def test_time_start(runner):
    """Test starting a timer with 'start', '+', and auto-naming."""
    # Test 'start' with name
    result = runner.invoke(cli, ["time", "start", "timer1"])
    assert result.exit_code == 0
    assert "Stopwatch timer1 started" in result.output

    # Test '+' alias with name
    result = runner.invoke(cli, ["time", "+", "timer2"])
    assert result.exit_code == 0
    assert "Stopwatch timer2 started" in result.output

    # Test auto-naming (no name provided)
    result = runner.invoke(cli, ["time", "start"])
    assert result.exit_code == 0
    assert "using auto-generated name: timer-1" in result.output

    # Test auto-naming again (should be timer-2)
    result = runner.invoke(cli, ["time", "+"])
    assert result.exit_code == 0
    assert "using auto-generated name: timer-2" in result.output

def test_time_resume_logic(runner):
    """Test that both 'start' and '+' resume an existing timer."""
    # 1. Start and stop a timer to get some initial sum
    runner.invoke(cli, ["time", "start", "t1"])
    time.sleep(0.1)
    runner.invoke(cli, ["time", "stop", "t1"])
    
    # 2. Use '+' to resume
    result = runner.invoke(cli, ["time", "+", "t1"])
    assert "Resuming stopwatch t1" in result.output
    
    # 3. Use 'start' to resume (should be the same as +)
    result = runner.invoke(cli, ["time", "start", "t1"])
    assert "Resuming stopwatch t1" in result.output

def test_time_list(runner):
    """Test listing timers with 'list'."""
    runner.invoke(cli, ["time", "start", "t1"])
    runner.invoke(cli, ["time", "start", "t2"])
    
    # Test 'list'
    result = runner.invoke(cli, ["time", "list"])
    assert result.exit_code == 0
    assert "t1" in result.output
    assert "t2" in result.output

def test_time_print_single(runner):
    """Test printing a single timer's time with '='."""
    runner.invoke(cli, ["time", "start", "t1"])
    runner.invoke(cli, ["time", "start", "t2"])
    
    # Test '=' with no args (last timer t2)
    result = runner.invoke(cli, ["time", "="])
    assert result.exit_code == 0
    assert "Stopwatch t2" in result.output

    # Test '=' with name (t1)
    result = runner.invoke(cli, ["time", "=", "t1"])
    assert result.exit_code == 0
    assert "Stopwatch t1" in result.output

    # Test '=' with index (1 -> t1)
    result = runner.invoke(cli, ["time", "=", "1"])
    assert result.exit_code == 0
    assert "Stopwatch t1" in result.output

def test_time_stop(runner):
    """Test stopping timers by name, index, and last started using 'stop' and '-'."""
    runner.invoke(cli, ["time", "start", "t1"])
    runner.invoke(cli, ["time", "start", "t2"])
    
    # Stop by name using 'stop'
    result = runner.invoke(cli, ["time", "stop", "t1"])
    assert result.exit_code == 0
    assert "Stopwatch t1 stopped" in result.output

    # Stop by index using '-' alias (t2 is index 2)
    result = runner.invoke(cli, ["time", "-", "2"])
    assert result.exit_code == 0
    assert "resolving to stopwatch: t2" in result.output
    assert "Stopwatch t2 stopped" in result.output

    # Stop last started using 'stop'
    runner.invoke(cli, ["time", "start", "t3"])
    result = runner.invoke(cli, ["time", "stop"])
    assert result.exit_code == 0
    assert "stopping last started stopwatch: t3" in result.output

def test_time_remove(runner):
    """Test removing timers using 'rm'."""
    runner.invoke(cli, ["time", "start", "t1"])
    runner.invoke(cli, ["time", "start", "t2"])
    
    # Remove by name
    result = runner.invoke(cli, ["time", "rm", "t1"])
    assert result.exit_code == 0
    assert "Stopwatch t1 removed" in result.output

    # Remove by index (t2 is now index 1)
    result = runner.invoke(cli, ["time", "rm", "1"])
    assert result.exit_code == 0
    assert "Stopwatch t2 removed" in result.output

def test_time_clean(runner):
    """Test cleaning all timers with 'clean' and 'c'."""
    runner.invoke(cli, ["time", "start", "t1"])
    runner.invoke(cli, ["time", "start", "t2"])
    
    # Test 'clean'
    result = runner.invoke(cli, ["time", "clean"])
    assert result.exit_code == 0
    assert "All stopwatches cleared" in result.output
    
    # Start again to test 'c'
    runner.invoke(cli, ["time", "start", "t3"])
    result = runner.invoke(cli, ["time", "c"])
    assert result.exit_code == 0
    assert "All stopwatches cleared" in result.output
    
    # Verify list is empty
    result = runner.invoke(cli, ["time", "list"])
    assert "No stopwatches recorded" in result.output

def test_time_persistence(runner, temp_stopwatch_file):
    """Verify that timers persist across different CLI calls."""
    runner.invoke(cli, ["time", "start", "persist_me"])
    
    # Check if file exists and contains the timer
    assert os.path.exists(temp_stopwatch_file)
    with open(temp_stopwatch_file, "r") as f:
        data = json.load(f)
        assert "persist_me" in data["timers"]
    
    # Run a separate command to see if it's still there
    result = runner.invoke(cli, ["time", "list"])
    assert "persist_me" in result.output