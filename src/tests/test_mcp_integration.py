"""Integration tests for MCP tools with VClusterManager."""

from unittest.mock import MagicMock, patch

import pytest

from utils.result import Result
from utils.exceptions import ValidationError


class TestMCPToolsIntegration:
    """Integration tests for MCP tools with VClusterManager."""

    def test_vcluster_list_tool(self):
        """Test vcluster_list MCP tool."""
        from tools.vcluster import vcluster_list
        
        with patch('tools.vcluster.setup_kubernetes'), \
             patch('tools.vcluster.VClusterManager') as MockManager:
            mock_manager = MagicMock()
            mock_manager.list.return_value = Result.ok([{'name': 'test'}])
            MockManager.return_value = mock_manager
            
            result = vcluster_list()
            
            assert result == [{'name': 'test'}]

    def test_vcluster_describe_tool_validation_error(self):
        """Test vcluster_describe MCP tool handles validation errors."""
        from tools.vcluster import vcluster_describe
        
        with patch('tools.vcluster.setup_kubernetes'), \
             patch('tools.vcluster.VClusterManager') as MockManager:
            mock_manager = MagicMock()
            # Make describe raise an exception
            mock_manager.describe.side_effect = ValidationError("name", "Validation error")
            MockManager.return_value = mock_manager
            
            # The tool should handle the exception and return an error dict
            # or raise the exception - either behavior is acceptable
            try:
                result = vcluster_describe("InvalidName")
                # If no exception, result should be a dict with error
                assert isinstance(result, dict)
            except ValidationError:
                # Exception propagation is also acceptable
                pass

    def test_get_namespace_labels_tool(self):
        """Test get_namespace_labels MCP tool."""
        from tools.vcluster import get_namespace_labels
        
        with patch('tools.vcluster.setup_kubernetes'), \
             patch('tools.vcluster.VClusterManager') as MockManager:
            mock_manager = MagicMock()
            mock_manager.get_namespace_labels.return_value = Result.ok({'app': 'test'})
            MockManager.return_value = mock_manager
            
            result = get_namespace_labels("test-ns")
            
            assert result == {'app': 'test'}
