"""Tests for custom exception classes."""

import pytest
from utils.exceptions import (
    ValidationError,
    VClusterCLIError,
    VClusterError,
)


class TestVClusterError:
    """Tests for the base VClusterError exception."""

    def test_is_subclass_of_exception(self):
        """VClusterError should be a subclass of Exception."""
        assert issubclass(VClusterError, Exception)

    def test_can_be_raised_and_caught(self):
        """VClusterError should be raisable and catchable."""
        with pytest.raises(VClusterError):
            raise VClusterError("base error")

    def test_message(self):
        """VClusterError should store the message."""
        exc = VClusterError("something went wrong")
        assert str(exc) == "something went wrong"


class TestVClusterCLIError:
    """Tests for VClusterCLIError."""

    def test_is_subclass_of_vcluster_error(self):
        """VClusterCLIError should inherit from VClusterError."""
        assert issubclass(VClusterCLIError, VClusterError)

    def test_stores_message(self):
        """Should store the message attribute."""
        exc = VClusterCLIError("CLI not installed")
        assert exc.message == "CLI not installed"
        assert str(exc) == "CLI not installed"

    def test_caught_as_vcluster_error(self):
        """Should be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise VClusterCLIError("not found")


class TestValidationError:
    """Tests for ValidationError."""

    def test_is_subclass_of_vcluster_error(self):
        """ValidationError should inherit from VClusterError."""
        assert issubclass(ValidationError, VClusterError)

    def test_stores_attributes(self):
        """Should store field and message attributes."""
        exc = ValidationError(field="name", message="cannot be empty")
        assert exc.field == "name"
        assert exc.message == "cannot be empty"

    def test_message_format(self):
        """Should format message with field and message."""
        exc = ValidationError(field="namespace", message="invalid format")
        assert str(exc) == "Validation error for 'namespace': invalid format"

    def test_caught_as_vcluster_error(self):
        """Should be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise ValidationError(field="name", message="bad")


class TestExceptionHierarchy:
    """Tests verifying the full exception class hierarchy."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            VClusterCLIError,
            ValidationError,
        ],
    )
    def test_all_exceptions_inherit_from_vcluster_error(self, exc_class):
        """All custom exceptions should be subclasses of VClusterError."""
        assert issubclass(exc_class, VClusterError)

    @pytest.mark.parametrize(
        "exc_class",
        [
            VClusterError,
            VClusterCLIError,
            ValidationError,
        ],
    )
    def test_all_exceptions_inherit_from_exception(self, exc_class):
        """All custom exceptions should be subclasses of Exception."""
        assert issubclass(exc_class, Exception)
