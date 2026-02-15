"""Edge case tests for VClusterManager."""

from unittest.mock import MagicMock, patch

import pytest

from utils.vcluster_manager import CommandResult
from utils.exceptions import VClusterCLIError


class TestEdgeCases:
    """Edge case tests for VClusterManager."""

    def test_default_namespace_generation(self, vcluster_manager):
        """Test that default namespace is generated correctly."""
        # The namespace should default to vcluster-{name}
        # This is verified by checking the command construction
        mock_result = CommandResult(exit_code=0, output="{}")
        
        with patch.object(vcluster_manager, '_run_command', return_value=mock_result) as mock_run:
            vcluster_manager.describe("my-cluster")
            
            # Verify the command was called with default namespace
            call_args = mock_run.call_args[0][0]
            assert "-n" in call_args
            ns_index = call_args.index("-n")
            assert call_args[ns_index + 1] == "vcluster-my-cluster"

    def test_custom_namespace_used(self, vcluster_manager):
        """Test that custom namespace is used when provided."""
        mock_result = CommandResult(exit_code=0, output="{}")
        
        with patch.object(vcluster_manager, '_run_command', return_value=mock_result) as mock_run:
            vcluster_manager.describe("my-cluster", namespace="custom-ns")
            
            call_args = mock_run.call_args[0][0]
            ns_index = call_args.index("-n")
            assert call_args[ns_index + 1] == "custom-ns"

    def test_cli_error_file_not_found(self, vcluster_manager):
        """Test CLI error when vcluster command is not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"])

    def test_cli_error_permission_denied(self, vcluster_manager):
        """Test CLI error when permission is denied."""
        with patch('subprocess.run', side_effect=PermissionError("Permission denied")):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"])

    def test_cli_error_unexpected(self, vcluster_manager):
        """Test CLI error for unexpected errors."""
        with patch('subprocess.run', side_effect=OSError("Unexpected error")):
            with pytest.raises(VClusterCLIError):
                vcluster_manager._run_command(["vcluster", "list"])

    def test_multiple_label_operations(self, vcluster_manager, mock_kubernetes_clients):
        """Test multiple label operations in sequence."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = {}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        # Set first label
        result1 = vcluster_manager.set_namespace_label("test-ns", "key1", "value1")
        assert result1.is_ok
        
        # Set second label
        result2 = vcluster_manager.set_namespace_label("test-ns", "key2", "value2")
        assert result2.is_ok
        
        # Get labels - should have both
        mock_ns.metadata.labels = {'key1': 'value1', 'key2': 'value2'}
        result3 = vcluster_manager.get_namespace_labels("test-ns")
        assert result3.is_ok
        assert len(result3.value) == 2

    def test_json_parse_edge_cases(self, vcluster_manager):
        """Test JSON parsing edge cases."""
        # Empty output
        mock_result = CommandResult(exit_code=0, output="")
        
        with patch.object(vcluster_manager, '_run_command', return_value=mock_result):
            result = vcluster_manager.list()
        
        assert result.is_err
        
        # Valid JSON but unexpected structure
        mock_result = CommandResult(exit_code=0, output="null")
        
        with patch.object(vcluster_manager, '_run_command', return_value=mock_result):
            result = vcluster_manager.list()
        
        # Should handle gracefully - wraps in list
        assert result.is_ok
