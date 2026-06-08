"""
Async client for the 企查查 MCP Streamable HTTP endpoints.

Endpoints:  https://agent.qcc.com/mcp/<server>/stream
Auth:       Authorization: Bearer <QCC_API_KEY>
Transport:  MCP Streamable HTTP (single bi-directional /stream channel)
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from qcc_client.servers import Server

DEFAULT_BASE_URL = "https://agent.qcc.com/mcp"


@dataclass
class QccClient:
    """Holds credentials + base URL. Sessions are opened per server via `session()`."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(cls) -> "QccClient":
        key = os.environ.get("QCC_API_KEY")
        if not key:
            raise RuntimeError("QCC_API_KEY is not set. Copy .env.example to .env and fill it in.")
        return cls(api_key=key, base_url=os.environ.get("QCC_BASE_URL", DEFAULT_BASE_URL))

    def _url(self, server: Server) -> str:
        return f"{self.base_url}/{server.value}/stream"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    @asynccontextmanager
    async def session(self, server: Server) -> AsyncIterator[ClientSession]:
        """Open an MCP session against one of the six QCC servers."""
        async with streamablehttp_client(self._url(server), headers=self._headers()) as (
            read,
            write,
            _get_session_id,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def list_tools(self, server: Server) -> list[dict[str, Any]]:
        async with self.session(server) as s:
            result = await s.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]

    async def call(
        self, server: Server, tool: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Call a tool on the given server and return the parsed payload.

        Returns the first text/json content block, or the full content list if heterogeneous.
        """
        async with self.session(server) as s:
            result = await s.call_tool(tool, arguments or {})
            return _unwrap(result)


def _unwrap(result: Any) -> Any:
    """Extract a usable payload from an MCP CallToolResult."""
    content = getattr(result, "content", None)
    if not content:
        return None
    if len(content) == 1:
        block = content[0]
        text = getattr(block, "text", None)
        if text is not None:
            return _maybe_json(text)
        return block
    return [getattr(b, "text", b) for b in content]


def _maybe_json(text: str) -> Any:
    import json

    s = text.strip()
    if s.startswith(("{", "[")):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    return text
