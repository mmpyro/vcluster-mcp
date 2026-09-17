# This package contains MCP resources
# Resources are read-only, URI-addressed views of the vcluster environment
from resources.vcluster import (
    cluster_certs_resource,
    namespace_metadata_resource,
)


__all__ = [
    "cluster_certs_resource",
    "namespace_metadata_resource",
]
