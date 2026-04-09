from __future__ import annotations

import math
from urllib import parse

from geolocation_server.http import http_get_json
from kadas_mcp_core import ToolSpec
from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.validation import as_float, require_keys


USER_AGENT = "kadas-ai-integration/0.1 (geolocation-server)"


def build_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="geocode",
            description="Geocode a place name using Nominatim.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}},
                "required": ["query"],
            },
            handler=geocode,
        ),
        ToolSpec(
            name="reverse_geocode",
            description="Reverse geocode lon/lat using Nominatim.",
            input_schema={
                "type": "object",
                "properties": {"lon": {"type": "number"}, "lat": {"type": "number"}},
                "required": ["lon", "lat"],
            },
            handler=reverse_geocode,
        ),
        ToolSpec(
            name="search_poi",
            description="Search points of interest around lon/lat and radius using Overpass.",
            input_schema={
                "type": "object",
                "properties": {
                    "lon": {"type": "number"},
                    "lat": {"type": "number"},
                    "radius_m": {"type": "number", "minimum": 1},
                    "amenity": {"type": "string"},
                },
                "required": ["lon", "lat", "radius_m", "amenity"],
            },
            handler=search_poi,
        ),
        ToolSpec(
            name="compute_route",
            description="Compute a route between two points using OSRM.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_lon": {"type": "number"},
                    "start_lat": {"type": "number"},
                    "end_lon": {"type": "number"},
                    "end_lat": {"type": "number"},
                    "profile": {"type": "string", "enum": ["driving", "walking", "cycling"]},
                },
                "required": ["start_lon", "start_lat", "end_lon", "end_lat"],
            },
            handler=compute_route,
        ),
    ]


def geocode(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["query"])
    query = args["query"]
    if not isinstance(query, str) or not query.strip():
        raise MCPError("query must be a non-empty string", code=-32602)
    limit = int(args.get("limit", 5))
    if limit < 1 or limit > 20:
        raise MCPError("limit must be between 1 and 20", code=-32602)

    q = parse.urlencode({"q": query, "format": "jsonv2", "limit": limit})
    url = f"https://nominatim.openstreetmap.org/search?{q}"
    data = http_get_json(url, headers={"User-Agent": USER_AGENT})
    if not isinstance(data, list):
        raise MCPError("Unexpected geocode response", code=-32000)

    results: list[dict[str, object]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "display_name": item.get("display_name"),
                "lon": item.get("lon"),
                "lat": item.get("lat"),
                "type": item.get("type"),
                "class": item.get("class"),
            }
        )
    return {"count": len(results), "results": results}


def reverse_geocode(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["lon", "lat"])
    lon = as_float(args["lon"], "lon")
    lat = as_float(args["lat"], "lat")
    q = parse.urlencode({"lon": lon, "lat": lat, "format": "jsonv2"})
    url = f"https://nominatim.openstreetmap.org/reverse?{q}"
    data = http_get_json(url, headers={"User-Agent": USER_AGENT})
    if not isinstance(data, dict):
        raise MCPError("Unexpected reverse geocode response", code=-32000)
    return {
        "display_name": data.get("display_name"),
        "lon": data.get("lon"),
        "lat": data.get("lat"),
        "address": data.get("address"),
    }


def search_poi(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["lon", "lat", "radius_m", "amenity"])
    lon = as_float(args["lon"], "lon")
    lat = as_float(args["lat"], "lat")
    radius_m = as_float(args["radius_m"], "radius_m")
    amenity = args["amenity"]

    if radius_m <= 0:
        raise MCPError("radius_m must be > 0", code=-32602)
    if not isinstance(amenity, str) or not amenity.strip():
        raise MCPError("amenity must be a non-empty string", code=-32602)

    overpass_query = f"[out:json][timeout:25];(node[\"amenity\"=\"{amenity}\"](around:{int(radius_m)},{lat},{lon}););out body;"
    q = parse.urlencode({"data": overpass_query})
    url = f"https://overpass-api.de/api/interpreter?{q}"

    data = http_get_json(url, headers={"User-Agent": USER_AGENT})
    if not isinstance(data, dict):
        raise MCPError("Unexpected POI response", code=-32000)

    elements = data.get("elements", [])
    pois: list[dict[str, object]] = []
    if isinstance(elements, list):
        for el in elements:
            if not isinstance(el, dict):
                continue
            tags = el.get("tags", {}) if isinstance(el.get("tags"), dict) else {}
            pois.append(
                {
                    "id": el.get("id"),
                    "name": tags.get("name"),
                    "amenity": tags.get("amenity"),
                    "lon": el.get("lon"),
                    "lat": el.get("lat"),
                }
            )
    return {"count": len(pois), "results": pois}


def compute_route(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["start_lon", "start_lat", "end_lon", "end_lat"])
    start_lon = as_float(args["start_lon"], "start_lon")
    start_lat = as_float(args["start_lat"], "start_lat")
    end_lon = as_float(args["end_lon"], "end_lon")
    end_lat = as_float(args["end_lat"], "end_lat")
    profile = args.get("profile", "driving")
    if profile not in {"driving", "walking", "cycling"}:
        raise MCPError("profile must be one of driving, walking, cycling", code=-32602)

    coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    q = parse.urlencode({"overview": "false", "steps": "false"})
    url = f"https://router.project-osrm.org/route/v1/{profile}/{coords}?{q}"
    data = http_get_json(url, headers={"User-Agent": USER_AGENT})

    if not isinstance(data, dict):
        raise MCPError("Unexpected route response", code=-32000)
    routes = data.get("routes", [])
    if not isinstance(routes, list) or not routes:
        straight = _haversine_m(start_lon, start_lat, end_lon, end_lat)
        return {
            "status": "fallback",
            "distance_m": round(straight, 2),
            "duration_s": None,
            "profile": profile,
        }

    first = routes[0]
    if not isinstance(first, dict):
        raise MCPError("Invalid route payload", code=-32000)

    return {
        "status": "ok",
        "distance_m": first.get("distance"),
        "duration_s": first.get("duration"),
        "profile": profile,
    }


def _haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))
