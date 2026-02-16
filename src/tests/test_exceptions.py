"""Tests for custom exception classes."""

import pytest
from utils.exceptions import (
    KubernetesError,
    NamespaceError,
    NamespaceNotFoundError,
    ValidationError,
    VClusterCLIError,
    VClusterCommandError,
    VClusterError,
    VClusterNotFoundError,
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


class TestVClusterNotFoundError:
    """Tests for VClusterNotFoundError."""

    def test_is_subclass_of_vcluster_error(self):
        """VClusterNotFoundError should inherit from VClusterError."""
        assert issubclass(VClusterNotFoundError, VClusterError)

    def test_with_name_only(self):
        """Should format message with name only when namespace is omitted."""
        exc = VClusterNotFoundError(name="my-cluster")
        assert exc.name == "my-cluster"
        assert exc.namespace is None
        assert str(exc) == "VCluster 'my-cluster' not found"

    def test_with_name_and_namespace(self):
        """Should format message with name and namespace."""
        exc = VClusterNotFoundError(name="my-cluster", namespace="dev")
        assert exc.name == "my-cluster"
        assert exc.namespace == "dev"
        assert str(exc) == "VCluster 'my-cluster' in namespace dev not found"

    def test_caught_as_vcluster_error(self):
        """Should be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise VClusterNotFoundError(name="test")


class TestVClusterCommandError:
    """Tests for VClusterCommandError."""

    def test_is_subclass_of_vcluster_error(self):
        """VClusterCommandError should inherit from VClusterError."""
        assert issubclass(VClusterCommandError, VClusterError)

    def test_stores_attributes(self):
        """Should store command, exit_code, and output."""
        exc = VClusterCommandError(
            command=["vcluster", "list"],
            exit_code=1,
            output="something failed",
        )
        assert exc.command == ["vcluster", "list"]
        assert exc.exit_code == 1
        assert exc.output == "something failed"

    def test_message_format(self):
        """Should format message with command, exit code, and output."""
        exc = VClusterCommandError(
            command=["vcluster", "list"],
            exit_code=127,
            output="not found",
        )
        msg = str(exc)
        assert "vcluster list" in msg
        assert "127" in msg
        assert "not found" in msg

    def test_caught_as_vcluster_error(self):
        """Should be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise VClusterCommandError(
                command=["vcluster", "list"],
                exit_code=1,
                output="error",
            )


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


class TestNamespaceError:
    """Tests for the base NamespaceError exception."""

    def test_is_subclass_of_vcluster_error(self):
        """NamespaceError should inherit from VClusterError."""
        assert issubclass(NamespaceError, VClusterError)

    def test_can_be_raised_and_caught(self):
        """NamespaceError should be raisable and catchable."""
        with pytest.raises(NamespaceError):
            raise NamespaceError("namespace problem")

    def test_caught_as_vcluster_error(self):
        """Should also be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise NamespaceError("namespace issue")


class TestNamespaceNotFoundError:
    """Tests for NamespaceNotFoundError."""

    def test_is_subclass_of_namespace_error(self):
        """NamespaceNotFoundError should inherit from NamespaceError."""
        assert issubclass(NamespaceNotFoundError, NamespaceError)

    def test_is_subclass_of_vcluster_error(self):
        """NamespaceNotFoundError should also inherit from VClusterError."""
        assert issubclass(NamespaceNotFoundError, VClusterError)

    def test_stores_namespace(self):
        """Should store the namespace attribute."""
        exc = NamespaceNotFoundError(namespace="prod")
        assert exc.namespace == "prod"

    def test_message_format(self):
        """Should format message with the namespace name."""
        exc = NamespaceNotFoundError(namespace="staging")
        assert str(exc) == "Namespace 'staging' not found"

    def test_caught_as_namespace_error(self):
        """Should be catchable as NamespaceError."""
        with pytest.raises(NamespaceError):
            raise NamespaceNotFoundError(namespace="test")

    def test_caught_as_vcluster_error(self):
        """Should be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise NamespaceNotFoundError(namespace="test")


class TestKubernetesError:
    """Tests for KubernetesError."""

    def test_is_subclass_of_vcluster_error(self):
        """KubernetesError should inherit from VClusterError."""
        assert issubclass(KubernetesError, VClusterError)

    def test_stores_attributes(self):
        """Should store operation and original_error attributes."""
        original = RuntimeError("connection refused")
        exc = KubernetesError(operation="list_pods", original_error=original)
        assert exc.operation == "list_pods"
        assert exc.original_error is original

    def test_message_format(self):
        """Should format message with operation and original error."""
        original = TimeoutError("timed out")
        exc = KubernetesError(operation="get_namespace", original_error=original)
        msg = str(exc)
        assert "get_namespace" in msg
        assert "timed out" in msg

    def test_caught_as_vcluster_error(self):
        """Should be catchable as VClusterError."""
        with pytest.raises(VClusterError):
            raise KubernetesError(
                operation="patch", original_error=Exception("fail")
            )


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
            VClusterNotFoundError,
            VClusterCommandError,
            VClusterCLIError,
            NamespaceError,
            NamespaceNotFoundError,
            KubernetesError,
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
            VClusterNotFoundError,
            VClusterCommandError,
            VClusterCLIError,
            NamespaceError,
            NamespaceNotFoundError,
            KubernetesError,
            ValidationError,
        ],
    )
    def test_all_exceptions_inherit_from_exception(self, exc_class):
        """All custom exceptions should be subclasses of Exception."""
        assert issubclass(exc_class, Exception)

    def test_namespace_not_found_inherits_from_namespace_error(self):
        """NamespaceNotFoundError should specifically inherit from NamespaceError."""
        assert issubclass(NamespaceNotFoundError, NamespaceError)
