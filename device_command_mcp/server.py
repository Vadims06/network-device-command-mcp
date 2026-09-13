"""Vendor-neutral read-only diagnostic MCP tools."""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from device_command_mcp.client import ExecutionProxyClient


class DeviceCommandTools:
    def __init__(self, client: ExecutionProxyClient):
        self._client = client

    async def get_bgp_vrf_inventory(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized BGP VRF inventory for up to 20 devices."""
        return await self._client.execute(
            "get_bgp_vrf_inventory", devices, request_id=request_id
        )

    async def get_ospf_neighbors(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized OSPF neighbors for up to 20 NetBox devices."""
        return await self._client.execute(
            "get_ospf_neighbors", devices, request_id=request_id
        )

    async def get_ospf_neighbor_detail(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized detailed OSPF neighbor state."""
        return await self._client.execute(
            "get_ospf_neighbor_detail", devices, request_id=request_id
        )

    async def get_interface_status(
        self, devices: list[str], interface: str, request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized admin/oper state for an inventoried interface."""
        return await self._client.execute(
            "get_interface_status",
            devices,
            {"interface": interface},
            request_id,
        )

    async def get_ospf_interface(
        self, devices: list[str], interface: str, request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized OSPF state and timers for an interface."""
        return await self._client.execute(
            "get_ospf_interface",
            devices,
            {"interface": interface},
            request_id,
        )

    async def get_ospf_status(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized OSPF process and area status."""
        return await self._client.execute(
            "get_ospf_status", devices, request_id=request_id
        )

    async def get_route(
        self, devices: list[str], prefix: str, request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized routing entries for one IP prefix."""
        return await self._client.execute(
            "get_route", devices, {"prefix": prefix}, request_id
        )

    async def get_rsvp_lsps(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized RSVP-TE tunnel sessions for up to 20 devices."""
        return await self._client.execute(
            "get_rsvp_lsps", devices, request_id=request_id
        )

    async def get_vrf_detail(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized VRF inventory for up to 20 devices."""
        return await self._client.execute(
            "get_vrf_detail", devices, request_id=request_id
        )

    async def get_bgp_summary(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized BGP session summary per address family."""
        return await self._client.execute(
            "get_bgp_summary", devices, request_id=request_id
        )

    async def get_bgp_neighbor_detail(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized detailed BGP neighbor state."""
        return await self._client.execute(
            "get_bgp_neighbor_detail", devices, request_id=request_id
        )

    async def get_isis_neighbors(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized IS-IS adjacencies for up to 20 devices."""
        return await self._client.execute(
            "get_isis_neighbors", devices, request_id=request_id
        )

    async def get_isis_interface(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized IS-IS per-interface state and per-level metrics."""
        return await self._client.execute(
            "get_isis_interface", devices, request_id=request_id
        )

    async def get_isis_database(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized IS-IS LSDB summary, per level."""
        return await self._client.execute(
            "get_isis_database", devices, request_id=request_id
        )

    async def get_mpls_forwarding(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized MPLS label forwarding table."""
        return await self._client.execute(
            "get_mpls_forwarding", devices, request_id=request_id
        )

    async def get_ldp_neighbors(
        self, devices: list[str], request_id: str = ""
    ) -> dict[str, Any]:
        """Return normalized LDP session state for up to 20 devices."""
        return await self._client.execute(
            "get_ldp_neighbors", devices, request_id=request_id
        )


def build_mcp(client: ExecutionProxyClient, bearer_token: str) -> FastMCP:
    verifier = StaticTokenVerifier(
        tokens={
            bearer_token: {
                "client_id": "device-command-client",
                "scopes": ["device:read"],
            }
        },
        required_scopes=["device:read"],
    )
    mcp = FastMCP("device-command", auth=verifier)
    tools = DeviceCommandTools(client)
    mcp.tool(tools.get_bgp_vrf_inventory)
    mcp.tool(tools.get_ospf_neighbors)
    mcp.tool(tools.get_ospf_neighbor_detail)
    mcp.tool(tools.get_interface_status)
    mcp.tool(tools.get_ospf_interface)
    mcp.tool(tools.get_ospf_status)
    mcp.tool(tools.get_route)
    mcp.tool(tools.get_rsvp_lsps)
    mcp.tool(tools.get_vrf_detail)
    mcp.tool(tools.get_bgp_summary)
    mcp.tool(tools.get_bgp_neighbor_detail)
    mcp.tool(tools.get_isis_neighbors)
    mcp.tool(tools.get_isis_interface)
    mcp.tool(tools.get_isis_database)
    mcp.tool(tools.get_mpls_forwarding)
    mcp.tool(tools.get_ldp_neighbors)
    return mcp


def create_server() -> FastMCP:
    client = ExecutionProxyClient(
        os.environ["EXECUTION_PROXY_URL"],
        os.environ["EXECUTION_PROXY_TOKEN"],
    )
    return build_mcp(client, os.environ["DEVICE_COMMAND_MCP_TOKEN"])
