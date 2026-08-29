from threading import Lock
from mcp.server.mcpserver import MCPServer


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
                    self._mcp = MCPServer("VCluster service")
                    Server._initialized = True

    @property
    def mcp(self) -> MCPServer:
        """Access the underlying MCPServer instance."""
        return self._mcp

    # Convenience methods to access MCPServer functionality directly
    def __getattr__(self, name):
        """Delegate attribute access to the MCPServer instance."""
        return getattr(self._mcp, name)
