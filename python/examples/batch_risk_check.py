"""Run a risk scan across a list of companies, sequentially (rate-limit friendly)."""
import asyncio
import sys

from dotenv import load_dotenv

from qcc_client import QccClient, Server

load_dotenv()


async def main(names: list[str]) -> None:
    client = QccClient.from_env()

    # Discover the right tool name first
    tools = await client.list_tools(Server.RISK)
    print("Available risk tools:")
    for t in tools:
        print(f"  - {t['name']}: {t['description'] or ''}")

    # Pick one — judicial docs is a common starter
    tool_name = next(
        (t["name"] for t in tools if "judicial" in t["name"].lower()),
        tools[0]["name"] if tools else None,
    )
    if not tool_name:
        print("No tools returned — check your API key / quota.")
        return

    print(f"\nUsing tool: {tool_name}\n")
    for name in names:
        print(f"--- {name} ---")
        try:
            result = await client.call(Server.RISK, tool_name, {"searchKey": name})
            print(result)
        except Exception as e:
            print(f"  ! failed: {e}")


if __name__ == "__main__":
    args = sys.argv[1:] or ["阿里巴巴(中国)有限公司", "腾讯科技(深圳)有限公司"]
    asyncio.run(main(args))
