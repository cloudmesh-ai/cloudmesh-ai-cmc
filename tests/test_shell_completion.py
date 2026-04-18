import pytest
from cloudmesh.ai.command.shell import get_command_completer
from prompt_toolkit.completion import WordCompleter

def test_get_command_completer():
    """Test that the shell completer correctly identifies registered commands."""
    completer = get_command_completer()
    
    # Ensure prompt_toolkit is installed for the test to be valid
    assert completer is not None, "prompt_toolkit should be installed for completion to work"
    assert isinstance(completer, WordCompleter), "Should return a WordCompleter instance"
    
    # Get the list of words the completer is using
    # WordCompleter stores its words in the 'words' attribute
    completed_words = completer.words
    
    # 1. Check for core commands
    assert "banner" in completed_words, "Completer should include 'banner' command"
    assert "version" in completed_words, "Completer should include 'version' command"
    
    # 2. Check for internal shell commands
    assert "exit" in completed_words, "Completer should include 'exit' internal command"
    assert "help" in completed_words, "Completer should include 'help' internal command"
    assert "set" in completed_words, "Completer should include 'set' internal command"
    
    # 3. Check for sub-commands (if any are registered)
    # For example, if 'plugins list' is registered
    assert any("plugins" in word for word in completed_words), "Completer should include 'plugins' related commands"

def test_completer_case_insensitivity():
    """Test that the completer is configured to ignore case."""
    completer = get_command_completer()
    assert completer.ignore_case is True, "Completer should be case-insensitive"