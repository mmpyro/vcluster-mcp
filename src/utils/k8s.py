from kubernetes import config


def setup_kubernetes(kubeconfig_path: str = None):
    """Initialize Kubernetes configuration"""
    try:
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            # Try in-cluster config first, then fall back to kubeconfig
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
    except config.ConfigException as e:
        raise RuntimeError(
            f"Failed to load Kubernetes configuration: {e}"
        ) from e
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Kubernetes configuration file not found: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error configuring Kubernetes: {e}"
        ) from e
