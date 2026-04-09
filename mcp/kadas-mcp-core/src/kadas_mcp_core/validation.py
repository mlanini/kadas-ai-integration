from __future__ import annotations

from kadas_mcp_core.errors import MCPError


def require_keys(payload: dict[str, object], keys: list[str]) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise MCPError(f"Missing required keys: {', '.join(missing)}", code=-32602)


def as_float(value: object, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise MCPError(f"{field_name} must be a number", code=-32602) from exc


def validate_bbox(bbox: list[object]) -> tuple[float, float, float, float]:
    if len(bbox) != 4:
        raise MCPError("bbox must contain exactly 4 numbers", code=-32602)
    min_x, min_y, max_x, max_y = (
        as_float(bbox[0], "bbox[0]"),
        as_float(bbox[1], "bbox[1]"),
        as_float(bbox[2], "bbox[2]"),
        as_float(bbox[3], "bbox[3]"),
    )
    if min_x >= max_x or min_y >= max_y:
        raise MCPError("bbox min values must be lower than max values", code=-32602)
    return min_x, min_y, max_x, max_y


def validate_epsg(crs: object) -> str:
    if not isinstance(crs, str) or not crs.startswith("EPSG:"):
        raise MCPError("crs must be a string like 'EPSG:4326'", code=-32602)
    code = crs.split(":", maxsplit=1)[1]
    if not code.isdigit():
        raise MCPError("crs EPSG code must be numeric", code=-32602)
    return crs
