from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SketchingState:
    pins: list[dict[str, object]] = field(default_factory=list)
    polygons: list[dict[str, object]] = field(default_factory=list)
    texts: list[dict[str, object]] = field(default_factory=list)
