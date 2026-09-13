import asyncio

from device_command_mcp.server import DeviceCommandTools


class Client:
    def __init__(self):
        self.calls = []

    async def execute(self, operation, devices, arguments=None, request_id=""):
        self.calls.append((operation, devices, arguments, request_id))
        return {"request_id": request_id, "results": []}


def test_bgp_vrf_inventory_tool_maps_to_semantic_operation():
    client = Client()
    tools = DeviceCommandTools(client)

    asyncio.run(tools.get_bgp_vrf_inventory(["router1"], "session-1"))

    assert client.calls == [
        ("get_bgp_vrf_inventory", ["router1"], None, "session-1")
    ]


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
