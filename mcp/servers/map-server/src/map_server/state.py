from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Layer:
    layer_id: str
    name: str
    source_type: str
    visible: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class MapState:
    crs: str = "EPSG:4326"
    extent: tuple[float, float, float, float] = (-180.0, -90.0, 180.0, 90.0)
    layers: dict[str, Layer] = field(default_factory=dict)
