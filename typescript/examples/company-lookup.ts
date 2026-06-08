import "dotenv/config";
import { QccClient, Server } from "../src/index.js";

async function main(searchKey: string) {
  const client = QccClient.fromEnv();

  const tools = await client.listTools(Server.COMPANY);
  console.log(`company exposes ${tools.length} tools; first 5:`);
  for (const t of tools.slice(0, 5)) console.log(`  - ${t.name}`);

  const toolName = "get_company_registration_info";
  console.log(`\nCalling ${toolName}(${JSON.stringify(searchKey)})…`);
  const result = await client.call(Server.COMPANY, toolName, { searchKey });
  console.log(result);
}

const arg = process.argv[2] || "阿里巴巴(中国)有限公司";
main(arg).catch((e) => {
  console.error(e);
  process.exit(1);
});
