# This package contains MCP prompts
# Prompts are loaded directly by server.py using dynamic imports
from prompt.prompts import (
    vcluster_management_assistant,
    vcluster_lifecycle_assistant,
    vcluster_access_assistant,
    vcluster_certificates_assistant,
    namespace_metadata_assistant,
    vcluster_troubleshooting_assistant,
)


__all__ = [
    "vcluster_management_assistant",
    "vcluster_lifecycle_assistant",
    "vcluster_access_assistant",
    "vcluster_certificates_assistant",
    "namespace_metadata_assistant",
    "vcluster_troubleshooting_assistant",
]
