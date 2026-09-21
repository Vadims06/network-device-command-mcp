"""The MCP tools must mirror the operations the installed proxy actually serves.

Expectations come from the proxy's own registry, so a new proxy operation with
no MCP tool (or a tool for an operation the proxy dropped) fails here.
"""

import asyncio

import pytest
from fastmcp import Client

from device_command_mcp.server import build_mcp
from device_command_proxy.operation_types import ArgumentKind
from device_command_proxy.operations import OPERATION_SPECS

SAMPLE_ARGUMENT_VALUES = {
    ArgumentKind.INTERFACE: "eth1",
    ArgumentKind.PREFIX: "10.0.0.0/24",
}


class RecordingClient:
    def __init__(self):
        self.calls = []

    async def execute(self, operation, devices, arguments=None, request_id=""):
        self.calls.append((operation, devices, arguments or {}))
        return {"request_id": request_id, "results": []}


def _expected_arguments(spec):
    if spec.argument_kind is ArgumentKind.NONE:
        return {}
    return {spec.argument_kind.value: SAMPLE_ARGUMENT_VALUES[spec.argument_kind]}


@pytest.fixture
def recording_client():
    return RecordingClient()


@pytest.fixture
def mcp_tools(recording_client):
    async def list_tools():
        async with Client(build_mcp(recording_client, "unused")) as client:
            return {tool.name: tool for tool in await client.list_tools()}

    return asyncio.run(list_tools())


def test_every_proxy_operation_has_a_tool_and_no_tool_is_extra(mcp_tools):
    proxy_operations = {operation.value for operation in OPERATION_SPECS}

    assert set(mcp_tools) == proxy_operations


@pytest.mark.parametrize("operation", [operation.value for operation in OPERATION_SPECS])
def test_tool_forwards_its_own_operation_with_the_proxy_argument(
    operation, mcp_tools, recording_client
):
    spec = next(spec for spec in OPERATION_SPECS.values() if spec.operation.value == operation)
    arguments = {"devices": ["router1"], **_expected_arguments(spec)}

    async def call():
        async with Client(build_mcp(recording_client, "unused")) as client:
            await client.call_tool(operation, arguments)

    asyncio.run(call())

    assert recording_client.calls == [(operation, ["router1"], _expected_arguments(spec))]
