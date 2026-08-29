"""Manager class for vcluster operations with improved error handling."""

import subprocess
import os
import shlex
import re
import json
import tempfile
import urllib.parse
from dataclasses import dataclass
from typing import Optional, Dict, List, Union

import yaml
from kubernetes import client
from kubernetes.client.exceptions import ApiException

from utils.result import Result
from utils.exceptions import (
    VClusterCLIError,
    VClusterTimeoutError,
    ValidationError,
)


@dataclass
class CommandResult:
    """Dataclass for command execution result"""
    exit_code: int
    output: str


# Kubernetes name validation pattern
VALID_NAME_PATTERN = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')

# Helm value key validation pattern (for --set key=value)
VALID_SET_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.\[\]-]*$')

# Bound the kubeconfig export, which can otherwise block on a port-forward
KUBECONFIG_TIMEOUT_SECONDS = 60.0


class VClusterManager:
    """Manager class for vcluster operations with improved error handling."""

    def __init__(self):
        """Initialize the VCluster Manager"""
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def _run_command(self, cmd: List[str], timeout: Optional[float] = None) -> CommandResult:
        """Run a shell command and return the result as CommandResult.

        Args:
            cmd: Command to run as list of strings
            timeout: Optional timeout in seconds. If not provided, the command
                is allowed to run indefinitely.

        Returns:
            CommandResult with exit_code and output

        Raises:
            VClusterCLIError: If the vcluster command is not found or times out
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout
            )
            return CommandResult(
                exit_code=result.returncode,
                output=result.stdout if result.returncode == 0 else result.stderr
            )
        except subprocess.TimeoutExpired:
            raise VClusterTimeoutError(
                f"vcluster command timed out after {timeout}s: {' '.join(cmd)}"
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

    def _validate_flag_value(self, value: str, field_name: str) -> None:
        """Validate a free-form value passed as a CLI flag argument.

        Argv is a list and no shell is involved, so shell injection is not the
        risk. What matters is a value that starts with '-', which the CLI would
        parse as another flag, and embedded control characters.

        Args:
            value: The value to validate
            field_name: The field name for error messages

        Raises:
            ValidationError: If the value is invalid
        """
        if not value or not value.strip():
            raise ValidationError(field_name, "cannot be empty")

        if value.startswith("-"):
            raise ValidationError(field_name, "must not start with '-'")

        if any(char in value for char in ("\n", "\r", "\x00")):
            raise ValidationError(field_name, "must not contain control characters")

    def _validate_server_url(self, server: str) -> None:
        """Validate an API server URL destined for the kubeconfig.

        Args:
            server: The URL to validate

        Raises:
            ValidationError: If the URL is not a usable http(s) address
        """
        self._validate_flag_value(server, "server")

        parsed = urllib.parse.urlparse(server)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError(
                "server",
                "must be an http(s) URL, e.g. https://vcluster.example.com"
            )

    def _validate_set_values(self, set_values: Dict[str, str]) -> None:
        """Validate helm --set key/value pairs.

        Args:
            set_values: Mapping of helm value paths to values

        Raises:
            ValidationError: If a key or value is invalid
        """
        for key, value in set_values.items():
            self._validate_flag_value(key, "set_values")

            if not VALID_SET_KEY_PATTERN.match(key):
                raise ValidationError(
                    "set_values",
                    f"invalid helm value key: {key}"
                )

            if not isinstance(value, str):
                raise ValidationError(
                    "set_values",
                    f"value for '{key}' must be a string"
                )

            # helm splits --set on commas, so a comma silently becomes a
            # second assignment rather than part of the value
            if "," in value or any(char in value for char in ("\n", "\r", "\x00")):
                raise ValidationError(
                    "set_values",
                    f"value for '{key}' must not contain commas or control "
                    f"characters; use a values file instead"
                )

    def _normalize_values(self, values: Optional[Union[str, List[str]]]) -> List[str]:
        """Normalize the values argument to a validated list of file paths.

        Args:
            values: A single path, a list of paths, or None

        Returns:
            List of validated values file paths (possibly empty)

        Raises:
            ValidationError: If any values file is missing or unreadable
        """
        if values is None:
            value_files: List[str] = []
        elif isinstance(values, str):
            value_files = [values]
        else:
            value_files = list(values)

        for value_file in value_files:
            self._validate_values_file(value_file)

        return value_files

    def _write_kubeconfig(self, name: str, content: str) -> str:
        """Write kubeconfig content to a private temporary file.

        ``tempfile.mkstemp`` creates the file with 0600 permissions, so the
        credentials are never briefly world-readable.

        Args:
            name: Name of the vcluster, used in the filename prefix
            content: The kubeconfig YAML to write

        Returns:
            Absolute path to the created file. The caller owns this file and
            is responsible for deleting it.

        Raises:
            OSError: If the file cannot be created or written
        """
        fd, path = tempfile.mkstemp(prefix=f"vcluster-{name}-", suffix=".yaml")

        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(content)
        except OSError:
            os.unlink(path)
            raise

        return path

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

    def certs_check(self, name: str, namespace: Optional[str] = None) -> Result[Union[Dict, List]]:
        """Check the control-plane certificates of a vcluster.

        Command: vcluster certs check <name> -n <namespace> -s --output json

        Expired control-plane certificates surface as opaque connection
        failures, so this is a first-class diagnostic.

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)

        Returns:
            Result containing the certificate report on success, or error
            message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if namespace is None:
            namespace = f"vcluster-{name}"

        # -s keeps log output off stdout so the JSON parses cleanly
        cmd = ["vcluster", "certs", "check", name, "-n", namespace, "-s", "--output", "json"]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                # Check if it's a "not found" error
                if "not found" in result.output.lower() or "does not exist" in result.output.lower():
                    return Result.err(f"VCluster '{name}' in namespace '{namespace}' not found")
                return Result.err(f"vcluster certs check failed: {result.output}")

            try:
                data = json.loads(result.output)
                return Result.ok(data)
            except json.JSONDecodeError as e:
                return Result.err(f"Failed to parse vcluster output: {e}")

        except VClusterCLIError as e:
            return Result.err(str(e))

    def kubeconfig(
        self,
        name: str,
        namespace: Optional[str] = None,
        server: Optional[str] = None,
        insecure: bool = False,
        timeout: float = KUBECONFIG_TIMEOUT_SECONDS,
    ) -> Result[Dict[str, str]]:
        """Export a vcluster kubeconfig to a private temporary file.

        Command: vcluster connect <name> -n <namespace> -s --print
        --background-proxy=false [--server <url>] [--insecure]

        Unlike ``call``, this does not switch the caller's kube context. The
        kubeconfig is written to a 0600 temp file rather than returned inline,
        because it contains client credentials.

        ``--background-proxy=false`` and the timeout together stop the command
        from blocking indefinitely on a port-forward when the vcluster is not
        directly reachable.

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)
            server: Override the API server address in the kubeconfig (optional)
            insecure: If True, skip TLS verification in the generated kubeconfig
            timeout: Seconds to wait before giving up

        Returns:
            Result containing a dict with ``kubeconfig_path``, ``context`` and
            ``server`` on success, or error message on failure. The caller owns
            the file at ``kubeconfig_path`` and should delete it after use.
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if server is not None:
            self._validate_server_url(server)

        if namespace is None:
            namespace = f"vcluster-{name}"

        cmd = [
            "vcluster", "connect", name, "-n", namespace,
            "-s", "--print", "--background-proxy=false",
        ]

        if server:
            cmd.extend(["--server", server])

        if insecure:
            cmd.append("--insecure")

        try:
            result = self._run_command(cmd, timeout=timeout)

            if result.exit_code != 0:
                if "not found" in result.output.lower() or "does not exist" in result.output.lower():
                    return Result.err(f"VCluster '{name}' in namespace '{namespace}' not found")
                return Result.err(f"vcluster kubeconfig failed: {result.output}")

            try:
                document = yaml.safe_load(result.output)
            except yaml.YAMLError as e:
                return Result.err(f"Failed to parse vcluster kubeconfig: {e}")

            if not isinstance(document, dict) or "clusters" not in document:
                return Result.err(
                    "vcluster connect --print did not return a kubeconfig"
                )

            try:
                path = self._write_kubeconfig(name, result.output)
            except OSError as e:
                return Result.err(f"Failed to write kubeconfig file: {e}")

            return Result.ok({
                "kubeconfig_path": path,
                "context": str(document.get("current-context", "")),
                "server": self._extract_server(document),
            })

        except VClusterTimeoutError as e:
            # Without --server the CLI falls back to port-forwarding, prints the
            # kubeconfig and then blocks holding the forward open. The printed
            # config would point at a local port served by the process we just
            # killed, so it is unusable - tell the caller what to do instead.
            return Result.err(
                f"{e}. The vcluster is not directly reachable, so "
                f"'vcluster connect --print' fell back to port-forwarding and did "
                f"not exit. Pass server=<https://...>, the ingress or LoadBalancer "
                f"address of the vcluster API, to get a standalone kubeconfig."
            )
        except VClusterCLIError as e:
            return Result.err(str(e))

    @staticmethod
    def _extract_server(document: Dict) -> str:
        """Pull the API server URL out of a parsed kubeconfig, best effort.

        Args:
            document: Parsed kubeconfig mapping

        Returns:
            The first cluster's server URL, or an empty string if absent
        """
        clusters = document.get("clusters") or []

        if not isinstance(clusters, list) or not clusters:
            return ""

        entry = clusters[0]

        if not isinstance(entry, dict):
            return ""

        cluster = entry.get("cluster")

        if not isinstance(cluster, dict):
            return ""

        return str(cluster.get("server", ""))

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

    def delete(
        self,
        name: str,
        namespace: Optional[str] = None,
        delete_namespace: bool = False,
        keep_pvc: bool = False,
        ignore_not_found: bool = False,
        wait: bool = True,
    ) -> Result[CommandResult]:
        """Delete a vcluster.

        Command: vcluster delete <name> -n <namespace> [--delete-namespace]
        [--keep-pvc] [--ignore-not-found] [--wait=false]

        By default the host namespace is preserved. The vcluster CLI still
        applies its own ``--auto-delete-namespace`` (default true), which
        removes only namespaces that vcluster itself created.

        Args:
            name: Name of the vcluster
            namespace: Namespace of the vcluster (optional, defaults to vcluster-name)
            delete_namespace: If True, delete the host namespace and everything
                else inside it. Destructive - leave False unless the namespace
                exists solely for this vcluster.
            keep_pvc: If True, retain the vcluster's persistent volume claim
            ignore_not_found: If True, do not error when the vcluster is absent
            wait: If False, return without waiting for the deletion to finish

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if namespace is None:
            namespace = f"vcluster-{name}"

        cmd = ["vcluster", "delete", name, "-n", namespace]

        # Only emit flags that deviate from the CLI's own defaults
        if delete_namespace:
            cmd.append("--delete-namespace")

        if keep_pvc:
            cmd.append("--keep-pvc")

        if ignore_not_found:
            cmd.append("--ignore-not-found")

        if not wait:
            cmd.append("--wait=false")

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster delete failed: {result.output}")

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    def create(
        self,
        name: str,
        values: Optional[Union[str, List[str]]] = None,
        upgrade: Optional[bool] = None,
        namespace: Optional[str] = None,
        set_values: Optional[Dict[str, str]] = None,
        chart_version: Optional[str] = None,
        chart_repo: Optional[str] = None,
        chart_name: Optional[str] = None,
        expose: bool = False,
        create_namespace: Optional[bool] = None,
        kube_config_context_name: Optional[str] = None,
    ) -> Result[CommandResult]:
        """Create a vcluster.

        Command: vcluster create <name> --connect=false [-n <namespace>]
        [--values <path>]... [--set key=value]... [--chart-version <v>]
        [--chart-repo <url>] [--chart-name <n>] [--kube-config-context-name <n>]
        [--expose] [--create-namespace=false] [--upgrade]

        ``--connect=false`` is always passed: creating a vcluster must never
        silently switch the caller's kube context.

        Args:
            name: Name of the vcluster to create
            values: Path to a values file, or a list of paths (optional)
            upgrade: If True, upgrade the cluster if it was created before (optional)
            namespace: Namespace to create the vcluster in (optional)
            set_values: Helm values to set inline, as key/value pairs (optional)
            chart_version: Pin the vcluster chart version, e.g. "0.36.0" (optional)
            chart_repo: Override the chart repository URL (optional)
            chart_name: Override the chart name (optional)
            expose: If True, create a load balancer service for the vcluster
            create_namespace: If False, do not create the namespace. Defaults to
                the CLI behaviour, which creates it.
            kube_config_context_name: Override the generated kube context name (optional)

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        value_files = self._normalize_values(values)

        if set_values:
            self._validate_set_values(set_values)

        for flag_value, field in (
            (chart_version, "chart_version"),
            (chart_repo, "chart_repo"),
            (chart_name, "chart_name"),
            (kube_config_context_name, "kube_config_context_name"),
        ):
            if flag_value:
                self._validate_flag_value(flag_value, field)

        cmd = ["vcluster", "create", name, "--connect=false"]

        if namespace:
            cmd.extend(["-n", namespace])

        for value_file in value_files:
            cmd.extend(["--values", value_file])

        if set_values:
            for key, value in sorted(set_values.items()):
                cmd.extend(["--set", f"{key}={value}"])

        if chart_version:
            cmd.extend(["--chart-version", chart_version])

        if chart_repo:
            cmd.extend(["--chart-repo", chart_repo])

        if chart_name:
            cmd.extend(["--chart-name", chart_name])

        if kube_config_context_name:
            cmd.extend(["--kube-config-context-name", kube_config_context_name])

        if expose:
            cmd.append("--expose")

        if create_namespace is False:
            cmd.append("--create-namespace=false")

        if upgrade:
            cmd.append("--upgrade")

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster create failed: {result.output}")

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    def call(
        self, name: str, command: str, namespace: Optional[str] = None
    ) -> Result[CommandResult]:
        """Connect to a vcluster and execute a command inside it.

        Connects to the specified vcluster and runs the given command
        within the virtual cluster context. The connection is established
        using ``vcluster connect`` with the ``-s`` (server-side) flag,
        and the command is passed after the ``--`` separator.

        Command: vcluster connect <name> -n <namespace> -s -- <command>

        Args:
            name: Name of the vcluster to connect to.
            command: The command string to execute inside the vcluster.
                Supports quoted arguments (e.g. ``"kubectl get pods -n default"``).
            namespace: Namespace where the vcluster resides. If not
                provided, defaults to ``vcluster-<name>``.

        Returns:
            Result containing a ``CommandResult`` with the exit code and
            output on success, or an error message on failure.

        Raises:
            ValidationError: If the name, namespace, or command is invalid.

        Examples:
            >>> manager = VClusterManager()
            >>> result = manager.call("my-cluster", "kubectl get pods")
            >>> if result.is_ok:
            ...     print(result.value.output)
        """
        # Validate inputs
        self._validate_name(name, "name")

        if namespace is not None:
            self._validate_name(namespace, "namespace")

        if not command or not command.strip():
            raise ValidationError("command", "cannot be empty")

        if namespace is None:
            namespace = f"vcluster-{name}"

        try:
            command_parts = shlex.split(command)
        except ValueError as e:
            raise ValidationError("command", f"invalid command syntax: {e}")

        cmd = [
            "vcluster", "connect", name, "-n", namespace, "-s", "--"
        ] + command_parts

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(
                    f"vcluster call failed: {result.output}"
                )

            return Result.ok(result)

        except VClusterCLIError as e:
            return Result.err(str(e))

    def disconnect(self) -> Result[CommandResult]:
        """Disconnect from a vcluster.

        Command: vcluster disconnect -s

        Returns:
            Result containing CommandResult on success, or error message on failure
        """
        cmd = ["vcluster", "disconnect", "-s"]

        try:
            result = self._run_command(cmd)

            if result.exit_code != 0:
                return Result.err(f"vcluster disconnect failed: {result.output}")

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
