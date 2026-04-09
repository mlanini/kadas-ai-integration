from __future__ import annotations

import json
from urllib import request


def http_get_json(url: str, timeout: int = 30) -> dict[str, object]:
    req = request.Request(url=url, method="GET")
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def http_get_text(url: str, timeout: int = 30) -> str:
    req = request.Request(url=url, method="GET")
    with request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8")


def http_post_json(url: str, payload: dict[str, object], timeout: int = 30) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
