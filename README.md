# KADAS AI Integrations

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mlanini/kadas-ai-integration)

A collection of reference integrations and experiments connecting the KADAS Albireo application framework with AI systems, including MCP tools, LLM workflows, retrieval pipelines, and geospatial agent capabilities.

Built around modular MCP servers, this repository is intended as a reference framework for KADAS plugin developers who want to build geospatially aware AI applications with explicit map context, catalog access, terrain analysis, routing, and AI-assisted raster workflows.

## Goals

- Expose KADAS-friendly geospatial capabilities through MCP tools.
- Provide reusable reference patterns for plugin authors.
- Make AI interactions geospatially grounded through CRS, extent, and dataset context.
- Keep the architecture modular so servers can be reused independently.

## Implemented Components

### MCP core

- Shared JSON-RPC/MCP runtime
- Tool registry and validation helpers
- Minimal stdio transport for local MCP clients

### MCP servers

- `map-server`: map navigation, layer listing, layer visibility, WMS registration
- `geodata-server`: STAC discovery, STAC item inspection, asset download, WMS/WFS discovery
- `analysis-server`: slope, hillshade, viewshed, line-of-sight primitives
- `sketching-server`: pins, polygons, text annotations, sketch reset
- `geolocation-server`: geocoding, reverse geocoding, POI search, route lookup
- `geoai-server`: imagery download, segmentation placeholder workflow, feature detection placeholder workflow, change detection placeholder workflow

## Repository Structure

- `mcp/`: Model Context Protocol servers and shared runtime utilities.
- `compute/`: Rust modules for compute-intensive geospatial workloads.
- `skills/`: Agent Skills for geospatial-aware AI assistants.
- `tests/`: smoke tests for MCP runtime and server registration.
- `examples/`: local client configuration examples.

## Quick Start

### 1. Use the KADAS Albireo Python runtime

This repository is configured to run MCP servers with:

- `<path_to_KadasAlbireo>\bin\python.exe` (should be adapted depending on the operating system being used)

### 2. VS Code MCP configuration

The workspace MCP client configuration is already defined in [.vscode/mcp.json](.vscode/mcp.json).

### 3. Local smoke test

Example with the KADAS Python runtime:

- compile/import all server modules
- instantiate each MCP server and verify tool registration

### 4. Claude Desktop configuration

See [examples/claude_desktop_config.json](examples/claude_desktop_config.json) for a starting point.

## Guides

- [Quick configuration guide for beginners](docs/quick-configuration-guide.md)
- [Quick starter guide for your first KADAS AI plugins](docs/quickstarter_plugin-kadas-ai.md)

## Architecture

### Python runtime

All MCP servers are implemented in Python and share `kadas-mcp-core`.

### Rust runtime

The crate in [compute/Cargo.toml](compute/Cargo.toml) contains compute-oriented functions intended for future integration from Python via PyO3, including:

- vector similarity helpers
- bbox and distance computations
- pairwise distance matrix support

### Agent skill

The skill in [skills/kadas-geospatial/SKILL.md](skills/kadas-geospatial/SKILL.md) documents orchestration rules, workflow playbooks, and output contracts for geospatial AI tasks.

## Current Limitations

- MCP server implementations currently focus on local reference behavior and API shape.
- `analysis-server` and `geoai-server` use simplified placeholder computations instead of full KADAS/QGIS processing pipelines.
- Rust validation could not be executed in this workspace because `cargo` is not installed.

## Next Integration Targets

- Direct KADAS/QGIS layer manipulation via PyQGIS APIs
- STAC asset-to-layer ingestion helpers
- Native raster/vector compute offloading into Rust where beneficial
- richer test coverage and server-specific schemas

## License

GPL-2.0
