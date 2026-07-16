"""Execution-proxy HTTP client."""

from __future__ import annotations

from typing import Any

import httpx


class ExecutionProxyClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        client: httpx.AsyncClient | None = None,
    ):
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=35.0,
        )
        self._owns_client = client is None

    async def execute(
        self,
        operation: str,
        devices: list[str],
        arguments: dict[str, Any] | None = None,
        request_id: str = "",
    ) -> dict[str, Any]:
        response = await self._client.post(
            "/v1/execute",
            json={
                "operation": operation,
                "devices": devices,
                "arguments": arguments or {},
                "request_id": request_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
