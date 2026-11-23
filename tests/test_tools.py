import asyncio

from device_command_mcp.server import DeviceCommandTools


class Client:
    def __init__(self):
        self.calls = []

    async def execute(self, operation, devices, arguments=None, request_id=""):
        self.calls.append((operation, devices, arguments, request_id))
        return {"request_id": request_id, "results": []}


def test_interface_tool_maps_to_one_semantic_operation_without_command_text():
    client = Client()
    tools = DeviceCommandTools(client)

    result = asyncio.run(
        tools.get_interface_status(["router1"], "eth1", "session-1")
    )

    assert result == {"request_id": "session-1", "results": []}
    assert client.calls == [
        (
            "get_interface_status",
            ["router1"],
            {"interface": "eth1"},
            "session-1",
        )
    ]


def test_route_tool_maps_prefix_only():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_route(["router1", "router3"], "10.10.10.6/32"))

    assert client.calls == [
        (
            "get_route",
            ["router1", "router3"],
            {"prefix": "10.10.10.6/32"},
            "",
        )
    ]


def test_rsvp_lsps_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_rsvp_lsps(["router1"], "session-1"))

    assert client.calls == [("get_rsvp_lsps", ["router1"], None, "session-1")]


def test_vrf_detail_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_vrf_detail(["router1"], "session-1"))

    assert client.calls == [("get_vrf_detail", ["router1"], None, "session-1")]


def test_bgp_summary_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_bgp_summary(["router1"], "session-1"))

    assert client.calls == [("get_bgp_summary", ["router1"], None, "session-1")]


def test_bgp_neighbor_detail_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_bgp_neighbor_detail(["router1"], "session-1"))

    assert client.calls == [("get_bgp_neighbor_detail", ["router1"], None, "session-1")]


def test_isis_neighbors_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_isis_neighbors(["router1"], "session-1"))

    assert client.calls == [("get_isis_neighbors", ["router1"], None, "session-1")]


def test_isis_interface_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_isis_interface(["router1"], "session-1"))

    assert client.calls == [("get_isis_interface", ["router1"], None, "session-1")]


def test_isis_database_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_isis_database(["router1"], "session-1"))

    assert client.calls == [("get_isis_database", ["router1"], None, "session-1")]


def test_mpls_forwarding_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_mpls_forwarding(["router1"], "session-1"))

    assert client.calls == [("get_mpls_forwarding", ["router1"], None, "session-1")]


def test_ldp_neighbors_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_ldp_neighbors(["router1"], "session-1"))

    assert client.calls == [("get_ldp_neighbors", ["router1"], None, "session-1")]


def test_every_tool_is_marked_read_only_for_clients_that_gate_calls():
    from device_command_mcp.server import build_mcp

    mcp = build_mcp(Client(), "token")
    tools = asyncio.run(mcp.list_tools())

    assert len(tools) == 17
    assert all(tool.annotations and tool.annotations.readOnlyHint is True for tool in tools)
    assert all(tool.annotations.destructiveHint is False for tool in tools)


def test_stdio_entry_point_serves_tools_without_an_mcp_token():
    import os
    import sys

    from fastmcp import Client as McpClient
    from fastmcp.client.transports import StdioTransport

    environment = {
        "PATH": os.environ["PATH"],
        "EXECUTION_PROXY_URL": "http://127.0.0.1:9",
        "EXECUTION_PROXY_TOKEN": "proxy-token",
    }
    transport = StdioTransport(
        command=sys.executable,
        args=["-c", "from device_command_mcp.server import main; main()"],
        env=environment,
    )

    async def list_tool_names():
        async with McpClient(transport) as client:
            return [tool.name for tool in await client.list_tools()]

    assert len(asyncio.run(list_tool_names())) == 17


def test_http_factory_refuses_to_start_without_an_mcp_token(monkeypatch):
    import pytest

    from device_command_mcp.server import create_server

    monkeypatch.setenv("EXECUTION_PROXY_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("EXECUTION_PROXY_TOKEN", "proxy-token")
    monkeypatch.delenv("DEVICE_COMMAND_MCP_TOKEN", raising=False)

    with pytest.raises(KeyError):
        create_server()
