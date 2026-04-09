---
name: kadas-geospatial
description: Domain skill for geospatial reasoning with KADAS Albireo, STAC catalogs, and MCP-based tool orchestration.
---

# KADAS Geospatial Skill

## Scope

Use this skill when the task involves:

- Geospatial data reasoning (layers, CRS, extents, geometries)
- STAC discovery and asset selection
- KADAS map interactions through MCP tools
- Terrain and visibility analysis workflows

Use MCP servers in this order when possible:

1. `kadas-map` to establish map context
2. `kadas-geodata` to discover/select datasets
3. `kadas-analysis` and `kadas-geoai` for analytics
4. `kadas-sketching` to annotate and communicate outcomes
5. `kadas-geolocation` to add search/routing context

## Core Rules

- Always confirm CRS and extent before spatial operations.
- Prefer explicit spatial filters (bbox/time/collection) for STAC queries.
- Return outputs with geospatial metadata (CRS, bounds, units, timestamp).
- Keep map actions reversible and traceable.

## Server Capabilities

### kadas-map

- `fly_to`: recenter map quickly before inspection.
- `get_extent`: use before geodata queries to avoid unbounded searches.
- `set_crs`: align spatial operations to a known CRS.
- `list_layers`, `toggle_layer`, `add_wms_layer`: maintain visual context.

### kadas-geodata

- `search_stac_catalog`: primary entrypoint for STAC item discovery.
- `get_stac_item`: inspect metadata and available assets.
- `download_stac_asset`: materialize selected assets locally.
- `discover_wms`, `discover_wfs`: discover OGC services when STAC is unavailable.

### kadas-analysis

- `compute_slope`, `compute_hillshade` for terrain descriptors.
- `compute_viewshed`, `line_of_sight` for visibility reasoning.

### kadas-sketching

- `add_pin`, `add_polygon`, `add_text` to annotate findings.
- `clear_sketches` to reset workspace before new analysis.

### kadas-geolocation

- `geocode`, `reverse_geocode` for location resolution.
- `search_poi` to contextualize local infrastructure.
- `compute_route` for route-based scenarios.

### kadas-geoai

- `segment_objects` for prompt-based segmentation workflows.
- `detect_features` for object/category detection.
- `detect_changes` for temporal comparison.
- `download_imagery` to ingest remote imagery.

## Workflow Playbooks

### STAC-driven analysis

1. Read map context with `get_extent`.
2. Query `search_stac_catalog` with bbox/time/collection constraints.
3. Inspect candidate with `get_stac_item`.
4. Download asset with `download_stac_asset`.
5. Run `compute_slope`/`compute_hillshade` or `segment_objects` as needed.

### Rapid site assessment

1. `geocode` target area.
2. `fly_to` and confirm view with `get_extent`.
3. Add basemap/overlay with `add_wms_layer`.
4. Run `compute_viewshed` or `line_of_sight`.
5. Annotate key outputs with `add_pin` and `add_text`.

### Change detection scenario

1. Acquire snapshots with `download_imagery` or STAC asset downloads.
2. Validate temporal ordering and spatial overlap.
3. Run `detect_changes` and report change ratio.
4. Mark impact areas with `add_polygon`.

## Output Contract

When summarizing results, always include:

- `crs`
- `extent` or point coordinates
- `data source` and acquisition time where available
- `tool chain` used (ordered list)
- `confidence/limitations` with assumptions

## Safety and Reliability

- Never perform broad remote searches without bbox/time constraints unless explicitly requested.
- If remote services fail, return fallback metrics and state reduced confidence.
- Validate file paths and required parameters before long operations.
