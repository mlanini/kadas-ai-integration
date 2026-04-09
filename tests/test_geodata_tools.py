from geodata_server.tools import _append_capabilities_params


def test_append_capabilities_params_wms() -> None:
    url = _append_capabilities_params("https://example.com/ows", "WMS")
    assert "service=WMS" in url
    assert "request=GetCapabilities" in url


def test_append_capabilities_params_preserves_existing_query() -> None:
    url = _append_capabilities_params("https://example.com/ows?foo=bar", "WFS")
    assert "foo=bar" in url
    assert "service=WFS" in url
