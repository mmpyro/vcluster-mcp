"""Tests for MCP resources."""

import json
from unittest.mock import MagicMock, patch
from utils.exceptions import ValidationError
from utils.result import Result


class TestVClusterResources:
    """Tests for the read-only vcluster resources."""

    def test_cluster_certs_resource(self):
        """Test the certificate resource returns the report as JSON."""
        from resources.vcluster import cluster_certs_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.certs_check.return_value = Result.ok({"apiserver.crt": "ok"})
            MockManager.return_value = mock_manager

            payload = json.loads(cluster_certs_resource("custom-ns", "test-cluster"))

            mock_manager.certs_check.assert_called_once_with("test-cluster", "custom-ns")

        assert payload == {"apiserver.crt": "ok"}

    def test_namespace_metadata_resource(self):
        """Test labels and annotations are combined into one document."""
        from resources.vcluster import namespace_metadata_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.get_namespace_labels.return_value = Result.ok({"team": "core"})
            mock_manager.get_namespace_annotations.return_value = Result.ok({"owner": "me"})
            MockManager.return_value = mock_manager

            payload = json.loads(namespace_metadata_resource("custom-ns"))

        assert payload == {
            "namespace": "custom-ns",
            "labels": {"team": "core"},
            "annotations": {"owner": "me"},
        }

    def test_namespace_metadata_resource_error(self):
        """Test a missing namespace is reported once, not twice."""
        from resources.vcluster import namespace_metadata_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.get_namespace_labels.return_value = Result.err("not found")
            MockManager.return_value = mock_manager

            payload = json.loads(namespace_metadata_resource("missing-ns"))

            mock_manager.get_namespace_annotations.assert_not_called()

        assert payload["error"] == "not found"
