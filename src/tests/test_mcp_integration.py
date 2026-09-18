"""Integration tests for MCP tools with VClusterManager.

Tools return compact JSON strings, so assertions parse the payload back.
"""

import json

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

            assert isinstance(result, str)
            assert json.loads(result) == [{"name": "test"}]

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

            result = vcluster_describe("InvalidName")

            assert "error" in json.loads(result)

    def test_namespace_metadata_get_labels_only(self):
        """Test namespace_metadata_get returns only the requested kind."""
        from tools.vcluster import namespace_metadata_get

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.get_namespace_labels.return_value = Result.ok({"app": "test"})
            MockManager.return_value = mock_manager

            result = namespace_metadata_get("test-ns", kind="labels")

            assert json.loads(result) == {"labels": {"app": "test"}}
            mock_manager.get_namespace_annotations.assert_not_called()

    def test_namespace_metadata_get_both(self):
        """Test the default kind reads labels and annotations."""
        from tools.vcluster import namespace_metadata_get

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.get_namespace_labels.return_value = Result.ok({"app": "test"})
            mock_manager.get_namespace_annotations.return_value = Result.ok({"note": "x"})
            MockManager.return_value = mock_manager

            result = namespace_metadata_get("test-ns")

            assert json.loads(result) == {
                "labels": {"app": "test"},
                "annotations": {"note": "x"},
            }

    def test_namespace_metadata_set_deletes_on_null_value(self):
        """Test omitting value deletes the key rather than setting it empty."""
        from tools.vcluster import namespace_metadata_set

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.delete_namespace_label.return_value = Result.ok(True)
            MockManager.return_value = mock_manager

            namespace_metadata_set("test-ns", "labels", "app")

            mock_manager.delete_namespace_label.assert_called_once_with("test-ns", "app")
            mock_manager.set_namespace_label.assert_not_called()

    def test_namespace_metadata_set_routes_by_kind(self):
        """Test kind selects the annotation setter."""
        from tools.vcluster import namespace_metadata_set

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.set_namespace_annotation.return_value = Result.ok(True)
            MockManager.return_value = mock_manager

            namespace_metadata_set("test-ns", "annotations", "note", "hello")

            mock_manager.set_namespace_annotation.assert_called_once_with(
                "test-ns", "note", "hello"
            )
            mock_manager.set_namespace_label.assert_not_called()

    def test_vcluster_certs_check_tool(self):
        """Test vcluster_certs_check MCP tool."""
        from tools.vcluster import vcluster_certs_check

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.certs_check.return_value = Result.ok({"apiserver.crt": "ok"})
            MockManager.return_value = mock_manager

            result = vcluster_certs_check("test-cluster")

            assert json.loads(result) == {"apiserver.crt": "ok"}

    def test_vcluster_kubeconfig_tool(self):
        """Test vcluster_kubeconfig MCP tool returns a path, not credentials."""
        from tools.vcluster import vcluster_kubeconfig

        payload = {
            "kubeconfig_path": "/tmp/vcluster-test-abc.yaml",
            "context": "vcluster_test",
            "server": "https://localhost:8443",
        }

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.kubeconfig.return_value = Result.ok(payload)
            MockManager.return_value = mock_manager

            result = vcluster_kubeconfig("test-cluster")

            assert json.loads(result) == payload

    def test_vcluster_kubeconfig_tool_validation_error(self):
        """Test vcluster_kubeconfig surfaces validation errors as an error object."""
        from tools.vcluster import vcluster_kubeconfig

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.kubeconfig.side_effect = ValidationError("server", "bad url")
            MockManager.return_value = mock_manager

            result = vcluster_kubeconfig("test-cluster", server="notaurl")

            assert "error" in json.loads(result)

    def test_vcluster_delete_tool_forwards_flags(self):
        """Test vcluster_delete passes its flags to the manager by keyword.

        Guards against a positional/keyword mixup silently changing which flag
        is set — for delete that would be a destructive bug.
        """
        from tools.vcluster import vcluster_delete

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.delete.return_value = Result.ok("deleted")
            MockManager.return_value = mock_manager

            vcluster_delete(
                "test-cluster",
                delete_namespace=True,
                keep_pvc=True,
                ignore_not_found=True,
                wait=False,
            )

            mock_manager.delete.assert_called_once_with(
                "test-cluster",
                None,
                delete_namespace=True,
                keep_pvc=True,
                ignore_not_found=True,
                wait=False,
            )

    def test_vcluster_delete_tool_defaults_preserve_namespace(self):
        """Test the tool defaults to delete_namespace=False."""
        from tools.vcluster import vcluster_delete

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.delete.return_value = Result.ok("deleted")
            MockManager.return_value = mock_manager

            vcluster_delete("test-cluster")

            assert mock_manager.delete.call_args.kwargs["delete_namespace"] is False

    def test_vcluster_create_tool_forwards_flags(self):
        """Test vcluster_create passes every new flag to the manager by keyword."""
        from tools.vcluster import vcluster_create

        with (
            patch("tools.vcluster.setup_kubernetes"),
            patch("tools.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.create.return_value = Result.ok("created")
            MockManager.return_value = mock_manager

            vcluster_create(
                "new-cluster",
                namespace="custom-ns",
                set_values={"a.b": "1"},
                chart_version="0.36.0",
                expose=True,
                create_namespace=False,
            )

            mock_manager.create.assert_called_once_with(
                "new-cluster",
                values=None,
                upgrade=None,
                namespace="custom-ns",
                set_values={"a.b": "1"},
                chart_version="0.36.0",
                chart_repo=None,
                chart_name=None,
                expose=True,
                create_namespace=False,
                kube_config_context_name=None,
            )
