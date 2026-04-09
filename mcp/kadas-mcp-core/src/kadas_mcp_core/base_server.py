from __future__ import annotations

import json
import sys
from typing import Any

from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.registry import ToolRegistry
from kadas_mcp_core.types import ToolSpec


class BaseMCPServer:
    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name = name
        self.version = version
        self.registry = ToolRegistry()

    def register_tool(self, tool: ToolSpec) -> None:
        self.registry.register(tool)

    def run_stdio(self) -> None:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self._handle_request(request)
            except json.JSONDecodeError:
                response = self._error_response(None, -32700, "Parse error")
            except MCPError as exc:
                response = self._error_response(None, exc.code, exc.message)
            except Exception as exc:
                response = self._error_response(None, -32000, str(exc))

            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        if not method:
            raise MCPError("Missing method", code=-32600)

        if method == "initialize":
            return self._success_response(
                request_id,
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.name, "version": self.version},
                },
            )

        if method in ("notifications/initialized", "initialized"):
            return None

        if method == "tools/list":
            return self._success_response(request_id, {"tools": self.registry.list_tools()})

        if method == "tools/call":
            tool_name = params.get("name")
            if not isinstance(tool_name, str):
                raise MCPError("tools/call requires string 'name'", code=-32602)
            arguments = params.get("arguments")
            if arguments is not None and not isinstance(arguments, dict):
                raise MCPError("tools/call 'arguments' must be an object", code=-32602)
            result = self.registry.call_tool(tool_name, arguments)
            return self._success_response(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                    "isError": False,
                },
            )

        raise MCPError(f"Method not found: {method}", code=-32601)

    @staticmethod
    def _success_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
