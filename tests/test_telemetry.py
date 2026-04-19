import pytest
import json
import csv
import os
from pathlib import Path
from click.testing import CliRunner
from cloudmesh.ai.command.command import cli
from cloudmesh.ai.cmc.utils import Config

def test_telemetry_toggle_off():
    """Test that 'cmc telemetry off' disables telemetry in config."""
    runner = CliRunner()
    config = Config()
    config.set("telemetry.enabled", True)
    config.save()

    result = runner.invoke(cli, ["telemetry", "off"])
    
    assert result.exit_code == 0
    assert "Telemetry has been disabled" in result.output
    
    # Verify config was updated
    updated_config = Config()
    assert updated_config.get("telemetry.enabled") is False

def test_telemetry_toggle_on():
    """Test that 'cmc telemetry on' enables telemetry in config."""
    runner = CliRunner()
    config = Config()
    config.set("telemetry.enabled", False)
    config.save()

    result = runner.invoke(cli, ["telemetry", "on"])
    
    assert result.exit_code == 0
    assert "Telemetry has been enabled" in result.output
    
    # Verify config was updated
    updated_config = Config()
    assert updated_config.get("telemetry.enabled") is True

def test_telemetry_list_no_db():
    """Test 'cmc telemetry list' when no database exists."""
    runner = CliRunner()
    # Ensure telemetry.db does not exist in current directory
    db_path = Path("telemetry.db")
    if db_path.exists():
        db_path.unlink()

    result = runner.invoke(cli, ["telemetry", "list"])
    
    assert result.exit_code == 0
    assert "No telemetry database found" in result.output

def test_telemetry_list_filtering(tmp_path):
    """Test 'cmc telemetry list' with filtering and export."""
    runner = CliRunner()
    
    # Create a dummy telemetry.db (SQLite)
    import sqlite3
    db_path = tmp_path / "telemetry.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                command TEXT,
                status TEXT,
                metrics TEXT,
                system TEXT,
                message TEXT
            )
        """)
        conn.execute("INSERT INTO telemetry (timestamp, command, status, metrics, system, message) VALUES (?, ?, ?, ?, ?, ?)",
                     ("2026-01-01T10:00:00", "test-cmd", "completed", "{}", "{}", "Success 1"))
        conn.execute("INSERT INTO telemetry (timestamp, command, status, metrics, system, message) VALUES (?, ?, ?, ?, ?, ?)",
                     ("2026-01-02T10:00:00", "test-cmd", "failed", "{}", "{}", "Failure 1"))
        conn.execute("INSERT INTO telemetry (timestamp, command, status, metrics, system, message) VALUES (?, ?, ?, ?, ?, ?)",
                     ("2026-01-03T10:00:00", "other-cmd", "completed", "{}", "{}", "Success 2"))
        conn.commit()

    # We need to make sure the command finds this DB. 
    # Since the command uses Path("telemetry.db").expanduser(), 
    # we can't easily change the path without modifying the code.
    # For the purpose of this test, we'll temporarily move the DB to the current working directory.
    real_db_path = Path("telemetry.db")
    if real_db_path.exists():
        real_db_path.unlink()
    
    import shutil
    shutil.copy(db_path, real_db_path)

    try:
        # Test filter by command
        result = runner.invoke(cli, ["telemetry", "list", "--command", "test-cmd"])
        assert result.exit_code == 0
        assert "test-cmd" in result.output
        assert "other-cmd" not in result.output

        # Test filter by status
        result = runner.invoke(cli, ["telemetry", "list", "--status", "failed"])
        assert result.exit_code == 0
        assert "FAILED" in result.output
        assert "COMPLETED" not in result.output

        # Test export to JSON
        result = runner.invoke(cli, ["telemetry", "list", "--export", "json"])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert Path("telemetry_export.json").exists()
        
        with open("telemetry_export.json", "r") as f:
            data = json.load(f)
            assert len(data) == 3

        # Test export to CSV
        result = runner.invoke(cli, ["telemetry", "list", "--export", "csv"])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert Path("telemetry_export.csv").exists()

    finally:
        # Cleanup
        if real_db_path.exists():
            real_db_path.unlink()
        if Path("telemetry_export.json").exists():
            Path("telemetry_export.json").unlink()
        if Path("telemetry_export.csv").exists():
            Path("telemetry_export.csv").unlink()