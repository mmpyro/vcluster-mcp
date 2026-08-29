"""Tests for validation logic."""

import os
import pytest
from utils.exceptions import ValidationError


class TestNameValidation:
    """Tests for name validation logic."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "test",
            "test-cluster",
            "my-vcluster-123",
            "a",
            "cluster0",
        ],
    )
    def test_valid_names(self, vcluster_manager, valid_name):
        """Test that valid names pass validation."""
        vcluster_manager._validate_name(valid_name, "name")

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            "  ",
            "TEST",
            "test_Cluster",
            "test-Cluster",
            "-test",
            "test-",
            "Test",
        ],
    )
    def test_invalid_names(self, vcluster_manager, invalid_name):
        """Test that invalid names raise ValidationError."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_name(invalid_name, "name")

    def test_validation_with_custom_field_name(self, vcluster_manager):
        """Test validation uses custom field name in error message."""
        with pytest.raises(ValidationError) as exc_info:
            vcluster_manager._validate_name("", "namespace")

        assert exc_info.value.field == "namespace"


class TestValuesFileValidation:
    """Tests for values file validation logic."""

    def test_valid_values_file(self, vcluster_manager, tmp_path):
        """Test that valid values file passes validation."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")

        vcluster_manager._validate_values_file(str(values_file))

    def test_none_values_file(self, vcluster_manager):
        """Test that None values file is valid (optional)."""
        vcluster_manager._validate_values_file(None)

    def test_empty_string_values_file(self, vcluster_manager):
        """Test that empty string values file is valid (optional)."""
        vcluster_manager._validate_values_file("")

    def test_nonexistent_values_file(self, vcluster_manager):
        """Test that nonexistent file raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            vcluster_manager._validate_values_file("/nonexistent/values.yaml")

        assert exc_info.value.field == "values"

    def test_unreadable_values_file(self, vcluster_manager, tmp_path):
        """Test that unreadable file raises ValidationError."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")
        os.chmod(values_file, 0o000)

        try:
            with pytest.raises(ValidationError):
                vcluster_manager._validate_values_file(str(values_file))
        finally:
            os.chmod(values_file, 0o644)


class TestFlagValueValidation:
    """Tests for free-form CLI flag value validation."""

    @pytest.mark.parametrize(
        "valid_value",
        [
            "v0.36.0",
            "0.36.0",
            "https://charts.loft.sh",
            "vcluster",
            "my_context.name",
        ],
    )
    def test_valid_flag_values(self, vcluster_manager, valid_value):
        """Test that valid flag values pass validation."""
        vcluster_manager._validate_flag_value(valid_value, "field")

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "",
            "   ",
            "-x",
            "--chart-version",
            "line\nbreak",
            "null\x00byte",
        ],
    )
    def test_invalid_flag_values(self, vcluster_manager, invalid_value):
        """Test that flag-like or control-character values are rejected."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_flag_value(invalid_value, "field")


class TestSetValuesValidation:
    """Tests for helm --set key/value validation."""

    @pytest.mark.parametrize(
        "valid_key",
        [
            "replicas",
            "sync.toHost.ingresses.enabled",
            "nodeSelector[0].key",
            "_private",
            "a-b",
        ],
    )
    def test_valid_set_keys(self, vcluster_manager, valid_key):
        """Test that valid helm value paths pass validation."""
        vcluster_manager._validate_set_values({valid_key: "value"})

    @pytest.mark.parametrize(
        "invalid_key",
        [
            "",
            "   ",
            "a=b",
            "a,b",
            "-x",
            "a b",
            ".leading-dot",
        ],
    )
    def test_invalid_set_keys(self, vcluster_manager, invalid_key):
        """Test that malformed helm value paths are rejected."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_set_values({invalid_key: "value"})

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "one,two",
            "line\nbreak",
            "null\x00byte",
        ],
    )
    def test_invalid_set_values(self, vcluster_manager, invalid_value):
        """Test that comma and control characters in values are rejected.

        Helm splits --set on commas, so a comma would silently turn one
        assignment into two.
        """
        with pytest.raises(ValidationError):
            vcluster_manager._validate_set_values({"key": invalid_value})

    def test_non_string_set_value(self, vcluster_manager):
        """Test that a non-string value is rejected."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_set_values({"key": 1})


class TestServerUrlValidation:
    """Tests for kubeconfig server URL validation."""

    @pytest.mark.parametrize(
        "valid_url",
        [
            "https://vcluster.example.com",
            "http://10.0.0.1:6443",
            "https://1.2.3.4:6443",
        ],
    )
    def test_valid_server_urls(self, vcluster_manager, valid_url):
        """Test that http(s) URLs pass validation."""
        vcluster_manager._validate_server_url(valid_url)

    @pytest.mark.parametrize(
        "invalid_url",
        [
            "",
            "notaurl",
            "ftp://x.example.com",
            "https://",
            "-x",
        ],
    )
    def test_invalid_server_urls(self, vcluster_manager, invalid_url):
        """Test that non-http(s) or malformed URLs are rejected."""
        with pytest.raises(ValidationError):
            vcluster_manager._validate_server_url(invalid_url)


class TestValuesNormalization:
    """Tests for normalizing the values argument to a list."""

    def test_none_yields_empty_list(self, vcluster_manager):
        """Test that None normalizes to no values files."""
        assert vcluster_manager._normalize_values(None) == []

    def test_single_path_is_wrapped(self, vcluster_manager, tmp_path):
        """Test that a single path becomes a one-element list."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")

        assert vcluster_manager._normalize_values(str(values_file)) == [str(values_file)]

    def test_list_order_is_preserved(self, vcluster_manager, tmp_path):
        """Test that list order survives, since helm merges left to right."""
        first = tmp_path / "base.yaml"
        first.write_text("replicas: 1")
        second = tmp_path / "override.yaml"
        second.write_text("replicas: 2")

        normalized = vcluster_manager._normalize_values([str(first), str(second)])

        assert normalized == [str(first), str(second)]

    def test_missing_file_in_list_raises(self, vcluster_manager, tmp_path):
        """Test that every entry in the list is validated."""
        values_file = tmp_path / "values.yaml"
        values_file.write_text("replicas: 1")

        with pytest.raises(ValidationError):
            vcluster_manager._normalize_values([str(values_file), "/nonexistent.yaml"])
