"""MCP resources exposing read-only views of the vcluster environment.

Resources differ from tools in two ways that matter here: they are addressed by
URI rather than called with arguments, and they are read-only. Everything in
this module is therefore a pure query - nothing creates, mutates or deletes.

Resource URIs cannot carry a kubeconfig path, so these always use the default
kubeconfig from the environment. Use the equivalent tool when you need to point
at a specific kubeconfig.
"""

import json
from typing import Any, Dict

from utils.mcp import Server
from utils.k8s import setup_kubernetes
from utils.vcluster_manager import VClusterManager
from utils.result import Result
from utils.exceptions import ValidationError

mcp = Server().mcp


def _serialize(result: Result[Any]) -> str:
    """Render a Result as a JSON document for a resource response.

    Errors are returned in band as ``{"error": ...}`` rather than raised, so a
    client reading the resource always gets a well-formed JSON body.

    Args:
        result: The Result to render

    Returns:
        A JSON string
    """
    if result.is_ok:
        return json.dumps(result.value, separators=(",", ":"), default=str)

    return json.dumps({"error": result.error or "Unknown error"}, separators=(",", ":"))


def _error(message: str) -> str:
    """Render an error as a JSON document.

    Args:
        message: The error message

    Returns:
        A JSON string
    """
    return json.dumps({"error": message}, separators=(",", ":"))


@mcp.resource("vcluster://{namespace}/{name}/certs", mime_type="application/json")
def cluster_certs_resource(namespace: str, name: str) -> str:
    """Control-plane certificate report for a single vcluster.

    Expired certificates surface as opaque connection failures, so this is
    worth reading when a vcluster looks healthy but is unreachable.

    Args:
        namespace: Namespace where the vcluster lives.
        name: Name of the vcluster.

    Returns:
        JSON certificate report, or a JSON error object.
    """
    setup_kubernetes(None)
    manager = VClusterManager()

    try:
        return _serialize(manager.certs_check(name, namespace))
    except ValidationError as e:
        return _error(str(e))


@mcp.resource("vcluster://{namespace}/metadata", mime_type="application/json")
def namespace_metadata_resource(namespace: str) -> str:
    """Labels and annotations on a vcluster's host namespace.

    Args:
        namespace: The namespace to read metadata from.

    Returns:
        JSON object with ``labels`` and ``annotations``, or a JSON error object.
    """
    setup_kubernetes(None)
    manager = VClusterManager()

    labels = manager.get_namespace_labels(namespace)

    if labels.is_err:
        return _error(labels.error or "Unknown error")

    annotations = manager.get_namespace_annotations(namespace)

    if annotations.is_err:
        return _error(annotations.error or "Unknown error")

    payload: Dict[str, Any] = {
        "namespace": namespace,
        "labels": labels.value,
        "annotations": annotations.value,
    }
    return json.dumps(payload, separators=(",", ":"), default=str)
