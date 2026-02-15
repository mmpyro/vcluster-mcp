from threading import Lock
from mcp.server.fastmcp import FastMCP


class Server:
    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not Server._initialized:
            with Server._lock:
                if not Server._initialized:
                    self._mcp = FastMCP("VCluster service")
                    Server._initialized = True

    @property
    def mcp(self) -> FastMCP:
        """Access the underlying FastMCP instance."""
        return self._mcp

    # Convenience methods to access FastMCP functionality directly
    def __getattr__(self, name):
        """Delegate attribute access to the FastMCP instance."""
        return getattr(self._mcp, name)
