from __future__ import annotations

from uuid import uuid4

from kadas_mcp_core import ToolSpec
from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.validation import as_float, require_keys, validate_bbox, validate_epsg
from map_server.state import Layer, MapState


def build_tools(state: MapState) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="fly_to",
            description="Center map around lon/lat with an optional zoom factor.",
            input_schema={
                "type": "object",
                "properties": {
                    "lon": {"type": "number"},
                    "lat": {"type": "number"},
                    "zoom": {"type": "number", "minimum": 1, "maximum": 20},
                },
                "required": ["lon", "lat"],
            },
            handler=lambda args: fly_to(state, args),
        ),
        ToolSpec(
            name="get_extent",
            description="Return current map extent and CRS.",
            input_schema={"type": "object", "properties": {}},
            handler=lambda _args: get_extent(state),
        ),
        ToolSpec(
            name="set_crs",
            description="Set current map CRS (e.g. EPSG:4326).",
            input_schema={
                "type": "object",
                "properties": {"crs": {"type": "string"}},
                "required": ["crs"],
            },
            handler=lambda args: set_crs(state, args),
        ),
        ToolSpec(
            name="list_layers",
            description="List current map layers.",
            input_schema={"type": "object", "properties": {}},
            handler=lambda _args: list_layers(state),
        ),
        ToolSpec(
            name="toggle_layer",
            description="Toggle visibility of an existing layer.",
            input_schema={
                "type": "object",
                "properties": {
                    "layer_id": {"type": "string"},
                    "visible": {"type": "boolean"},
                },
                "required": ["layer_id", "visible"],
            },
            handler=lambda args: toggle_layer(state, args),
        ),
        ToolSpec(
            name="add_wms_layer",
            description="Register a WMS layer reference in current map context.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "layers": {"type": "string"},
                    "name": {"type": "string"},
                },
                "required": ["url", "layers"],
            },
            handler=lambda args: add_wms_layer(state, args),
        ),
    ]


def fly_to(state: MapState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["lon", "lat"])
    lon = as_float(args["lon"], "lon")
    lat = as_float(args["lat"], "lat")
    zoom = as_float(args.get("zoom", 8), "zoom")
    if zoom < 1 or zoom > 20:
        raise MCPError("zoom must be between 1 and 20", code=-32602)

    span = max(0.001, 180.0 / (2 ** (zoom - 1)))
    state.extent = (lon - span, lat - span, lon + span, lat + span)
    return {
        "status": "ok",
        "center": {"lon": lon, "lat": lat},
        "zoom": zoom,
        "extent": list(state.extent),
        "crs": state.crs,
    }


def get_extent(state: MapState) -> dict[str, object]:
    return {"extent": list(state.extent), "crs": state.crs}


def set_crs(state: MapState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["crs"])
    state.crs = validate_epsg(args["crs"])
    return {"status": "ok", "crs": state.crs}


def list_layers(state: MapState) -> dict[str, object]:
    layers = [
        {
            "layer_id": layer.layer_id,
            "name": layer.name,
            "source_type": layer.source_type,
            "visible": layer.visible,
            "metadata": layer.metadata,
        }
        for layer in state.layers.values()
    ]
    return {"count": len(layers), "layers": layers}


def toggle_layer(state: MapState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["layer_id", "visible"])
    layer_id = args["layer_id"]
    if not isinstance(layer_id, str):
        raise MCPError("layer_id must be a string", code=-32602)
    if layer_id not in state.layers:
        raise MCPError(f"Layer not found: {layer_id}", code=-32602)
    visible = args["visible"]
    if not isinstance(visible, bool):
        raise MCPError("visible must be a boolean", code=-32602)
    state.layers[layer_id].visible = visible
    return {"status": "ok", "layer_id": layer_id, "visible": visible}


def add_wms_layer(state: MapState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["url", "layers"])
    url = args["url"]
    layers = args["layers"]
    name = args.get("name", f"WMS {layers}")

    if not isinstance(url, str) or not url.strip():
        raise MCPError("url must be a non-empty string", code=-32602)
    if not isinstance(layers, str) or not layers.strip():
        raise MCPError("layers must be a non-empty string", code=-32602)
    if not isinstance(name, str) or not name.strip():
        raise MCPError("name must be a non-empty string", code=-32602)

    layer_id = str(uuid4())
    state.layers[layer_id] = Layer(
        layer_id=layer_id,
        name=name,
        source_type="wms",
        metadata={"url": url, "layers": layers},
    )
    return {"status": "ok", "layer_id": layer_id, "name": name, "source_type": "wms"}


def set_extent(state: MapState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["bbox"])
    bbox_obj = args["bbox"]
    if not isinstance(bbox_obj, list):
        raise MCPError("bbox must be a list", code=-32602)
    bbox = validate_bbox(bbox_obj)
    state.extent = bbox
    return {"status": "ok", "extent": list(state.extent), "crs": state.crs}
