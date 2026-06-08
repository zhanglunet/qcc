"""Look up basic registration info for one company."""
import asyncio
import sys

from dotenv import load_dotenv

from qcc_client import QccClient, Server

load_dotenv()


async def main(search_key: str) -> None:
    client = QccClient.from_env()

    # First see what tools `company` actually exposes (names differ from docs sometimes)
    tools = await client.list_tools(Server.COMPANY)
    print(f"company exposes {len(tools)} tools; first 5:")
    for t in tools[:5]:
        print(f"  - {t['name']}")

    # Common starter tool — adjust name if `tools` output uses a different one
    tool_name = "get_company_registration_info"
    print(f"\nCalling {tool_name}({search_key!r})…")
    result = await client.call(Server.COMPANY, tool_name, {"searchKey": search_key})
    print(result)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "阿里巴巴(中国)有限公司"
    asyncio.run(main(arg))
