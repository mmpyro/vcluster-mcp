"""Tests for CommandResult dataclass."""

from utils.vcluster_manager import CommandResult


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_creation(self):
        """Test CommandResult can be created with valid parameters."""
        result = CommandResult(exit_code=0, output="success output")

        assert result.exit_code == 0
        assert result.output == "success output"

    def test_command_result_with_error(self):
        """Test CommandResult with non-zero exit code."""
        result = CommandResult(exit_code=1, output="error message")

        assert result.exit_code == 1
        assert result.output == "error message"
