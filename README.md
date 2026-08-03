# device-command-mcp

MCP server exposing read-only network diagnostics to LLM agents.

It is a thin, deliberately dumb layer: each MCP tool maps 1:1 to one
`device-command-proxy` operation. All validation, credentials, SSH, and vendor
normalization live in the proxy — this repo adds only the MCP protocol surface
and its bearer-token auth.

```
LLM agent ──MCP/HTTP──▶ device-command-mcp ──HTTP──▶ device-command-proxy ──SSH──▶ devices
```

This repository is the MCP adapter for
[device-command-proxy](https://github.com/Vadims06/device-command-proxy). Read
both READMEs when changing the shared operation contract: this server exposes
the agent-facing tools, while the proxy owns inventory, credentials, SSH,
validation and vendor-neutral responses.

## Tools

| Tool | Arguments | Purpose |
|---|---|---|
| `get_ospf_neighbors` | `devices[]` | OSPF neighbor list and states |
| `get_ospf_neighbor_detail` | `devices[]` | Neighbor states with area and flap counters |
| `get_ospf_status` | `devices[]` | OSPF process and per-area status |
| `get_ospf_interface` | `devices[]`, `interface` | OSPF state, cost, and timers on an interface |
| `get_interface_status` | `devices[]`, `interface` | Admin/oper state, addresses, MTU, speed |
| `get_route` | `devices[]`, `prefix` | Routing entries for one prefix |

Every tool also takes an optional `request_id` used for correlation in the
proxy's audit log. `devices` accepts 1–20 NetBox device names and results come
back per device — one unreachable device does not fail the others.

Returned field schemas are documented in the
[device-command-proxy README](https://github.com/Vadims06/device-command-proxy/blob/main/README.md).

## Configuration

| Variable | Meaning |
|---|---|
| `EXECUTION_PROXY_URL` | Base URL of device-command-proxy, e.g. `http://execution-proxy:8080` |
| `EXECUTION_PROXY_TOKEN` | Bearer token the proxy expects |
| `DEVICE_COMMAND_MCP_TOKEN` | Bearer token clients must present to this server; requires scope `device:read` |

## Run

```bash
pip install -e .
fastmcp run device_command_mcp/server.py:create_server --transport http --port 8000
```

The image runs the same entrypoint unprivileged as uid 2001 on port 8000.

## Tests

```bash
pytest tests -q
```
