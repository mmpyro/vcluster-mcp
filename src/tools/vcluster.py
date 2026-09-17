"""MCP tools wrapping the vcluster CLI and namespace metadata operations.

Responses are emitted as compact JSON strings rather than structured objects.
Every tool is registered with ``structured_output=False`` so the SDK sends the
payload once as text instead of twice (unstructured ``content`` plus
``structured_content``), and a ``str`` return bypasses the SDK's ``indent=2``
pretty-printing in ``_convert_to_content``. See ``_emit``.
"""

import json
from typing import Annotated, Any, Dict, List, Literal, Optional, TypeVar

from pydantic import Field

from utils.mcp import Server
from utils.k8s import setup_kubernetes
from utils.vcluster_manager import VClusterManager, CommandResult
from utils.result import Result
from utils.exceptions import ValidationError

mcp = Server().mcp

T = TypeVar('T')

# Hard ceiling on any single tool response. `vcluster call` can run an arbitrary
# command inside the vcluster (`kubectl get pods -A -o yaml`), so without this a
# single call can exhaust the client's context.
MAX_RESPONSE_CHARS = 20_000

# Keys dropped from `vcluster list --output json` unless `full=True`. Verified
# against vcluster 0.36.0, whose entries are Created/Name/Namespace/Version/
# Status/AgeSeconds/Connected - `Created` and `AgeSeconds` are the same fact
# twice, and the relative one is what you sort staleness by.
#
# A denylist, not an allowlist, on purpose: this is a shape we do not control,
# and a field added by a future CLI release should reach the model rather than
# be silently hidden.
LIST_DROP_KEYS = ("created",)


def _emit(value: Any) -> str:
    """Serialize a tool result as a compact, size-capped JSON string.

    Args:
        value: Any JSON-serializable value, or a str to pass through as-is.

    Returns:
        Compact JSON, truncated with an explicit marker past MAX_RESPONSE_CHARS.
    """
    if isinstance(value, CommandResult):
        value = {"exit_code": value.exit_code, "output": value.output}

    text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"), default=str)

    if len(text) > MAX_RESPONSE_CHARS:
        dropped = len(text) - MAX_RESPONSE_CHARS
        return text[:MAX_RESPONSE_CHARS] + f"\n[truncated: {dropped} more chars]"

    return text


def _handle_result(result: Result[T]) -> str:
    """Render a Result as the tool's response string."""
    if result.is_ok:
        return _emit(result.value)
    return _emit({"error": result.error or "Unknown error"})


def _error(message: str) -> str:
    """Render an error as the tool's response string."""
    return _emit({"error": message})


def _project(entries: Any, drop: tuple) -> Any:
    """Drop `drop` keys from each list entry, leaving anything else untouched."""
    if not isinstance(entries, list):
        return entries

    return [
        {k: v for k, v in entry.items() if k.lower() not in drop} if isinstance(entry, dict) else entry
        for entry in entries
    ]


@mcp.tool(structured_output=False)
def vcluster_list(
    full: Annotated[bool, Field(description="Also return the absolute Created timestamp, which AgeSeconds otherwise covers.")] = False,
    kubeconfig_path: Optional[str] = None,
) -> str:
    """List all vclusters in the current Kubernetes context."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.list()

    if result.is_ok and not full:
        return _emit(_project(result.value, LIST_DROP_KEYS))

    return _handle_result(result)


@mcp.tool(structured_output=False)
def vcluster_describe(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> str:
    """Status, resources and configuration of one vcluster. Namespace defaults to vcluster-<name>."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        return _handle_result(manager.describe(name, namespace))
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_certs_check(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> str:
    """Report control-plane certificates and expiry for a vcluster.

    Read-only. Worth checking when a vcluster looks healthy but is unreachable,
    since expired certs surface as opaque connection failures.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        return _handle_result(manager.certs_check(name, namespace))
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_kubeconfig(
    name: str,
    namespace: Optional[str] = None,
    server: Annotated[Optional[str], Field(
        description="API server address to record, when the vcluster is reached via ingress or a load balancer rather than a port forward."
    )] = None,
    insecure: bool = False,
    kubeconfig_path: Optional[str] = None,
) -> str:
    """Export a vcluster kubeconfig without switching the caller's context.

    Returns the path to a private (0600) temp file, not the contents, because it
    holds client credentials. Pass the path to other tools; delete it after use.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        return _handle_result(manager.kubeconfig(name, namespace, server=server, insecure=insecure))
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_pause(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> str:
    """Pause a running vcluster, stopping its workloads without deleting state."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        return _handle_result(manager.pause(name, namespace))
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_resume(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> str:
    """Resume a paused vcluster."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        return _handle_result(manager.resume(name, namespace))
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_delete(
    name: str,
    namespace: Optional[str] = None,
    delete_namespace: Annotated[bool, Field(
        description="DESTRUCTIVE: also delete the host namespace, removing every other workload in it. Only for a namespace that exists solely for this vcluster."
    )] = False,
    keep_pvc: Annotated[bool, Field(description="Retain the persistent volume claim so data survives the deletion.")] = False,
    ignore_not_found: bool = False,
    wait: bool = True,
    kubeconfig_path: Optional[str] = None,
) -> str:
    """Delete a vcluster. Irreversible. The host namespace is preserved by default."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.delete(
            name,
            namespace,
            delete_namespace=delete_namespace,
            keep_pvc=keep_pvc,
            ignore_not_found=ignore_not_found,
            wait=wait,
        )
        return _handle_result(result)
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_create(
    name: str,
    values: Annotated[Optional[List[str]], Field(description="Values file paths; later files override earlier ones.")] = None,
    upgrade: Optional[bool] = None,
    namespace: Optional[str] = None,
    set_values: Annotated[Optional[Dict[str, str]], Field(description='Inline helm values as dotted keys, e.g. {"sync.toHost.ingresses.enabled": "true"}.')] = None,
    chart_version: Optional[str] = None,
    chart_repo: Optional[str] = None,
    chart_name: Optional[str] = None,
    expose: Annotated[bool, Field(description="Create a load balancer service exposing the vcluster outside the host cluster.")] = False,
    create_namespace: Optional[bool] = None,
    kube_config_context_name: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
) -> str:
    """Create a vcluster. Never switches the caller's kube context."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.create(
            name,
            values=values,
            upgrade=upgrade,
            namespace=namespace,
            set_values=set_values,
            chart_version=chart_version,
            chart_repo=chart_repo,
            chart_name=chart_name,
            expose=expose,
            create_namespace=create_namespace,
            kube_config_context_name=kube_config_context_name,
        )
        return _handle_result(result)
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_call(
    name: str,
    command: Annotated[str, Field(description='Command to run inside the vcluster, standard shell quoting, e.g. "kubectl get pods -n default".')],
    namespace: Optional[str] = None,
    kubeconfig_path: Optional[str] = None,
) -> str:
    """Run a command inside a vcluster via `vcluster connect`.

    Output is capped; prefer narrow queries over `-o yaml` across all namespaces.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        return _handle_result(manager.call(name, command, namespace))
    except ValidationError as e:
        return _error(str(e))


@mcp.tool(structured_output=False)
def vcluster_disconnect(kubeconfig_path: Optional[str] = None) -> str:
    """Disconnect from the currently connected vcluster."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    return _handle_result(manager.disconnect())


@mcp.tool(structured_output=False)
def namespace_metadata_get(
    namespace: str,
    kind: Literal["labels", "annotations", "both"] = "both",
    kubeconfig_path: Optional[str] = None,
) -> str:
    """Read labels and/or annotations on a namespace."""
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    payload: Dict[str, Any] = {}

    if kind in ("labels", "both"):
        result = manager.get_namespace_labels(namespace)

        if result.is_err:
            return _error(result.error or "Unknown error")

        payload["labels"] = result.value

    if kind in ("annotations", "both"):
        result = manager.get_namespace_annotations(namespace)

        if result.is_err:
            return _error(result.error or "Unknown error")

        payload["annotations"] = result.value

    return _emit(payload)


@mcp.tool(structured_output=False)
def namespace_metadata_set(
    namespace: str,
    kind: Literal["labels", "annotations"],
    key: str,
    value: Annotated[Optional[str], Field(description="The value to set. Omit or pass null to delete the key instead.")] = None,
    kubeconfig_path: Optional[str] = None,
) -> str:
    """Set or delete one label or annotation on a namespace.

    Deleting a key that does not exist succeeds.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    if kind == "labels":
        result = manager.delete_namespace_label(namespace, key) if value is None \
            else manager.set_namespace_label(namespace, key, value)
    else:
        result = manager.delete_namespace_annotation(namespace, key) if value is None \
            else manager.set_namespace_annotation(namespace, key, value)

    return _handle_result(result)
