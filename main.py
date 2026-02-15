#!/usr/bin/env python3
"""
vCluster Manager - A tool to manage vclusters in Kubernetes
"""
import argparse
from typing import List, Dict
from kubernetes import config
from tabulate import tabulate
from src.utils.vcluster_manager import VClusterManager

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
        print("✓ Successfully connected to Kubernetes cluster")
    except Exception as e:
        import sys
        print(f"✗ Error connecting to Kubernetes cluster: {e}")
        sys.exit(1)

def display_vclusters(vclusters: List[VClusterInfo]):
    """Display vclusters in a formatted table using tabulate"""
    if not vclusters:
        print("\nNo vclusters found in the cluster.")
        return

    print(f"\nFound {len(vclusters)} vcluster(s):\n")

    # Prepare data for tabulate
    table_data = [
        [vc.name, vc.namespace, vc.status, vc.replicas, vc.age]
        for vc in vclusters
    ]
    headers = ["NAME", "NAMESPACE", "STATUS", "REPLICAS", "AGE"]

    print(tabulate(table_data, headers=headers, tablefmt="plain"))
    print()

def display_annotations(namespace: str, annotations: Dict[str, str]):
    """Display annotations for a namespace"""
    if not annotations:
        print(f"\nNo annotations found for namespace '{namespace}'.")
        return

    print(f"\nAnnotations for namespace '{namespace}':\n")
    table_data = [[k, v] for k, v in annotations.items()]
    headers = ["KEY", "VALUE"]
    print(tabulate(table_data, headers=headers, tablefmt="plain"))
    print()

def display_labels(namespace: str, labels: Dict[str, str]):
    """Display labels for a namespace"""
    if not labels:
        print(f"\nNo labels found for namespace '{namespace}'.")
        return

    print(f"\nLabels for namespace '{namespace}':\n")
    table_data = [[k, v] for k, v in labels.items()]
    headers = ["KEY", "VALUE"]
    print(tabulate(table_data, headers=headers, tablefmt="plain"))
    print()

def main():
    """Main entry point for the vCluster Manager CLI"""
    parser = argparse.ArgumentParser(
        description='vCluster Manager - Manage vclusters in Kubernetes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all vclusters in all namespaces
  python vcluster_manager.py list
  
  # List vclusters in a specific namespace
  python vcluster_manager.py list --namespace vcluster-team-a
  
  # Use a specific kubeconfig file
  python vcluster_manager.py list --kubeconfig /path/to/kubeconfig

  # Get annotations for a specific namespace
  python vcluster_manager.py get-annotations --namespace vcluster-team-a

  # Get labels for a specific namespace
  python vcluster_manager.py get-labels --namespace vcluster-team-a
        """
    )
    
    parser.add_argument(
        'command',
        choices=['list', 'get-annotations', 'get-labels'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '-n', '--namespace',
        help='Namespace to search for vclusters (default: all namespaces)',
        default=None
    )
    
    parser.add_argument(
        '-k', '--kubeconfig',
        help='Path to kubeconfig file (default: uses default kubeconfig)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Initialize Kubernetes configuration
    setup_kubernetes(kubeconfig_path=args.kubeconfig)
    
    # Initialize manager
    manager = VClusterManager()
    
    # Execute command
    if args.command == 'list':
        vclusters = manager.list_vclusters(namespace=args.namespace)
        display_vclusters(vclusters)
    elif args.command == 'get-annotations':
        if not args.namespace:
            import sys
            print("✗ Error: Namespace is required for get-annotations command")
            sys.exit(1)
        annotations = manager.get_namespace_annotations(args.namespace)
        display_annotations(args.namespace, annotations)
    elif args.command == 'get-labels':
        if not args.namespace:
            import sys
            print("✗ Error: Namespace is required for get-labels command")
            sys.exit(1)
        labels = manager.get_namespace_labels(args.namespace)
        display_labels(args.namespace, labels)


if __name__ == '__main__':
    main()
