# network-device-command-mcp

MCP server that lets an LLM agent read live network-device state, read-only.
Each MCP tool maps 1:1 to one operation of
[network-device-command-proxy](https://github.com/Vadims06/network-device-command-proxy),
which owns validation, credentials, SSH and vendor parsing. This repository adds
only the MCP protocol surface and its bearer-token authentication.

```
LLM agent ──MCP/HTTP──▶ network-device-command-mcp ──HTTP──▶ network-device-command-proxy ──SSH──▶ devices
```

The agent can only call the sixteen tools below. It cannot send a CLI command,
change configuration or see device credentials.

## Tools

Every tool takes `devices` (1–20 inventory names) and an optional `request_id`
that is echoed back and written to the proxy audit log. Results come back per
device, so one unreachable device does not fail the others.

| Tool | Extra arguments | Platforms | Returns |
|---|---|---|---|
| `get_ospf_neighbors` | | FRR, Junos | OSPF neighbors, adjacency state, interface, dead timer |
| `get_ospf_neighbor_detail` | | FRR, Junos | Neighbors plus area and state-change counter |
| `get_ospf_interfaces` | | FRR, Junos | Every OSPF interface: state, cost, timers, network type, neighbor counts |
| `get_ospf_interface` | `interface` | FRR, Junos | The same for one interface |
| `get_ospf_status` | | FRR, Junos | Router ID and per-area counters |
| `get_interface_status` | `interface` | FRR, Junos | Admin/oper state, addresses, MTU, speed |
| `get_route` | `prefix` | FRR, Junos | Routes matching one prefix, with next hops |
| `get_rsvp_lsps` | | IOS XR | RSVP-TE sessions: explicit route, labels, FRR label, record route |
| `get_vrf_detail` | | IOS XR | VRFs: route distinguisher, interfaces, import/export route targets |
| `get_bgp_summary` | | IOS XR | BGP sessions per address family |
| `get_bgp_neighbor_detail` | | IOS XR | Per-neighbor state, timers, message counters |
| `get_isis_neighbors` | | IOS XR | IS-IS adjacencies |
| `get_isis_interface` | | IOS XR | Per-interface IS-IS state, adjacency count and metric per level |
| `get_isis_database` | | IOS XR | LSP summary per level |
| `get_mpls_forwarding` | | IOS XR | MPLS label forwarding table |
| `get_ldp_neighbors` | | IOS XR | LDP sessions |

A platform that does not implement a tool answers `unsupported_operation` for
that device.

The device commands behind each tool and a real response for each are in the
proxy repository: see its
[supported operations](https://github.com/Vadims06/network-device-command-proxy#what-is-supported)
and [operations reference](https://github.com/Vadims06/network-device-command-proxy/blob/main/docs/operations.md).
A tool returns the proxy's JSON unchanged, for example:

```json
{
  "request_id": "",
  "results": [
    {
      "device": "123.123.200.200",
      "operation": "get_isis_neighbors",
      "platform": "iosxr",
      "status": "success",
      "data": {
        "instance": "test",
        "neighbors": [
          {"system_id": "R1_xe", "interface": "Gi0/0/0/0.115", "snpa": "fa16.3eff.4f49",
           "state": "up", "holdtime_sec": 24, "circuit_type": "l1l2"}
        ]
      },
      "duration_ms": 1,
      "unsupported_fields": [],
      "data_source": "fixture"
    }
  ]
}
```

Fields an agent must read before drawing a conclusion: `status` and `error.code`
per device, `unsupported_fields` (null because the vendor cannot report it, not
because it is zero) and `data_source` (`live` or replayed `fixture`).

## Install and run

Requirements: Python 3.12+ and a running network-device-command-proxy.

```bash
python3.12 -m venv venv
venv/bin/pip install -e .

export EXECUTION_PROXY_URL=http://127.0.0.1:8080
export EXECUTION_PROXY_TOKEN=<the proxy's EXECUTION_PROXY_TOKEN>
export DEVICE_COMMAND_MCP_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

venv/bin/fastmcp run device_command_mcp/server.py:create_server --transport http --port 8000
```

| Variable | Meaning |
|---|---|
| `EXECUTION_PROXY_URL` | Base URL of the proxy, for example `http://127.0.0.1:8080` |
| `EXECUTION_PROXY_TOKEN` | Bearer token the proxy expects |
| `DEVICE_COMMAND_MCP_TOKEN` | Bearer token MCP clients must present to this server (scope `device:read`) |

All three are required; a missing one stops the process at startup. Tokens come
from the environment only.

The MCP endpoint is `http://<host>:8000/mcp`. Bind it to a trusted interface and
put TLS in front of it before exposing it beyond localhost.

### Docker

```bash
docker build -t network-device-command-mcp .
docker run --rm -p 127.0.0.1:8000:8000 \
  -e EXECUTION_PROXY_URL -e EXECUTION_PROXY_TOKEN -e DEVICE_COMMAND_MCP_TOKEN \
  network-device-command-mcp
```

The image runs unprivileged as uid 2001 on port 8000.

## Connect a client

Claude Code:

```bash
claude mcp add --transport http device-command http://127.0.0.1:8000/mcp \
  --header "Authorization: Bearer $DEVICE_COMMAND_MCP_TOKEN"
```

Any other MCP client that supports streamable HTTP needs the same two things:
the `/mcp` URL and the `Authorization: Bearer` header. With the `fastmcp`
package installed:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://127.0.0.1:8000/mcp", auth="<DEVICE_COMMAND_MCP_TOKEN>") as client:
        result = await client.call_tool("get_isis_neighbors", {"devices": ["123.123.200.200"]})
        print(result.data)

asyncio.run(main())
```

## Try it without devices

The proxy ships fixture devices that replay captured FRR and IOS XR output.
Start the proxy as described in its
[Try it without devices](https://github.com/Vadims06/network-device-command-proxy#try-it-without-devices),
start this server as above, and call the OSPF, interface and route tools against
`123.10.10.10`, `123.30.30.30` or `123.14.14.14`, and the IS-IS, BGP, VRF, MPLS,
LDP or RSVP tools against `123.123.31.31`, `123.123.100.100` or
`123.123.200.200`. Results carry `data_source: "fixture"`.

## Runbook for agents

[docs/runbook.md](docs/runbook.md) tells an agent how to use these tools to
diagnose a lost OSPF or IS-IS adjacency and a broken BGP/MPLS service: which tool
to call first, what each field means, when to stop. It can be pasted into an
agent's system prompt.

## Tests

```bash
venv/bin/pip install -e ".[test]"
venv/bin/pytest tests -q
```

Tests inject a fake client and never contact a proxy. `tests/test_proxy_parity.py`
reads the operations of the installed network-device-command-proxy and fails if
any has no tool here, or a tool has no operation, so the two stay in step. See [AGENTS.md](AGENTS.md)
if an AI agent is working on this repository.

## License

Apache License 2.0, see [LICENSE](LICENSE).
