import pytest
from click.testing import CliRunner
from cloudmesh.ai.command.progress import progress

@pytest.fixture
def runner():
    return CliRunner()

def test_progress_0(runner):
    result = runner.invoke(progress, ["0"])
    assert result.exit_code == 0
    assert "progress=0" in result.output

def test_progress_50(runner):
    result = runner.invoke(progress, ["50"])
    assert result.exit_code == 0
    assert "progress=50" in result.output

def test_progress_now(runner):
    result = runner.invoke(progress, ["50", "--now"])
    assert result.exit_code == 0
    assert "progress=50" in result.output
    assert "time=" in result.output

def test_progress_status(runner):
    result = runner.invoke(progress, ["50", "--status=undefined"])
    assert result.exit_code == 0
    assert "progress=50" in result.output
    assert "status=undefined" in result.output

def test_progress_values(runner):
    result = runner.invoke(progress, ["50", "a=10", "b=text", "c={d:1}"])
    assert result.exit_code == 0
    assert "progress=50" in result.output
    assert "a=10" in result.output
    assert "b=text" in result.output
    assert "c={d:1}" in result.output

def test_progress_banner(runner):
    result = runner.invoke(progress, ["50", "a=10", "--banner"])
    assert result.exit_code == 0
    assert "progress=50" in result.output