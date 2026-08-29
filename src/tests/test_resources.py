"""Tests for MCP resources."""

import json
from unittest.mock import MagicMock, patch
from utils.exceptions import ValidationError
from utils.result import Result


class TestVClusterResources:
    """Tests for the read-only vcluster resources."""

    def test_clusters_resource(self):
        """Test the cluster list resource returns JSON."""
        from resources.vcluster import clusters_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = Result.ok([{"name": "test"}])
            MockManager.return_value = mock_manager

            payload = json.loads(clusters_resource())

        assert payload == [{"name": "test"}]

    def test_clusters_resource_error(self):
        """Test a failed listing is returned in band as JSON."""
        from resources.vcluster import clusters_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = Result.err("vcluster list failed")
            MockManager.return_value = mock_manager

            payload = json.loads(clusters_resource())

        assert payload["error"] == "vcluster list failed"

    def test_cluster_resource(self):
        """Test the describe resource passes name and namespace through."""
        from resources.vcluster import cluster_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.describe.return_value = Result.ok({"status": "Running"})
            MockManager.return_value = mock_manager

            payload = json.loads(cluster_resource("custom-ns", "test-cluster"))

            mock_manager.describe.assert_called_once_with("test-cluster", "custom-ns")

        assert payload == {"status": "Running"}

    def test_cluster_resource_validation_error(self):
        """Test an invalid name is reported as JSON rather than raised."""
        from resources.vcluster import cluster_resource

        with (
            patch("resources.vcluster.setup_kubernetes"),
            patch("resources.vcluster.VClusterManager") as MockManager,
        ):
            mock_manager = MagicMock()
            mock_manager.describe.side_effect = ValidationError("name", "invalid")
            MockManager.return_value = mock_manager

            payload = json.loads(cluster_resource("custom-ns", "InvalidName"))

        assert "error" in payload

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
