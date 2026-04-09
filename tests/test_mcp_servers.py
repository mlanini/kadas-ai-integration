from analysis_server.server import AnalysisMCPServer
from geoai_server.server import GeoAIMCPServer
from geodata_server.server import GeodataMCPServer
from geolocation_server.server import GeolocationMCPServer
from map_server.server import MapMCPServer
from sketching_server.server import SketchingMCPServer


def test_server_tool_registration_counts() -> None:
    servers = {
        "map": MapMCPServer(),
        "geodata": GeodataMCPServer(),
        "analysis": AnalysisMCPServer(),
        "sketching": SketchingMCPServer(),
        "geolocation": GeolocationMCPServer(),
        "geoai": GeoAIMCPServer(),
    }

    assert len(servers["map"].registry.list_tools()) == 6
    assert len(servers["geodata"].registry.list_tools()) == 5
    assert len(servers["analysis"].registry.list_tools()) == 4
    assert len(servers["sketching"].registry.list_tools()) == 4
    assert len(servers["geolocation"].registry.list_tools()) == 4
    assert len(servers["geoai"].registry.list_tools()) == 4


def test_map_tools_basic_calls() -> None:
    server = MapMCPServer()

    fly = server.registry.call_tool("fly_to", {"lon": 8.54, "lat": 47.37, "zoom": 6})
    assert fly["status"] == "ok"
    assert fly["crs"] == "EPSG:4326"

    set_crs = server.registry.call_tool("set_crs", {"crs": "EPSG:3857"})
    assert set_crs["crs"] == "EPSG:3857"

    extent = server.registry.call_tool("get_extent", {})
    assert extent["crs"] == "EPSG:3857"


def test_sketching_workflow() -> None:
    server = SketchingMCPServer()

    pin = server.registry.call_tool("add_pin", {"lon": 8.54, "lat": 47.37, "label": "Zurich"})
    assert pin["counts"]["pins"] == 1

    text = server.registry.call_tool("add_text", {"lon": 8.54, "lat": 47.37, "text": "AOI"})
    assert text["counts"]["texts"] == 1

    cleared = server.registry.call_tool("clear_sketches", {})
    assert cleared["counts"] == {"pins": 0, "polygons": 0, "texts": 0}


def test_analysis_and_geoai_workflows(tmp_path) -> None:
    analysis = AnalysisMCPServer()
    geoai = GeoAIMCPServer()

    slope = analysis.registry.call_tool("compute_slope", {"bbox": [7.0, 46.0, 8.0, 47.0]})
    assert slope["status"] == "ok"
    assert slope["mean_slope_deg"] > 0

    before = tmp_path / "before.tif"
    after = tmp_path / "after.tif"
    raster = tmp_path / "image.tif"
    before.write_bytes(b"1234")
    after.write_bytes(b"123456")
    raster.write_bytes(b"abc")

    changes = geoai.registry.call_tool(
        "detect_changes",
        {"before_path": str(before), "after_path": str(after)},
    )
    assert changes["status"] == "ok"

    segment = geoai.registry.call_tool(
        "segment_objects",
        {"input_path": str(raster), "prompts": ["building"]},
    )
    assert segment["status"] == "ok"
