from __future__ import annotations

import json
from urllib import request


def http_get_json(url: str, timeout: int = 30, headers: dict[str, str] | None = None) -> dict[str, object] | list[object]:
    req = request.Request(url=url, method="GET", headers=headers or {})
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
