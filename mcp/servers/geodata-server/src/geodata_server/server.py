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

from geodata_server.tools import build_tools
from kadas_mcp_core import BaseMCPServer


class GeodataMCPServer(BaseMCPServer):
    def __init__(self) -> None:
        super().__init__(name="kadas-geodata-server")
        for tool in build_tools():
            self.register_tool(tool)


def main() -> None:
    server = GeodataMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
