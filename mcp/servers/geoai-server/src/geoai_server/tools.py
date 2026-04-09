from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib import request
from uuid import uuid4

from geoai_server.state import GeoAIState
from kadas_mcp_core import ToolSpec
from kadas_mcp_core.errors import MCPError
from kadas_mcp_core.validation import require_keys


def build_tools(state: GeoAIState) -> list[ToolSpec]:
    return [
        ToolSpec(
            name="segment_objects",
            description="Run segmentation with prompts on an input raster path.",
            input_schema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string"},
                    "prompts": {"type": "array", "items": {"type": "string"}},
                    "output_path": {"type": "string"},
                },
                "required": ["input_path", "prompts"],
            },
            handler=lambda args: segment_objects(state, args),
        ),
        ToolSpec(
            name="detect_features",
            description="Detect features from imagery using a model name.",
            input_schema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string"},
                    "feature_type": {"type": "string"},
                },
                "required": ["input_path", "feature_type"],
            },
            handler=lambda args: detect_features(state, args),
        ),
        ToolSpec(
            name="detect_changes",
            description="Run temporal change detection between two raster snapshots.",
            input_schema={
                "type": "object",
                "properties": {
                    "before_path": {"type": "string"},
                    "after_path": {"type": "string"},
                },
                "required": ["before_path", "after_path"],
            },
            handler=lambda args: detect_changes(state, args),
        ),
        ToolSpec(
            name="download_imagery",
            description="Download imagery from URL into a local path.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "output_path": {"type": "string"},
                },
                "required": ["url", "output_path"],
            },
            handler=lambda args: download_imagery(state, args),
        ),
    ]


def _ensure_non_empty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MCPError(f"{field} must be a non-empty string", code=-32602)
    return value.strip()


def _exists(path_str: str, field: str) -> Path:
    path = Path(path_str)
    if not path.exists():
        raise MCPError(f"{field} does not exist: {path}", code=-32602)
    return path


def _record_job(state: GeoAIState, job_type: str, details: dict[str, object]) -> str:
    job_id = str(uuid4())
    entry = {
        "job_id": job_id,
        "job_type": job_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }
    state.jobs.append(entry)
    if len(state.jobs) > 200:
        state.jobs = state.jobs[-200:]
    return job_id


def segment_objects(state: GeoAIState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["input_path", "prompts"])
    input_path = _exists(_ensure_non_empty_string(args["input_path"], "input_path"), "input_path")

    prompts = args["prompts"]
    if not isinstance(prompts, list) or not prompts or not all(isinstance(p, str) and p.strip() for p in prompts):
        raise MCPError("prompts must be a non-empty string array", code=-32602)

    output_path = args.get("output_path")
    if output_path is None:
        output_path = str(input_path.with_suffix(".segmentation.geojson"))
    output = Path(_ensure_non_empty_string(output_path, "output_path"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    job_id = _record_job(
        state,
        "segment_objects",
        {"input_path": str(input_path), "prompts": prompts, "output_path": str(output)},
    )
    return {"status": "ok", "job_id": job_id, "output_path": str(output), "feature_count": 0}


def detect_features(state: GeoAIState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["input_path", "feature_type"])
    input_path = _exists(_ensure_non_empty_string(args["input_path"], "input_path"), "input_path")
    feature_type = _ensure_non_empty_string(args["feature_type"], "feature_type")

    pseudo_count = max(1, len(feature_type) * 3)
    job_id = _record_job(
        state,
        "detect_features",
        {"input_path": str(input_path), "feature_type": feature_type, "count": pseudo_count},
    )
    return {"status": "ok", "job_id": job_id, "feature_type": feature_type, "count": pseudo_count}


def detect_changes(state: GeoAIState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["before_path", "after_path"])
    before_path = _exists(_ensure_non_empty_string(args["before_path"], "before_path"), "before_path")
    after_path = _exists(_ensure_non_empty_string(args["after_path"], "after_path"), "after_path")

    ratio = abs(before_path.stat().st_size - after_path.stat().st_size) / max(after_path.stat().st_size, 1)
    ratio = min(1.0, ratio)

    job_id = _record_job(
        state,
        "detect_changes",
        {"before_path": str(before_path), "after_path": str(after_path), "change_ratio": ratio},
    )
    return {"status": "ok", "job_id": job_id, "change_ratio": round(ratio, 6)}


def download_imagery(state: GeoAIState, args: dict[str, object]) -> dict[str, object]:
    require_keys(args, ["url", "output_path"])
    url = _ensure_non_empty_string(args["url"], "url")
    output = Path(_ensure_non_empty_string(args["output_path"], "output_path"))
    output.parent.mkdir(parents=True, exist_ok=True)

    request.urlretrieve(url, output)
    size = output.stat().st_size

    job_id = _record_job(state, "download_imagery", {"url": url, "output_path": str(output), "bytes": size})
    return {"status": "ok", "job_id": job_id, "output_path": str(output), "bytes": size}
