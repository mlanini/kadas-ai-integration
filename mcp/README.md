# MCP Integrations

This directory contains Model Context Protocol servers for KADAS geospatial workflows.

## Available servers

- `map-server`
- `geodata-server`
- `analysis-server`
- `sketching-server`
- `geolocation-server`
- `geoai-server`

## Server summary

### map-server

- `fly_to`
- `get_extent`
- `set_crs`
- `list_layers`
- `toggle_layer`
- `add_wms_layer`

### geodata-server

- `search_stac_catalog`
- `get_stac_item`
- `download_stac_asset`
- `discover_wms`
- `discover_wfs`

### analysis-server

- `compute_slope`
- `compute_hillshade`
- `compute_viewshed`
- `line_of_sight`

### sketching-server

- `add_pin`
- `add_polygon`
- `add_text`
- `clear_sketches`

### geolocation-server

- `geocode`
- `reverse_geocode`
- `search_poi`
- `compute_route`

### geoai-server

- `segment_objects`
- `detect_features`
- `detect_changes`
- `download_imagery`

## Shared Runtime

`kadas-mcp-core` hosts shared server/runtime utilities used by all MCP servers.

## Transport

The current reference implementation uses stdio and a minimal JSON-RPC/MCP-compatible interaction model suitable for local clients and iterative development.
