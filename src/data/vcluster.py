from dataclasses import dataclass
from typing import Optional


@dataclass
class VClusterInfo:
    """Dataclass for holding vcluster information"""
    name: str
    namespace: str
    status: str
    replicas: str
    age: str
    created: str
