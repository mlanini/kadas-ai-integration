from kadas_mcp_core import BaseMCPServer, ToolSpec


class DummyServer(BaseMCPServer):
    def __init__(self) -> None:
        super().__init__(name="dummy-server")
        self.register_tool(
            ToolSpec(
                name="echo",
                description="Echo a value back.",
                input_schema={"type": "object", "properties": {"value": {"type": "string"}}},
                handler=lambda args: {"value": args.get("value")},
            )
        )


def test_initialize_response_shape() -> None:
    server = DummyServer()
    response = server._handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

    assert response is not None
    assert response["result"]["serverInfo"]["name"] == "dummy-server"
    assert "tools" in response["result"]["capabilities"]


def test_tools_call_roundtrip() -> None:
    server = DummyServer()
    response = server._handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"value": "hello"}},
        }
    )

    assert response is not None
    assert response["result"]["isError"] is False
    assert "hello" in response["result"]["content"][0]["text"]
