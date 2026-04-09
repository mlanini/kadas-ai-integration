from __future__ import annotations

import sys
from pathlib import Path


def _ensure_core_on_path() -> None:
    current = Path(__file__).resolve()
    core_src = current.parents[4] / "kadas-mcp-core" / "src"
    core_src_str = str(core_src)
    if core_src_str not in sys.path:
        sys.path.insert(0, core_src_str)


_ensure_core_on_path()

from geoai_server.state import GeoAIState
from geoai_server.tools import build_tools
from kadas_mcp_core import BaseMCPServer


class GeoAIMCPServer(BaseMCPServer):
    def __init__(self) -> None:
        super().__init__(name="kadas-geoai-server")
        state = GeoAIState()
        for tool in build_tools(state):
            self.register_tool(tool)


def main() -> None:
    server = GeoAIMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
