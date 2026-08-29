"""Shared fixtures for VClusterManager tests."""

import pytest
from unittest.mock import MagicMock, patch
from utils.vcluster_manager import VClusterManager


@pytest.fixture
def mock_kubernetes_clients():
    """Mock Kubernetes API clients."""
    with (
        patch("utils.vcluster_manager.client.CoreV1Api") as mock_core,
        patch("utils.vcluster_manager.client.AppsV1Api") as mock_apps,
    ):
        mock_core_v1 = MagicMock()
        mock_apps_v1 = MagicMock()
        mock_core.return_value = mock_core_v1
        mock_apps.return_value = mock_apps_v1
        yield {"core_v1": mock_core_v1, "apps_v1": mock_apps_v1}


@pytest.fixture
def vcluster_manager(mock_kubernetes_clients):
    """Create a VClusterManager instance with mocked clients."""
    return VClusterManager()


@pytest.fixture
def mock_successful_vcluster_list():
    """Mock successful vcluster list output."""
    return [
        {
            "name": "test-cluster",
            "namespace": "vcluster-test-cluster",
            "status": "Running",
        },
        {
            "name": "dev-cluster",
            "namespace": "vcluster-dev-cluster",
            "status": "Paused",
        },
    ]


@pytest.fixture
def mock_kubeconfig_yaml():
    """Minimal kubeconfig as printed by `vcluster connect --print`."""
    return (
        "apiVersion: v1\n"
        "kind: Config\n"
        "current-context: vcluster_test-cluster_vcluster-test-cluster\n"
        "clusters:\n"
        "- name: local\n"
        "  cluster:\n"
        "    server: https://localhost:8443\n"
        "contexts: []\n"
        "users: []\n"
    )


@pytest.fixture
def mock_successful_vcluster_describe():
    """Mock successful vcluster describe output."""
    return {
        "name": "test-cluster",
        "namespace": "vcluster-test-cluster",
        "status": "Running",
        "created": "2024-01-01T00:00:00Z",
    }
