from __future__ import annotations

from uuid import uuid4

from kadas_mcp_core import ToolSpec
from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.validation import as_float, require_keys
from sketching_server.state import SketchingState


def build_tools(state: SketchingState) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="add_pin",
            description="Add a redlining pin at lon/lat.",
            input_schema={
                "type": "object",
                "properties": {
                    "lon": {"type": "number"},
                    "lat": {"type": "number"},
                    "label": {"type": "string"},
                },
                "required": ["lon", "lat"],
            },
            handler=lambda args: add_pin(state, args),
        ),
        ToolSpec(
            name="add_polygon",
            description="Add polygon annotation from coordinate ring.",
            input_schema={
                "type": "object",
                "properties": {
                    "coordinates": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "minItems": 3,
                    },
                    "label": {"type": "string"},
                },
                "required": ["coordinates"],
            },
            handler=lambda args: add_polygon(state, args),
        ),
        ToolSpec(
            name="add_text",
            description="Add text annotation at lon/lat.",
            input_schema={
                "type": "object",
                "properties": {
                    "lon": {"type": "number"},
                    "lat": {"type": "number"},
                    "text": {"type": "string"},
                },
                "required": ["lon", "lat", "text"],
            },
            handler=lambda args: add_text(state, args),
        ),
        ToolSpec(
            name="clear_sketches",
            description="Clear all sketch annotations.",
            input_schema={"type": "object", "properties": {}},
            handler=lambda _args: clear_sketches(state),
        ),
    ]


def add_pin(state: SketchingState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["lon", "lat"])
    lon = as_float(args["lon"], "lon")
    lat = as_float(args["lat"], "lat")
    label = args.get("label", "Pin")
    if not isinstance(label, str):
        raise MCPError("label must be a string", code=-32602)

    pin = {"id": str(uuid4()), "lon": lon, "lat": lat, "label": label}
    state.pins.append(pin)
    return {"status": "ok", "pin": pin, "counts": _counts(state)}


def add_polygon(state: SketchingState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["coordinates"])
    coordinates = args["coordinates"]
    if not isinstance(coordinates, list) or len(coordinates) < 3:
        raise MCPError("coordinates must contain at least 3 points", code=-32602)

    ring: list[list[float]] = []
    for index, point in enumerate(coordinates):
        if not isinstance(point, list) or len(point) != 2:
            raise MCPError(f"coordinates[{index}] must be [lon, lat]", code=-32602)
        ring.append([as_float(point[0], f"coordinates[{index}][0]"), as_float(point[1], f"coordinates[{index}][1]")])

    label = args.get("label", "Polygon")
    if not isinstance(label, str):
        raise MCPError("label must be a string", code=-32602)

    polygon = {"id": str(uuid4()), "coordinates": ring, "label": label}
    state.polygons.append(polygon)
    return {"status": "ok", "polygon": polygon, "counts": _counts(state)}


def add_text(state: SketchingState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["lon", "lat", "text"])
    lon = as_float(args["lon"], "lon")
    lat = as_float(args["lat"], "lat")
    text = args["text"]
    if not isinstance(text, str) or not text.strip():
        raise MCPError("text must be a non-empty string", code=-32602)

    annotation = {"id": str(uuid4()), "lon": lon, "lat": lat, "text": text}
    state.texts.append(annotation)
    return {"status": "ok", "text": annotation, "counts": _counts(state)}


def clear_sketches(state: SketchingState) -> dict[str, object]:
    previous = _counts(state)
    state.pins.clear()
    state.polygons.clear()
    state.texts.clear()
    return {"status": "ok", "cleared": previous, "counts": _counts(state)}


def _counts(state: SketchingState) -> dict[str, int]:
    return {"pins": len(state.pins), "polygons": len(state.polygons), "texts": len(state.texts)}
