"""Custom exceptions for vcluster operations."""


class VClusterError(Exception):
    """Base exception for vcluster operations."""
    pass


class VClusterNotFoundError(VClusterError):
    """Raised when a vcluster is not found."""

    def __init__(self, name: str, namespace: str = None):
        self.name = name
        self.namespace = namespace
        ns_msg = f" in namespace {namespace}" if namespace else ""
        super().__init__(f"VCluster '{name}'{ns_msg} not found")


class VClusterCommandError(VClusterError):
    """Raised when a vcluster CLI command fails."""

    def __init__(self, command: str, exit_code: int, output: str):
        self.command = command
        self.exit_code = exit_code
        self.output = output
        super().__init__(f"Command '{' '.join(command)}' failed with code {exit_code}: {output}")


class VClusterCLIError(VClusterError):
    """Raised when vcluster CLI is not found or not executable."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NamespaceError(VClusterError):
    """Base for namespace-related errors."""
    pass


class NamespaceNotFoundError(NamespaceError):
    """Raised when a namespace is not found."""

    def __init__(self, namespace: str):
        self.namespace = namespace
        super().__init__(f"Namespace '{namespace}' not found")


class KubernetesError(VClusterError):
    """Raised when a Kubernetes operation fails."""

    def __init__(self, operation: str, original_error: Exception):
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"Kubernetes {operation} failed: {original_error}")


class ValidationError(VClusterError):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")
