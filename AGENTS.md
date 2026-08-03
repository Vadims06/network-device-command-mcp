# AGENTS.md — device-command-mcp

Guide for an AI agent working **on this repository**. Read
[README.md](README.md) first for the tool list.

## What belongs here — and what does not

This repo is a protocol adapter. Its whole job is: MCP tool call in, one
`device-command-proxy` operation out, JSON back unchanged.

| Belongs here | Belongs in device-command-proxy |
|---|---|
| Tool registration and signatures | Operation allowlist |
| Tool docstrings (the LLM reads them) | Argument validation |
| MCP bearer auth and scopes | Credentials, SSH, host keys |
| The HTTP client to the proxy | Vendor commands and normalizers |
| — | Audit logging |

If a change adds validation, retries, caching, or output reshaping here, it is
in the wrong repo. Duplicated validation is worse than none: the two copies
drift, and the proxy's copy is the one that is actually authoritative.

## Layout

| File | Role |
|---|---|
| `server.py` | `DeviceCommandTools` (one method per tool), `build_mcp()` wiring, `create_server()` env entrypoint |
| `client.py` | `ExecutionProxyClient` — a single `POST /v1/execute` |

## Adding a tool

Only after the operation exists in `device-command-proxy`.

1. Add an `async def` to `DeviceCommandTools` whose parameters mirror the
   proxy's operation arguments, plus `request_id: str = ""`.
2. Register it in `build_mcp()` with `mcp.tool(tools.<name>)`.
3. Add a test to `tests/test_tools.py` asserting the exact `(operation,
   devices, arguments)` tuple forwarded to a fake client.
4. Update the tool table in `README.md`.

```python
async def get_route(self, devices: list[str], prefix: str, request_id: str = "") -> dict[str, Any]:
    """Return normalized routing entries for one IP prefix."""
    return await self._client.execute("get_route", devices, {"prefix": prefix}, request_id)
```

**The docstring is the tool description an LLM sees.** Write it for a model
choosing between tools: say what comes back and what the arguments mean, in one
sentence. It is the only prompt-facing text in the repo.

## Errors

The client calls `raise_for_status()`, so a proxy rejection surfaces as an
`httpx.HTTPStatusError` and the MCP call fails. Per-device failures are
different: those come back inside a `200` response as entries with
`status: "error"` and an error code, and must be passed through untouched so
the agent can reason about a partial result.

Do not translate, summarize, or filter proxy error codes here.

## Auth

`StaticTokenVerifier` gates every tool on scope `device:read`. Tokens come from
the environment only — never a default, never a literal in code. Both tokens
(inbound MCP, outbound proxy) are required at startup; a missing one should
crash the process, not degrade to unauthenticated.

## Tests

```bash
pytest tests -q
```

Inject a fake client; never contact a real proxy.
