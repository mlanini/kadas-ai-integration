"""Shared MCP runtime for KADAS servers."""

from kadas_mcp_core.base_server import BaseMCPServer
from kadas_mcp_core.types import ToolSpec

__all__ = ["BaseMCPServer", "ToolSpec", "__version__"]
__version__ = "0.1.0"
