"""Tests for namespace metadata operations (labels and annotations)."""

from unittest.mock import MagicMock

import pytest

from kubernetes.client.exceptions import ApiException


class TestNamespaceLabels:
    """Tests for namespace labels CRUD operations."""

    def test_get_namespace_labels_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test successful get namespace labels."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = {'app': 'test', 'env': 'production'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.get_namespace_labels("test-ns")
        
        assert result.is_ok
        assert result.value == {'app': 'test', 'env': 'production'}

    def test_get_namespace_labels_not_found(self, vcluster_manager, mock_kubernetes_clients):
        """Test get namespace labels when namespace doesn't exist."""
        api_exception = ApiException(status=404)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.get_namespace_labels("nonexistent-ns")
        
        assert result.is_err
        assert "not found" in result.error

    def test_get_namespace_labels_no_labels(self, vcluster_manager, mock_kubernetes_clients):
        """Test get namespace labels when namespace has no labels."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = None
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.get_namespace_labels("test-ns")
        
        assert result.is_ok
        assert result.value == {}

    def test_set_namespace_label_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test successful set namespace label."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = {'existing': 'value'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.set_namespace_label("test-ns", "new-key", "new-value")
        
        assert result.is_ok
        assert result.value is True
        mock_kubernetes_clients['core_v1'].patch_namespace.assert_called_once()

    def test_set_namespace_label_not_found(self, vcluster_manager, mock_kubernetes_clients):
        """Test set namespace label when namespace doesn't exist."""
        api_exception = ApiException(status=404)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.set_namespace_label("nonexistent-ns", "key", "value")
        
        assert result.is_err
        assert "not found" in result.error

    def test_set_namespace_label_kubernetes_error(self, vcluster_manager, mock_kubernetes_clients):
        """Test set namespace label when Kubernetes API fails."""
        api_exception = ApiException(status=500)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.set_namespace_label("test-ns", "key", "value")
        
        assert result.is_err

    def test_delete_namespace_label_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test successful delete namespace label."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = {'key-to-delete': 'value', 'keep': 'this'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.delete_namespace_label("test-ns", "key-to-delete")
        
        assert result.is_ok
        assert result.value is True

    def test_delete_namespace_label_not_found(self, vcluster_manager, mock_kubernetes_clients):
        """Test delete namespace label when namespace doesn't exist."""
        api_exception = ApiException(status=404)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.delete_namespace_label("nonexistent-ns", "key")
        
        assert result.is_err
        assert "not found" in result.error

    def test_delete_nonexistent_label_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test delete label that doesn't exist returns success."""
        mock_ns = MagicMock()
        mock_ns.metadata.labels = {'existing': 'value'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.delete_namespace_label("test-ns", "nonexistent-key")
        
        # Should succeed because the operation is idempotent
        assert result.is_ok
        assert result.value is True


class TestNamespaceAnnotations:
    """Tests for namespace annotations CRUD operations."""

    def test_get_namespace_annotations_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test successful get namespace annotations."""
        mock_ns = MagicMock()
        mock_ns.metadata.annotations = {'description': 'test ns', 'owner': 'admin'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.get_namespace_annotations("test-ns")
        
        assert result.is_ok
        assert result.value == {'description': 'test ns', 'owner': 'admin'}

    def test_get_namespace_annotations_not_found(self, vcluster_manager, mock_kubernetes_clients):
        """Test get namespace annotations when namespace doesn't exist."""
        api_exception = ApiException(status=404)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.get_namespace_annotations("nonexistent-ns")
        
        assert result.is_err
        assert "not found" in result.error

    def test_get_namespace_annotations_no_annotations(self, vcluster_manager, mock_kubernetes_clients):
        """Test get namespace annotations when namespace has no annotations."""
        mock_ns = MagicMock()
        mock_ns.metadata.annotations = None
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.get_namespace_annotations("test-ns")
        
        assert result.is_ok
        assert result.value == {}

    def test_set_namespace_annotation_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test successful set namespace annotation."""
        mock_ns = MagicMock()
        mock_ns.metadata.annotations = {'existing': 'value'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.set_namespace_annotation("test-ns", "new-key", "new-value")
        
        assert result.is_ok
        assert result.value is True
        mock_kubernetes_clients['core_v1'].patch_namespace.assert_called_once()

    def test_set_namespace_annotation_not_found(self, vcluster_manager, mock_kubernetes_clients):
        """Test set namespace annotation when namespace doesn't exist."""
        api_exception = ApiException(status=404)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.set_namespace_annotation("nonexistent-ns", "key", "value")
        
        assert result.is_err
        assert "not found" in result.error

    def test_delete_namespace_annotation_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test successful delete namespace annotation."""
        mock_ns = MagicMock()
        mock_ns.metadata.annotations = {'key-to-delete': 'value', 'keep': 'this'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.delete_namespace_annotation("test-ns", "key-to-delete")
        
        assert result.is_ok
        assert result.value is True

    def test_delete_namespace_annotation_not_found(self, vcluster_manager, mock_kubernetes_clients):
        """Test delete namespace annotation when namespace doesn't exist."""
        api_exception = ApiException(status=404)
        mock_kubernetes_clients['core_v1'].read_namespace.side_effect = api_exception
        
        result = vcluster_manager.delete_namespace_annotation("nonexistent-ns", "key")
        
        assert result.is_err
        assert "not found" in result.error

    def test_delete_nonexistent_annotation_success(self, vcluster_manager, mock_kubernetes_clients):
        """Test delete annotation that doesn't exist returns success."""
        mock_ns = MagicMock()
        mock_ns.metadata.annotations = {'existing': 'value'}
        mock_kubernetes_clients['core_v1'].read_namespace.return_value = mock_ns
        
        result = vcluster_manager.delete_namespace_annotation("test-ns", "nonexistent-key")
        
        # Should succeed because the operation is idempotent
        assert result.is_ok
        assert result.value is True
