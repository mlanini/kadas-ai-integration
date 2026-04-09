from __future__ import annotations

import math

from analysis_server.state import AnalysisState
from kadas_mcp_core import ToolSpec
from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.validation import as_float, require_keys, validate_bbox


def build_tools(state: AnalysisState) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="compute_slope",
            description="Compute a simplified slope metric for a bbox and resolution.",
            input_schema={
                "type": "object",
                "properties": {
                    "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
                    "resolution": {"type": "number", "minimum": 0.1},
                },
                "required": ["bbox"],
            },
            handler=lambda args: compute_slope(state, args),
        ),
        ToolSpec(
            name="compute_hillshade",
            description="Compute a synthetic hillshade descriptor for a bbox.",
            input_schema={
                "type": "object",
                "properties": {
                    "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
                    "azimuth": {"type": "number"},
                    "altitude": {"type": "number"},
                },
                "required": ["bbox"],
            },
            handler=lambda args: compute_hillshade(state, args),
        ),
        ToolSpec(
            name="compute_viewshed",
            description="Estimate visible area ratio from an observer point and radius.",
            input_schema={
                "type": "object",
                "properties": {
                    "observer_lon": {"type": "number"},
                    "observer_lat": {"type": "number"},
                    "observer_height_m": {"type": "number"},
                    "radius_m": {"type": "number"},
                },
                "required": ["observer_lon", "observer_lat", "radius_m"],
            },
            handler=lambda args: compute_viewshed(state, args),
        ),
        ToolSpec(
            name="line_of_sight",
            description="Evaluate a simplified line-of-sight between two coordinates.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_lon": {"type": "number"},
                    "start_lat": {"type": "number"},
                    "end_lon": {"type": "number"},
                    "end_lat": {"type": "number"},
                    "obstacle_factor": {"type": "number"},
                },
                "required": ["start_lon", "start_lat", "end_lon", "end_lat"],
            },
            handler=lambda args: line_of_sight(state, args),
        ),
    ]


def _register(state: AnalysisState, entry: dict[str, object]) -> None:
    state.runs.append(entry)
    if len(state.runs) > 100:
        state.runs = state.runs[-100:]


def compute_slope(state: AnalysisState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["bbox"])
    bbox_obj = args["bbox"]
    if not isinstance(bbox_obj, list):
        raise MCPError("bbox must be a list", code=-32602)
    min_x, min_y, max_x, max_y = validate_bbox(bbox_obj)

    resolution = as_float(args.get("resolution", 30.0), "resolution")
    if resolution <= 0:
        raise MCPError("resolution must be > 0", code=-32602)

    dx = max_x - min_x
    dy = max_y - min_y
    pseudo_slope_deg = min(89.9, (dx + dy) * 1000 / resolution)

    result = {
        "status": "ok",
        "bbox": [min_x, min_y, max_x, max_y],
        "resolution": resolution,
        "mean_slope_deg": round(pseudo_slope_deg, 3),
    }
    _register(state, {"tool": "compute_slope", **result})
    return result


def compute_hillshade(state: AnalysisState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["bbox"])
    bbox_obj = args["bbox"]
    if not isinstance(bbox_obj, list):
        raise MCPError("bbox must be a list", code=-32602)
    min_x, min_y, max_x, max_y = validate_bbox(bbox_obj)

    azimuth = as_float(args.get("azimuth", 315.0), "azimuth")
    altitude = as_float(args.get("altitude", 45.0), "altitude")
    if altitude <= 0 or altitude >= 90:
        raise MCPError("altitude must be between 0 and 90", code=-32602)

    complexity = ((max_x - min_x) + (max_y - min_y)) * 10
    shade = max(0.0, min(255.0, 180 + math.cos(math.radians(azimuth)) * 40 + complexity - altitude))

    result = {
        "status": "ok",
        "bbox": [min_x, min_y, max_x, max_y],
        "azimuth": azimuth,
        "altitude": altitude,
        "mean_hillshade": round(shade, 3),
    }
    _register(state, {"tool": "compute_hillshade", **result})
    return result


def compute_viewshed(state: AnalysisState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["observer_lon", "observer_lat", "radius_m"])
    observer_lon = as_float(args["observer_lon"], "observer_lon")
    observer_lat = as_float(args["observer_lat"], "observer_lat")
    observer_height_m = as_float(args.get("observer_height_m", 2.0), "observer_height_m")
    radius_m = as_float(args["radius_m"], "radius_m")

    if radius_m <= 0:
        raise MCPError("radius_m must be > 0", code=-32602)

    visibility_ratio = max(0.05, min(0.98, 0.45 + math.log10(radius_m + 10) * 0.08 + observer_height_m * 0.01))

    result = {
        "status": "ok",
        "observer": {"lon": observer_lon, "lat": observer_lat, "height_m": observer_height_m},
        "radius_m": radius_m,
        "visibility_ratio": round(visibility_ratio, 4),
    }
    _register(state, {"tool": "compute_viewshed", **result})
    return result


def line_of_sight(state: AnalysisState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["start_lon", "start_lat", "end_lon", "end_lat"])
    start_lon = as_float(args["start_lon"], "start_lon")
    start_lat = as_float(args["start_lat"], "start_lat")
    end_lon = as_float(args["end_lon"], "end_lon")
    end_lat = as_float(args["end_lat"], "end_lat")
    obstacle_factor = as_float(args.get("obstacle_factor", 0.3), "obstacle_factor")

    if obstacle_factor < 0 or obstacle_factor > 1:
        raise MCPError("obstacle_factor must be between 0 and 1", code=-32602)

    distance = math.sqrt((end_lon - start_lon) ** 2 + (end_lat - start_lat) ** 2)
    clear_probability = max(0.0, min(1.0, 1 - obstacle_factor - distance * 0.1))
    is_clear = clear_probability > 0.5

    result = {
        "status": "ok",
        "start": {"lon": start_lon, "lat": start_lat},
        "end": {"lon": end_lon, "lat": end_lat},
        "distance_deg": round(distance, 6),
        "obstacle_factor": obstacle_factor,
        "clear_probability": round(clear_probability, 4),
        "is_clear": is_clear,
    }
    _register(state, {"tool": "line_of_sight", **result})
    return result
