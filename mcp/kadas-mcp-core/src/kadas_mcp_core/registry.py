from __future__ import annotations

from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.types import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise MCPError(f"Tool already registered: {tool.name}", code=-32602)
        self._tools[tool.name] = tool

    def list_tools(self) -> list[dict[str, object]]:
        return [tool.as_mcp_tool() for tool in self._tools.values()]

    def call_tool(self, name: str, arguments: dict[str, object] | None) -> dict[str, object]:
        if name not in self._tools:
            raise MCPError(f"Unknown tool: {name}", code=-32601)
        tool = self._tools[name]
        payload = arguments or {}
        return tool.handler(payload)
