import "dotenv/config";
import { QccClient, Server } from "../src/index.js";

async function main(names: string[]) {
  const client = QccClient.fromEnv();

  const tools = await client.listTools(Server.RISK);
  console.log("Available risk tools:");
  for (const t of tools) console.log(`  - ${t.name}: ${t.description ?? ""}`);

  const toolName =
    tools.find((t) => t.name.toLowerCase().includes("judicial"))?.name ??
    tools[0]?.name;
  if (!toolName) {
    console.log("No tools returned — check your API key / quota.");
    return;
  }

  console.log(`\nUsing tool: ${toolName}\n`);
  for (const name of names) {
    console.log(`--- ${name} ---`);
    try {
      const result = await client.call(Server.RISK, toolName, { searchKey: name });
      console.log(result);
    } catch (e) {
      console.log(`  ! failed: ${(e as Error).message}`);
    }
  }
}

const args =
  process.argv.slice(2).length > 0
    ? process.argv.slice(2)
    : ["阿里巴巴(中国)有限公司", "腾讯科技(深圳)有限公司"];

main(args).catch((e) => {
  console.error(e);
  process.exit(1);
});
