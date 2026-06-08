#!/usr/bin/env node
import "dotenv/config";

import { Command } from "commander";

import { QccClient } from "./client.js";
import { SERVERS, SERVER_KEYS, Server } from "./servers.js";

const program = new Command();

program
  .name("qcc-ts")
  .description("企查查 Agent MCP CLI (TypeScript)")
  .version("0.1.0");

program
  .command("servers")
  .description("List the six available servers.")
  .action(() => {
    console.log("QCC MCP servers:");
    for (const key of SERVER_KEYS) {
      console.log(`  ${key.padEnd(11)} — ${SERVERS[key]}`);
    }
  });

program
  .command("tools <server>")
  .description("List all tools exposed by a server.")
  .action(async (server: string) => {
    assertServer(server);
    const client = QccClient.fromEnv();
    const tools = await client.listTools(server);
    console.log(`${server} exposes ${tools.length} tool(s):`);
    for (const t of tools) {
      console.log(`  • ${t.name} — ${t.description ?? ""}`);
    }
  });

program
  .command("call <server> <tool>")
  .description("Invoke a tool with JSON args.")
  .option("-a, --args <json>", "Arguments as JSON", "{}")
  .action(async (server: string, tool: string, opts: { args: string }) => {
    assertServer(server);
    let args: Record<string, unknown>;
    try {
      args = JSON.parse(opts.args);
    } catch (e) {
      console.error(`--args must be JSON: ${(e as Error).message}`);
      process.exit(1);
    }
    const client = QccClient.fromEnv();
    const out = await client.call(server, tool, args);
    console.log(typeof out === "string" ? out : JSON.stringify(out, null, 2));
  });

function assertServer(s: string): asserts s is Server {
  if (!SERVER_KEYS.includes(s as Server)) {
    console.error(`unknown server "${s}" — must be one of: ${SERVER_KEYS.join(", ")}`);
    process.exit(1);
  }
}

program.parseAsync().catch((err) => {
  console.error(err);
  process.exit(1);
});
