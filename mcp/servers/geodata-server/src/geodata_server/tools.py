from __future__ import annotations

from pathlib import Path
from urllib import parse
from xml.etree import ElementTree

from geodata_server.http import http_get_json, http_get_text, http_post_json
from kadas_mcp_core import ToolSpec
from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.validation import require_keys, validate_bbox


def build_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="search_stac_catalog",
            description="Search STAC API for items with optional collection/bbox/time filters.",
            input_schema={
                "type": "object",
                "properties": {
                    "api_url": {"type": "string"},
                    "collections": {"type": "array", "items": {"type": "string"}},
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "datetime": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                },
                "required": ["api_url"],
            },
            handler=search_stac_catalog,
        ),
        ToolSpec(
            name="get_stac_item",
            description="Retrieve one STAC item by collection and item id.",
            input_schema={
                "type": "object",
                "properties": {
                    "api_url": {"type": "string"},
                    "collection_id": {"type": "string"},
                    "item_id": {"type": "string"},
                },
                "required": ["api_url", "collection_id", "item_id"],
            },
            handler=get_stac_item,
        ),
        ToolSpec(
            name="download_stac_asset",
            description="Download a STAC asset href to a local file path.",
            input_schema={
                "type": "object",
                "properties": {
                    "href": {"type": "string"},
                    "output_path": {"type": "string"},
                },
                "required": ["href", "output_path"],
            },
            handler=download_stac_asset,
        ),
        ToolSpec(
            name="discover_wms",
            description="Parse WMS GetCapabilities and list available layers.",
            input_schema={
                "type": "object",
                "properties": {
                    "capabilities_url": {"type": "string"},
                    "max_layers": {"type": "integer", "minimum": 1, "maximum": 500},
                },
                "required": ["capabilities_url"],
            },
            handler=discover_wms,
        ),
        ToolSpec(
            name="discover_wfs",
            description="Parse WFS GetCapabilities and list feature types.",
            input_schema={
                "type": "object",
                "properties": {
                    "capabilities_url": {"type": "string"},
                    "max_features": {"type": "integer", "minimum": 1, "maximum": 500},
                },
                "required": ["capabilities_url"],
            },
            handler=discover_wfs,
        ),
    ]


def _ensure_non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MCPError(f"{name} must be a non-empty string", code=-32602)
    return value.strip()


def _join_url(base: str, suffix: str) -> str:
    return base.rstrip("/") + "/" + suffix.lstrip("/")


def search_stac_catalog(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["api_url"])
    api_url = _ensure_non_empty_string(args["api_url"], "api_url")
    limit = int(args.get("limit", 10))
    if limit < 1 or limit > 200:
        raise MCPError("limit must be between 1 and 200", code=-32602)

    payload: dict[str, object] = {"limit": limit}

    collections = args.get("collections")
    if collections is not None:
        if not isinstance(collections, list) or not all(isinstance(v, str) for v in collections):
            raise MCPError("collections must be a string array", code=-32602)
        payload["collections"] = collections

    bbox = args.get("bbox")
    if bbox is not None:
        if not isinstance(bbox, list):
            raise MCPError("bbox must be an array", code=-32602)
        payload["bbox"] = list(validate_bbox(bbox))

    dt = args.get("datetime")
    if dt is not None:
        payload["datetime"] = _ensure_non_empty_string(dt, "datetime")

    search_url = _join_url(api_url, "search")
    response = http_post_json(search_url, payload)
    features = response.get("features", [])
    if not isinstance(features, list):
        raise MCPError("Invalid STAC response: features must be a list", code=-32000)

    simplified: list[dict[str, object]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        simplified.append(
            {
                "id": feature.get("id"),
                "collection": feature.get("collection"),
                "bbox": feature.get("bbox"),
                "datetime": (feature.get("properties") or {}).get("datetime")
                if isinstance(feature.get("properties"), dict)
                else None,
                "asset_keys": list((feature.get("assets") or {}).keys())
                if isinstance(feature.get("assets"), dict)
                else [],
            }
        )

    return {
        "count": len(simplified),
        "items": simplified,
        "context": response.get("context"),
    }


def get_stac_item(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["api_url", "collection_id", "item_id"])
    api_url = _ensure_non_empty_string(args["api_url"], "api_url")
    collection_id = parse.quote(_ensure_non_empty_string(args["collection_id"], "collection_id"), safe="")
    item_id = parse.quote(_ensure_non_empty_string(args["item_id"], "item_id"), safe="")

    url = _join_url(api_url, f"collections/{collection_id}/items/{item_id}")
    item = http_get_json(url)
    return {
        "id": item.get("id"),
        "collection": item.get("collection"),
        "bbox": item.get("bbox"),
        "geometry_type": (item.get("geometry") or {}).get("type")
        if isinstance(item.get("geometry"), dict)
        else None,
        "assets": list((item.get("assets") or {}).keys()) if isinstance(item.get("assets"), dict) else [],
        "raw": item,
    }


def download_stac_asset(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["href", "output_path"])
    href = _ensure_non_empty_string(args["href"], "href")
    output_path = Path(_ensure_non_empty_string(args["output_path"], "output_path"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from urllib import request

    request.urlretrieve(href, output_path)
    size = output_path.stat().st_size
    return {"status": "ok", "output_path": str(output_path), "bytes": size}


def _append_capabilities_params(url: str, service: str) -> str:
    parsed = parse.urlparse(url)
    query = dict(parse.parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("service", service)
    query.setdefault("request", "GetCapabilities")
    rebuilt = parsed._replace(query=parse.urlencode(query))
    return parse.urlunparse(rebuilt)


def discover_wms(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["capabilities_url"])
    url = _append_capabilities_params(
        _ensure_non_empty_string(args["capabilities_url"], "capabilities_url"), "WMS"
    )
    max_layers = int(args.get("max_layers", 30))
    if max_layers < 1 or max_layers > 500:
        raise MCPError("max_layers must be between 1 and 500", code=-32602)

    xml_content = http_get_text(url)
    root = ElementTree.fromstring(xml_content)
    layers: list[dict[str, object]] = []

    for element in root.findall(".//{*}Layer"):
        name_node = element.find("{*}Name")
        title_node = element.find("{*}Title")
        if name_node is None or not (name_node.text or "").strip():
            continue
        layers.append(
            {
                "name": (name_node.text or "").strip(),
                "title": (title_node.text or "").strip() if title_node is not None else None,
            }
        )
        if len(layers) >= max_layers:
            break

    return {"count": len(layers), "layers": layers, "request_url": url}


def discover_wfs(args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["capabilities_url"])
    url = _append_capabilities_params(
        _ensure_non_empty_string(args["capabilities_url"], "capabilities_url"), "WFS"
    )
    max_features = int(args.get("max_features", 30))
    if max_features < 1 or max_features > 500:
        raise MCPError("max_features must be between 1 and 500", code=-32602)

    xml_content = http_get_text(url)
    root = ElementTree.fromstring(xml_content)
    feature_types: list[dict[str, object]] = []

    for element in root.findall(".//{*}FeatureType"):
        name_node = element.find("{*}Name")
        title_node = element.find("{*}Title")
        if name_node is None or not (name_node.text or "").strip():
            continue
        feature_types.append(
            {
                "name": (name_node.text or "").strip(),
                "title": (title_node.text or "").strip() if title_node is not None else None,
            }
        )
        if len(feature_types) >= max_features:
            break

    return {"count": len(feature_types), "feature_types": feature_types, "request_url": url}
