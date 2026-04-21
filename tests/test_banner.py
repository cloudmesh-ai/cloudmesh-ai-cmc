import pytest
from click.testing import CliRunner
from cloudmesh.ai.cmc.main import cli

def test_banner_single_arg():
    """Test cmc banner a -> title empty, 'a' as content."""
    runner = CliRunner()
    result = runner.invoke(cli, ["banner", "Hello"])
    assert result.exit_code == 0
    # Check for the rounded border and the content
    assert "╭" in result.output
    assert "Hello" in result.output
    assert "╰" in result.output

def test_banner_multi_arg():
    """Test cmc banner Title Line1 Line2 -> 'Title' as title, 'Line1\nLine2' as content."""
    runner = CliRunner()
    result = runner.invoke(cli, ["banner", "MyTitle", "Line1", "Line2"])
    assert result.exit_code == 0
    assert "MyTitle" in result.output
    assert "Line1" in result.output
    assert "Line2" in result.output
    # Verify they are on separate lines (roughly)
    assert result.output.count("\n") >= 2

def test_banner_comment_prefix():
    """Test cmc banner -c Title Line1 -> every line prefixed with #."""
    runner = CliRunner()
    result = runner.invoke(cli, ["banner", "-c", "Title", "Line1"])
    assert result.exit_code == 0
    # Every line of the panel should start with #
    lines = result.output.strip().splitlines()
    for line in lines:
        assert line.startswith("#")
    assert "Title" in result.output
    assert "Line1" in result.output

def test_banner_custom_comment_char():
    """Test cmc banner --comment-char '>>' -c Title Line1 -> every line prefixed with >>."""
    runner = CliRunner()
    result = runner.invoke(cli, ["banner", "--comment-char", ">>", "-c", "Title", "Line1"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    for line in lines:
        assert line.startswith(">>")
    assert "Title" in result.output

def test_banner_no_args():
    """Test cmc banner without arguments should fail."""
    runner = CliRunner()
    result = runner.invoke(cli, ["banner"])
    assert result.exit_code != 0