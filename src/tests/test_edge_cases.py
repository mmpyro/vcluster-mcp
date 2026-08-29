"""Edge case tests for VClusterManager."""

import subprocess
import pytest
from unittest.mock import MagicMock, patch
from utils.exceptions import VClusterCLIError, VClusterTimeoutError
from utils.vcluster_manager import CommandResult


class TestEdgeCases:
    """Edge case tests for VClusterManager."""

    def test_default_namespace_generation(self, vcluster_manager):
        """Test that default namespace is generated correctly."""
        mock_result = CommandResult(exit_code=0, output="{}")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            vcluster_manager.describe("my-cluster")

            call_args = mock_run.call_args[0][0]
            assert "-n" in call_args
            ns_index = call_args.index("-n")
            assert call_args[ns_index + 1] == "vcluster-my-cluster"

    def test_custom_namespace_used(self, vcluster_manager):
        """Test that custom namespace is used when provided."""
        mock_result = CommandResult(exit_code=0, output="{}")

        with patch.object(
            vcluster_manager, "_run_command", return_value=mock_result
        ) as mock_run:
            vcluster_manager.describe("my-cluster", namespace="custom-ns")

            call_args = mock_run.call_args[0][0]
            ns_index = call_args.index("-n")
            assert call_args[ns_index + 1] == "custom-ns"

    def test_cli_error_file_not_found(self, vcluster_manager):
        """Test CLI error when vcluster command is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"])

    def test_cli_error_permission_denied(self, vcluster_manager):
        """Test CLI error when permission is denied."""
        with patch("subprocess.run", side_effect=PermissionError("Permission denied")):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"])

    def test_cli_error_unexpected(self, vcluster_manager):
        """Test CLI error for unexpected errors."""
        with patch("subprocess.run", side_effect=OSError("Unexpected error")):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"])

    def test_cli_error_timeout(self, vcluster_manager):
        """Test a timed-out command raises VClusterTimeoutError."""
        timeout_error = subprocess.TimeoutExpired(cmd=["vcluster", "list"], timeout=1)

        with patch("subprocess.run", side_effect=timeout_error):
            with pytest.raises(VClusterTimeoutError):
                vcluster_manager._run_command(["vcluster", "list"], timeout=1)

    def test_timeout_error_is_a_cli_error(self, vcluster_manager):
        """Test existing VClusterCLIError handlers still catch timeouts."""
        timeout_error = subprocess.TimeoutExpired(cmd=["vcluster", "list"], timeout=1)

        with patch("subprocess.run", side_effect=timeout_error):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"], timeout=1)

    def test_run_command_forwards_timeout(self, vcluster_manager):
        """Test the timeout is passed through to subprocess.run."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            vcluster_manager._run_command(["vcluster", "list"], timeout=5)

        assert mock_run.call_args.kwargs["timeout"] == 5

    def test_run_command_defaults_to_no_timeout(self, vcluster_manager):
        """Test existing callers are unchanged: no timeout unless asked for."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            vcluster_manager._run_command(["vcluster", "list"])

        assert mock_run.call_args.kwargs["timeout"] is None

    def test_multiple_label_operations(self, vcluster_manager, mock_kubernetes_clients):
        """Test multiple label operations in sequence."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = {}
        mock_kubernetes_clients["core_v1"].read_namespace.return_value = mock_ns

        result1 = vcluster_manager.set_namespace_label("test-ns", "key1", "value1")
        assert result1.is_ok

        result2 = vcluster_manager.set_namespace_label("test-ns", "key2", "value2")
        assert result2.is_ok

        mock_ns.metadata.labels = {"key1": "value1", "key2": "value2"}
        result3 = vcluster_manager.get_namespace_labels("test-ns")
        assert result3.is_ok
        assert len(result3.value) == 2

    def test_json_parse_edge_cases(self, vcluster_manager):
        """Test JSON parsing edge cases."""
        # Empty output
        mock_result = CommandResult(exit_code=0, output="")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_err

        # Valid JSON but unexpected structure
        mock_result = CommandResult(exit_code=0, output="null")

        with patch.object(vcluster_manager, "_run_command", return_value=mock_result):
            result = vcluster_manager.list()

        assert result.is_ok
