"""qcc-py CLI — thin wrapper around QccClient."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.table import Table

from qcc_client.client import QccClient
from qcc_client.servers import SERVERS, Server

# Walk up to find a .env in qcc/ root or python/
for candidate in (Path.cwd(), Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent.parent):
    if (candidate / ".env").exists():
        load_dotenv(candidate / ".env")
        break

app = typer.Typer(add_completion=False, help="企查查 Agent MCP CLI")


@app.command("servers")
def cmd_servers() -> None:
    """List the six available servers."""
    table = Table(title="QCC MCP servers")
    table.add_column("key")
    table.add_column("description")
    for srv, desc in SERVERS.items():
        table.add_row(srv.value, desc)
    rprint(table)


@app.command("tools")
def cmd_tools(server: Server) -> None:
    """List all tools exposed by a server."""

    async def _run() -> None:
        client = QccClient.from_env()
        tools = await client.list_tools(server)
        rprint(f"[bold]{server.value}[/bold] exposes {len(tools)} tool(s):")
        for t in tools:
            rprint(f"  • [cyan]{t['name']}[/cyan] — {t['description'] or ''}")

    asyncio.run(_run())


@app.command("call")
def cmd_call(
    server: Server,
    tool: str,
    args_json: str = typer.Option("{}", "--args", "-a", help='Arguments as JSON, e.g. \'{"searchKey":"阿里巴巴"}\''),
) -> None:
    """Invoke a tool. Example: qcc-py call company get_company_registration_info -a '{"searchKey":"阿里巴巴(中国)有限公司"}'"""

    async def _run() -> None:
        client = QccClient.from_env()
        try:
            arguments = json.loads(args_json)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--args must be JSON: {e}")
        out = await client.call(server, tool, arguments)
        rprint(out)

    asyncio.run(_run())


if __name__ == "__main__":
    app()
