"""Dump all tools (name + description + inputSchema) from all 6 QCC MCP servers to JSON.

Usage:
    python -m qcc_client.dump_inventory > ../skills/_inventory.json
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from qcc_client.client import QccClient
from qcc_client.servers import Server

# Walk up to find a .env
for candidate in (Path.cwd(), Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent):
    if (candidate / ".env").exists():
        load_dotenv(candidate / ".env")
        break


async def main() -> None:
    client = QccClient.from_env()
    inventory: dict[str, list[dict]] = {}
    for server in Server:
        try:
            tools = await client.list_tools(server)
            inventory[server.value] = tools
            print(f"{server.value}: {len(tools)} tools", file=sys.stderr)
        except Exception as e:
            inventory[server.value] = []
            print(f"{server.value}: SKIP ({e})", file=sys.stderr)
    json.dump(inventory, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
