"""Tests for validation logic."""

import os
from unittest.mock import patch

import pytest

from utils.exceptions import ValidationError


class TestNameValidation:
    """Tests for name validation logic."""

    @pytest.mark.parametrize("valid_name", [
        "test",
        "test-cluster",
        "my-vcluster-123",
        "a",
        "cluster0",
    ])
    def test_valid_names(self, vcluster_manager, valid_name):
        """Test that valid names pass validation."""
        # Should not raise any exception
        vcluster_manager._validate_name(valid_name, "name")

    @pytest.mark.parametrize("invalid_name", [
        "",
        "  ",
        "TEST",
        "test_Cluster",
        "test-Cluster",
        "-test",
        "test-",
        "Test",
    ])
    def test_invalid_names(self, vcluster_manager, invalid_name):
        """Test that invalid names raise ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_name(invalid_name, "name")

    def test_validation_with_custom_field_name(self, vcluster_manager):
        """Test validation uses custom field name in error message."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_name("", "namespace")


class TestValuesFileValidation:
    """Tests for values file validation logic."""

    def test_valid_values_file(self, vcluster_manager, tmp_path):
        """Test that valid values file passes validation."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")
        
        # Should not raise any exception
        vcluster_manager._validate_values_file(str(values_file))

    def test_none_values_file(self, vcluster_manager):
        """Test that None values file is valid (optional)."""
        # Should not raise any exception
        vcluster_manager._validate_values_file(None)

    def test_empty_string_values_file(self, vcluster_manager):
        """Test that empty string values file is valid (optional)."""
        # Should not raise any exception
        vcluster_manager._validate_values_file("")

    def test_nonexistent_values_file(self, vcluster_manager):
        """Test that nonexistent file raises ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_values_file("/nonexistent/values.yaml")

    def test_unreadable_values_file(self, vcluster_manager, tmp_path):
        """Test that unreadable file raises ValidationError."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")
        os.chmod(values_file, 0o000)  # Remove all permissions
        
        try:
            with pytest.raises(ValidationError):
                vcluster_manager._validate_values_file(str(values_file))
        finally:
            os.chmod(values_file, 0o644)  # Restore permissions
