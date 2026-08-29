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
def vcluster_certs_check(name: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> Union[Dict, List, str]:
    """Check the control-plane certificates of a vcluster.

    This function reports the current certificates and their expiry dates.
    Expired control-plane certificates typically surface as opaque connection
    failures, so this is worth checking when a vcluster is unreachable but
    otherwise appears healthy. The operation is read-only.

    Args:
        name: The name of the vcluster to check.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[Dict, List, str]: Certificate report on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.certs_check(name, namespace)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def vcluster_kubeconfig(
    name: str,
    namespace: Optional[str] = None,
    server: Optional[str] = None,
    insecure: bool = False,
    kubeconfig_path: Optional[str] = None,
) -> Union[Dict[str, str], str]:
    """Export a vcluster kubeconfig to a file without switching contexts.

    Use this when you need credentials to hand to another tool, for example
    ``kubectl --kubeconfig <path>`` or a Helm invocation. Unlike vcluster_call,
    it leaves the caller's current kube context untouched.

    The kubeconfig is written to a private (0600) temporary file and the path is
    returned rather than the contents, because the file holds client
    credentials. The caller owns that file and should delete it after use.

    Args:
        name: The name of the vcluster to export credentials for.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        server: Optional API server address to record in the kubeconfig. Set
            this when the vcluster is reached through an ingress or load
            balancer rather than a local port forward.
        insecure: If True, the generated kubeconfig skips TLS verification.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[Dict[str, str], str]: A dict with kubeconfig_path, context and
            server on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.kubeconfig(name, namespace, server=server, insecure=insecure)
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
def vcluster_delete(
    name: str,
    namespace: Optional[str] = None,
    delete_namespace: bool = False,
    keep_pvc: bool = False,
    ignore_not_found: bool = False,
    wait: bool = True,
    kubeconfig_path: Optional[str] = None,
) -> Union[CommandResult, Dict[str, str], str]:
    """Delete a vcluster.

    This action is irreversible - the cluster and all its resources will be
    permanently removed. By default the host namespace is preserved; the
    vcluster CLI still cleans up namespaces it created itself.

    Args:
        name: The name of the vcluster to delete.
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to the vcluster name.
        delete_namespace: If True, also delete the host namespace. DESTRUCTIVE -
            this removes every other workload in that namespace as well. Only
            set it when the namespace exists solely for this vcluster.
        keep_pvc: If True, retain the vcluster's persistent volume claim so the
            data survives the deletion.
        ignore_not_found: If True, succeed instead of erroring when the vcluster
            does not exist. Useful for idempotent cleanup.
        wait: If False, return immediately instead of waiting for the deletion
            to complete.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
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
        return {"error": str(e)}


@mcp.tool()
def vcluster_create(
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
    kubeconfig_path: Optional[str] = None,
) -> Union[CommandResult, Dict[str, str], str]:
    """Create a new vcluster.

    Creates a vcluster with the specified name. Configuration can come from
    values files, inline helm values, or both. The caller's kube context is
    never switched by this operation.

    Args:
        name: The name for the new vcluster.
        values: Optional path to a values file, or a list of paths. Later files
            override earlier ones.
        upgrade: Optional flag to upgrade the cluster if it was created before.
        namespace: Optional namespace to create the vcluster in. If not
            provided, the vcluster CLI picks the default.
        set_values: Optional inline helm values, e.g.
            {"sync.toHost.ingresses.enabled": "true"}. Avoids writing a
            temporary values file for a single setting.
        chart_version: Optional vcluster chart version to pin, e.g. "0.36.0".
        chart_repo: Optional chart repository URL override.
        chart_name: Optional chart name override.
        expose: If True, create a load balancer service to expose the vcluster
            endpoint outside the host cluster.
        create_namespace: If False, do not create the namespace. Defaults to the
            CLI behaviour, which creates it when missing.
        kube_config_context_name: Optional override for the generated kube
            context name.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
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
        return {"error": str(e)}


@mcp.tool()
def vcluster_call(name: str, command: str, namespace: Optional[str] = None, kubeconfig_path: Optional[str] = None) -> Union[CommandResult, Dict[str, str], str]:
    """Execute a command inside a vcluster.

    This function connects to a running vcluster and executes the given
    command within the virtual cluster context. It uses ``vcluster connect``
    with the server-side flag to establish the connection and run the command.

    Args:
        name: The name of the vcluster to connect to and execute the command in.
        command: The command string to execute inside the vcluster.
            Supports standard shell quoting (e.g. ``"kubectl get pods -n default"``).
        namespace: Optional namespace where the vcluster is located.
            If not provided, defaults to ``vcluster-<name>``.
        kubeconfig_path: Optional path to a kubeconfig file. If not provided,
            the default kubeconfig from the environment will be used.

    Returns:
        Union[CommandResult, Dict[str, str], str]: CommandResult with exit code
            and output on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()

    try:
        result = manager.call(name, command, namespace)
        return _handle_result(result)
    except ValidationError as e:
        return {"error": str(e)}


@mcp.tool()
def vcluster_disconnect(kubeconfig_path: Optional[str] = None) -> Union[CommandResult, Dict[str, str], str]:
    """Disconnect from a vcluster.

    Returns:
        Union[CommandResult, str]: CommandResult on success, or error object if failed.
    """
    setup_kubernetes(kubeconfig_path)
    manager = VClusterManager()
    result = manager.disconnect()
    return _handle_result(result)


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
