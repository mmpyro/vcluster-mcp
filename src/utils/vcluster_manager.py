"""Manager class for vcluster operations with improved error handling."""

import subprocess
import os
import re
import json
from dataclasses import dataclass
from typing import Optional, Dict, List

from kubernetes import client
from kubernetes.client.exceptions import ApiException

from utils.result import Result
from utils.exceptions import (
    VClusterCLIError,
    ValidationError,
)


@dataclass
class CommandResult:
    """Dataclass for command execution result"""
    exit_code: int
    output: str


# Kubernetes name validation pattern
VALID_NAME_PATTERN = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')


class VClusterManager:
    """Manager class for vcluster operations with improved error handling."""

    def __init__(self):
        """Initialize the VCluster Manager"""
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def _run_command(self, cmd: List[str]) -> CommandResult:
        """Run a shell command and return the result as CommandResult.

        Args:
            cmd: Command to run as list of strings

        Returns:
            CommandResult with exit_code and output

        Raises:
            VClusterCLIError: If the vcluster command is not found
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            return CommandResult(
                exit_code=result.returncode,
                output=result.stdout if result.returncode == 0 else result.stderr
            )
        except FileNotFoundError:
            raise VClusterCLIError(
                "vcluster CLI not found. Is it installed and in your PATH?"
            )
        except PermissionError as e:
            raise VClusterCLIError(
                f"Permission denied running vcluster command: {e}"
            )
        except OSError as e:
            raise VClusterCLIError(
                f"Unexpected error running vcluster command: {e}"
            )

    def _validate_name(self, name: str, field_name: str = "name") -> None:
        """Validate a resource name.

        Args:
            name: The name to validate
            field_name: The field name for error messages

        Raises:
            ValidationError: If the name is invalid
        """
        if not name or not name.strip():
            raise ValidationError(field_name, "cannot be empty")

        if not VALID_NAME_PATTERN.match(name):
            raise ValidationError(
                field_name,
                "must match pattern: ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
            )

    def _validate_values_file(self, values: str) -> None:
        """Validate a values file path.

        Args:
            values: The path to validate

        Raises:
            ValidationError: If the values file is invalid
        """
        if values and not os.path.isfile(values):
            raise ValidationError("values", f"file not found: {values}")

        if values and not os.access(values, os.R_OK):
            raise ValidationError("values", f"file not readable: {values}")

    # ==================== CLI Command Wrappers ====================

    def list(self) -> Result[List[Dict]]:
        """List all vclusters.

        Command: vcluster list --output json

        Returns:
            Result containing list of vclusters on success, or error message on failure
        """
        cmd = ["vcluster", "list", "--output", "json"]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster list failed: {result.output}")

            try:
                data = json.loads(result.output)
                # Handle case where output is not a list
                if isinstance(data, dict) and 'items' in data:
                    return Result.ok(data['items'])
                elif isinstance(data, list):
                    return Result.ok(data)
                else:
                    return Result.ok([data])

            except json.JSONDecodeError as e:
                return Result.err(f"Failed to parse vcluster output: {e}")

        except VClusterCLIError as e:
            return Result.err(str(e))

    def describe(self, name: str, namespace: Optional[str] = None) -> Result[Dict]:
        """Describe a specific vcluster.

        Command: vcluster describe <name> -n <namespace> --output json

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)

        Returns:
            Result containing vcluster details on success, or error message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if namespace is None:
            namespace = f"vcluster-{name}"

        cmd = ["vcluster", "describe", name, "-n", namespace, "--output", "json"]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                # Check if it's a "not found" error
                if "not found" in result.output.lower() or "does not exist" in result.output.lower():
                    return Result.err(f"VCluster '{name}' in namespace '{namespace}' not found")
                return Result.err(f"vcluster describe failed: {result.output}")

            try:
                data = json.loads(result.output)
                return Result.ok(data)
            except json.JSONDecodeError as e:
                return Result.err(f"Failed to parse vcluster output: {e}")

        except VClusterCLIError as e:
            return Result.err(str(e))

    def pause(self, name: str, namespace: Optional[str] = None) -> Result[CommandResult]:
        """Pause a vcluster.

        Command: vcluster pause <name> -n <namespace>

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if namespace is None:
            namespace = f"vcluster-{name}"

        cmd = ["vcluster", "pause", name, "-n", namespace]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster pause failed: {result.output}")

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    def resume(self, name: str, namespace: Optional[str] = None) -> Result[CommandResult]:
        """Resume a vcluster.

        Command: vcluster resume <name> -n <namespace>

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if namespace is None:
            namespace = f"vcluster-{name}"

        cmd = ["vcluster", "resume", name, "-n", namespace]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster resume failed: {result.output}")

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    def delete(self, name: str, namespace: Optional[str] = None) -> Result[CommandResult]:
        """Delete a vcluster.

        Command: vcluster delete <name> -n <namespace> --delete-namespace

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if namespace is None:
            namespace = f"vcluster-{name}"

        cmd = ["vcluster", "delete", name, "-n", namespace, "--delete-namespace"]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster delete failed: {result.output}")

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    def create(self, name: str, values: Optional[str] = None, upgrade: Optional[bool] = None) -> Result[CommandResult]:
        """Create a vcluster.

        Command: vcluster create <name> --connect=false --values <path to values file> --upgrade

        Args:
            name: Name of the vcluster to create
            values: Path to values file (optional)
            upgrade: If True, upgrade the cluster if it was created before (optional)

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        # Validate name
        self._validate_name(name, "name")

        # Validate values file if provided
        if values:
            self._validate_values_file(values)

        cmd = ["vcluster", "create", name, "--connect=false"]

        if values:
            cmd.extend(["--values", values])

        if upgrade:
            cmd.append("--upgrade")

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster create failed: {result.output}")

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    # ==================== Namespace Labels CRUD ====================

    def get_namespace_labels(self, namespace: str) -> Result[Dict[str, str]]:
        """Get labels for a specific namespace.

        Args:
            namespace: Name of the namespace

        Returns:
            Result containing dictionary of labels on success, or error on failure
        """
        try:
            ns = self.core_v1.read_namespace(name=namespace)
            return Result.ok(ns.metadata.labels or {})
        except ApiException as e:
            if e.status == 404:
                return Result.err(f"Namespace '{namespace}' not found")
            return Result.err(f"Error reading namespace {namespace}: {e}")

    def set_namespace_label(self, namespace: str, key: str, value: str) -> Result[bool]:
        """Create or update a label on a namespace.

        Args:
            namespace: Name of the namespace
            key: Label key
            value: Label value

        Returns:
            Result containing True on success, or error on failure
        """
        try:
            # Get current labels
            ns = self.core_v1.read_namespace(name=namespace)
            labels = ns.metadata.labels or {}

            # Update the label
            labels[key] = value

            # Apply the update
            body = {"metadata": {"labels": labels}}
            self.core_v1.patch_namespace(name=namespace, body=body)
            return Result.ok(True)
        except ApiException as e:
            if e.status == 404:
                return Result.err(f"Namespace '{namespace}' not found")
            return Result.err(f"Error setting label on namespace {namespace}: {e}")

    def delete_namespace_label(self, namespace: str, key: str) -> Result[bool]:
        """Delete a label from a namespace.

        Args:
            namespace: Name of the namespace
            key: Label key to delete

        Returns:
            Result containing True on success (including if label didn't exist),
            or error on failure
        """
        try:
            # Get current labels
            ns = self.core_v1.read_namespace(name=namespace)
            labels = ns.metadata.labels or {}

            # Check if label exists
            if key not in labels:
                return Result.ok(True)  # Consider it success if label doesn't exist

            # Remove the label
            del labels[key]

            # Apply the update
            body = {"metadata": {"labels": labels}}
            self.core_v1.patch_namespace(name=namespace, body=body)
            return Result.ok(True)
        except ApiException as e:
            if e.status == 404:
                return Result.err(f"Namespace '{namespace}' not found")
            return Result.err(f"Error deleting label from namespace {namespace}: {e}")

    # ==================== Namespace Annotations CRUD ====================

    def get_namespace_annotations(self, namespace: str) -> Result[Dict[str, str]]:
        """Get annotations for a specific namespace.

        Args:
            namespace: Name of the namespace

        Returns:
            Result containing dictionary of annotations on success, or error on failure
        """
        try:
            ns = self.core_v1.read_namespace(name=namespace)
            return Result.ok(ns.metadata.annotations or {})
        except ApiException as e:
            if e.status == 404:
                return Result.err(f"Namespace '{namespace}' not found")
            return Result.err(f"Error reading namespace {namespace}: {e}")

    def set_namespace_annotation(self, namespace: str, key: str, value: str) -> Result[bool]:
        """Create or update an annotation on a namespace.

        Args:
            namespace: Name of the namespace
            key: Annotation key
            value: Annotation value

        Returns:
            Result containing True on success, or error on failure
        """
        try:
            # Get current annotations
            ns = self.core_v1.read_namespace(name=namespace)
            annotations = ns.metadata.annotations or {}

            # Update the annotation
            annotations[key] = value

            # Apply the update
            body = {"metadata": {"annotations": annotations}}
            self.core_v1.patch_namespace(name=namespace, body=body)
            return Result.ok(True)
        except ApiException as e:
            if e.status == 404:
                return Result.err(f"Namespace '{namespace}' not found")
            return Result.err(f"Error setting annotation on namespace {namespace}: {e}")

    def delete_namespace_annotation(self, namespace: str, key: str) -> Result[bool]:
        """Delete an annotation from a namespace.

        Args:
            namespace: Name of the namespace
            key: Annotation key to delete

        Returns:
            Result containing True on success (including if annotation didn't exist),
            or error on failure
        """
        try:
            # Get current annotations
            ns = self.core_v1.read_namespace(name=namespace)
            annotations = ns.metadata.annotations or {}

            # Check if annotation exists
            if key not in annotations:
                return Result.ok(True)  # Consider it success if annotation doesn't exist

            # Remove the annotation
            del annotations[key]

            # Apply the update
            body = {"metadata": {"annotations": annotations}}
            self.core_v1.patch_namespace(name=namespace, body=body)
            return Result.ok(True)
        except ApiException as e:
            if e.status == 404:
                return Result.err(f"Namespace '{namespace}' not found")
            return Result.err(f"Error deleting annotation from namespace {namespace}: {e}")
