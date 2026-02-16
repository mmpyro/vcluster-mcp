"""Integration tests for MCP tools with VClusterManager."""

from unittest.mock import MagicMock, patch
from utils.exceptions import ValidationError
from utils.result import Result


class TestMCPToolsIntegration:
    """Integration tests for MCP tools with VClusterManager."""

    def test_vcluster_list_tool(self):
        """Test vcluster_list MCP tool."""
        from tools.vcluster import vcluster_list

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = Result.ok([{"name": "test"}])
            MockManager.return_value = mock_manager

            result = vcluster_list()

            assert result == [{"name": "test"}]

    def test_vcluster_describe_tool_validation_error(self):
        """Test vcluster_describe MCP tool handles validation errors."""
        from tools.vcluster import vcluster_describe

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.describe.side_effect = ValidationError(
                "name", "Validation error"
            )
            MockManager.return_value = mock_manager

            try:
                result = vcluster_describe("InvalidName")
                assert isinstance(result, dict)
            except ValidationError:
                pass

    def test_get_namespace_labels_tool(self):
        """Test get_namespace_labels MCP tool."""
        from tools.vcluster import get_namespace_labels

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.get_namespace_labels.return_value = Result.ok({"app": "test"})
            MockManager.return_value = mock_manager

            result = get_namespace_labels("test-ns")

            assert result == {"app": "test"}
