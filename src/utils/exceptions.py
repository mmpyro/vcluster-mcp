"""Custom exceptions for vcluster operations."""

from typing import Optional


class VClusterError(Exception):
    """Base exception for vcluster operations."""
    pass


class VClusterCLIError(VClusterError):
    """Raised when vcluster CLI is not found or not executable."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationError(VClusterError):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")
