from typing import Optional, Dict, Union, Any, List, TypeVar
from utils.mcp import Server
from utils.k8s import setup_kubernetes
from utils.vcluster_manager import VClusterManager, CommandResult
from utils.result import Result
from utils.exceptions import ValidationError

mcp = Server().mcp

T = TypeVar('T')


def _handle_result(result: Result[T], success_message: str = "Operation successful") -> Union[T, Dict[str, str]]:
    """Handle a Result object and return appropriate value for MCP."""
    if result.is_ok:
        assert result.value is not None
        return result.value
    return {"error": result.error or "Unknown error"}


@mcp.tool()
def vcluster_list(kubeconfig_path: Optional[str] = None) -> Union[Dict, List, str]:
    """List all vclusters in the current Kubernetes context.

    This function retrieves all vclusters managed by the vcluster platform
    in the current Kubernetes context. It sets up the Kubernetes client
    internally and returns the list of vclusters as serialized JSON on success,
    or an error object if the command failed.

    Args:
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[Dict, List, str]: List of vclusters on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.list()
    return _handle_result(result)


@mcp.tool()
def vcluster_describe(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> Union[Dict, str]:
    """Describe a specific vcluster in detail.

    This function retrieves detailed information about a specific vcluster,
    including its status, resources, and configuration. The information is
    returned as serialized JSON on success, or an error object if the
    command failed.

    Args:
        name: The name of the vcluster to describe.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[Dict, str]: Detailed vcluster information on success,
            or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.describe(name, namespace)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def vcluster_pause(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> Union[CommandResult, Dict[str, str], str]:
    """Pause a running vcluster.

    This function pauses a running vcluster, which stops the virtual cluster
    without deleting it. This is useful for temporarily suspending workloads
    while preserving the cluster state.

    Args:
        name: The name of the vcluster to pause.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.pause(name, namespace)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def vcluster_resume(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> Union[CommandResult, Dict[str, str], str]:
    """Resume a paused vcluster.

    This function resumes a previously paused vcluster, restoring its
    operation and allowing workloads to run again.

    Args:
        name: The name of the vcluster to resume.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.resume(name, namespace)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def vcluster_delete(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> Union[CommandResult, Dict[str, str], str]:
    """Delete a vcluster.

    This function deletes a vcluster and optionally its namespace.
    This action is irreversible - the cluster and all its resources
    will be permanently removed.

    Args:
        name: The name of the vcluster to delete.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.delete(name, namespace)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def vcluster_create(name: str, values: Optional[str] = None, upgrade: Optional[bool] = None, kubeconfig_path: Optional[str] = None) -> Union[CommandResult, Dict[str, str], str]:
    """Create a new vcluster.

    This function creates a new vcluster with the specified name.
    Optionally, you can provide a values file to customize the vcluster
    configuration during creation. If the upgrade parameter is set to True,
    the cluster will be upgraded if it was created before.

    Args:
        name: The name for the new vcluster.
        values: Optional path to a values file for vcluster configuration.
        upgrade: Optional flag to upgrade the cluster if it was created before.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.create(name, values, upgrade)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def get_namespace_labels(namespace: str, kubeconfig_path: Optional[str] = None) -> Union[Dict[str, str], str]:
    """Get labels for a specific namespace.

    This function retrieves all labels associated with a Kubernetes namespace.
    Labels are key-value pairs that can be used to organize and select resources.

    Args:
        namespace: The name of the namespace to get labels from.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[Dict[str, str], str]: Dictionary of labels on success,
            or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.get_namespace_labels(namespace)
    return _handle_result(result)


@mcp.tool()
def set_namespace_label(namespace: str, key: str, value: str, kubeconfig_path: Optional[str] = None) -> Union[bool, Dict[str, str], str]:
    """Create or update a label on a namespace.

    This function creates a new label or updates an existing label on a
    Kubernetes namespace. Labels are key-value pairs used for organizing
    and selecting resources.

    Args:
        namespace: The name of the namespace to label.
        key: The label key to set.
        value: The label value to assign.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[bool, str]: True on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.set_namespace_label(namespace, key, value)
    return _handle_result(result)


@mcp.tool()
def delete_namespace_label(namespace: str, key: str, kubeconfig_path: Optional[str] = None) -> Union[bool, Dict[str, str], str]:
    """Delete a label from a namespace.

    This function removes a label from a Kubernetes namespace.
    If the label doesn't exist, the operation is considered successful.

    Args:
        namespace: The name of the namespace to remove the label from.
        key: The label key to delete.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[bool, str]: True on success (or if label didn't exist),
            or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.delete_namespace_label(namespace, key)
    return _handle_result(result)


@mcp.tool()
def get_namespace_annotations(namespace: str, kubeconfig_path: Optional[str] = None) -> Union[Dict[str, str], str]:
    """Get annotations for a specific namespace.

    This function retrieves all annotations associated with a Kubernetes namespace.
    Annotations are similar to labels but are typically used for storing non-identifying
    metadata.

    Args:
        namespace: The name of the namespace to get annotations from.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[Dict[str, str], str]: Dictionary of annotations on success,
            or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.get_namespace_annotations(namespace)
    return _handle_result(result)


@mcp.tool()
def set_namespace_annotation(namespace: str, key: str, value: str, kubeconfig_path: Optional[str] = None) -> Union[bool, Dict[str, str], str]:
    """Create or update an annotation on a namespace.

    This function creates a new annotation or updates an existing annotation on a
    Kubernetes namespace. Annotations are key-value pairs used for storing
    non-identifying metadata such as descriptions, links, or configuration data.

    Args:
        namespace: The name of the namespace to annotate.
        key: The annotation key to set.
        value: The annotation value to assign.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[bool, str]: True on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.set_namespace_annotation(namespace, key, value)
    return _handle_result(result)


@mcp.tool()
def delete_namespace_annotation(namespace: str, key: str, kubeconfig_path: Optional[str] = None) -> Union[bool, Dict[str, str], str]:
    """Delete an annotation from a namespace.

    This function removes an annotation from a Kubernetes namespace.
    If the annotation doesn't exist, the operation is considered successful.

    Args:
        namespace: The name of the namespace to remove the annotation from.
        key: The annotation key to delete.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[bool, str]: True on success (or if annotation didn't exist),
            or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.delete_namespace_annotation(namespace, key)
    return _handle_result(result)
