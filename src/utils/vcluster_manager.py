from kubernetes import client
from kubernetes.client.exceptions import ApiException
from typing import List, Dict, Any
from .datetime_utils import calculate_age
from ..data import VClusterInfo


class VClusterManager:
    """Manager class for vCluster operations"""

    def __init__(self):
        """
        Initialize the VCluster Manager
        """
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def list_vclusters(self, namespace: str = None) -> List[VClusterInfo]:
        """
        List all vclusters in the cluster or specific namespace

        Args:
            namespace: Specific namespace to search. If None, searches all namespaces

        Returns:
            List of VClusterInfo objects containing vcluster information
        """
        vclusters = []

        try:
            # vClusters are identified by StatefulSets with specific labels
            # Label selector for vcluster: app=vcluster
            label_selector = "app=vcluster"

            if namespace:
                statefulsets = self.apps_v1.list_namespaced_stateful_set(
                    namespace=namespace,
                    label_selector=label_selector
                )
            else:
                statefulsets = self.apps_v1.list_stateful_set_for_all_namespaces(
                    label_selector=label_selector
                )

            for sts in statefulsets.items:
                vcluster_info = self._extract_vcluster_info(sts)
                vclusters.append(vcluster_info)

            return vclusters

        except ApiException as e:
            print(f"✗ Error listing vclusters: {e}")
            return []

    def _extract_vcluster_info(self, statefulset) -> VClusterInfo:
        """
        Extract relevant information from a vcluster StatefulSet

        Args:
            statefulset: Kubernetes StatefulSet object

        Returns:
            VClusterInfo object with vcluster information
        """
        metadata = statefulset.metadata
        spec = statefulset.spec
        status = statefulset.status

        # Extract vcluster name from labels or statefulset name
        vcluster_name = metadata.labels.get('release', metadata.name)

        # Determine status
        replicas = spec.replicas or 0
        ready_replicas = status.ready_replicas or 0

        if replicas == 0:
            vcluster_status = 'Paused'
        elif ready_replicas == replicas:
            vcluster_status = 'Ready'
        else:
            vcluster_status = 'Not Ready'

        return VClusterInfo(
            name=vcluster_name,
            namespace=metadata.namespace,
            status=vcluster_status,
            replicas=f"{ready_replicas}/{replicas}",
            age=calculate_age(metadata.creation_timestamp),
            created=metadata.creation_timestamp.isoformat() if metadata.creation_timestamp else 'Unknown'
        )

    def get_namespace_annotations(self, namespace: str) -> Dict[str, str]:
        """
        Get annotations for a specific namespace

        Args:
            namespace: Name of the namespace

        Returns:
            Dictionary of annotations
        """
        try:
            ns = self.core_v1.read_namespace(name=namespace)
            return ns.metadata.annotations or {}
        except ApiException as e:
            print(f"✗ Error reading namespace {namespace}: {e}")
            return {}

    def get_namespace_labels(self, namespace: str) -> Dict[str, str]:
        """
        Get labels for a specific namespace

        Args:
            namespace: Name of the namespace

        Returns:
            Dictionary of labels
        """
        try:
            ns = self.core_v1.read_namespace(name=namespace)
            return ns.metadata.labels or {}
        except ApiException as e:
            print(f"✗ Error reading namespace {namespace}: {e}")
            return {}
