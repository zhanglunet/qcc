/**
 * TypeScript client for 企查查 Agent MCP Streamable HTTP endpoints.
 *
 * Endpoints: https://agent.qcc.com/mcp/<server>/stream
 * Auth:      Authorization: Bearer <QCC_API_KEY>
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

import { Server } from "./servers.js";

export const DEFAULT_BASE_URL = "https://agent.qcc.com/mcp";

export interface ToolInfo {
  name: string;
  description?: string;
  inputSchema: unknown;
}

export class QccClient {
  constructor(
    private readonly apiKey: string,
    private readonly baseUrl: string = DEFAULT_BASE_URL,
  ) {}

  static fromEnv(): QccClient {
    const key = process.env.QCC_API_KEY;
    if (!key) {
      throw new Error("QCC_API_KEY is not set. Copy .env.example to .env and fill it in.");
    }
    return new QccClient(key, process.env.QCC_BASE_URL || DEFAULT_BASE_URL);
  }

  private url(server: Server): URL {
    return new URL(`${this.baseUrl}/${server}/stream`);
  }

  /**
   * Open a session, run `fn`, then close. Always prefer this over manually managing the client.
   */
  async withSession<T>(server: Server, fn: (client: Client) => Promise<T>): Promise<T> {
    const transport = new StreamableHTTPClientTransport(this.url(server), {
      requestInit: {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      },
    });
    const client = new Client({ name: "qcc-ts", version: "0.1.0" }, { capabilities: {} });
    await client.connect(transport);
    try {
      return await fn(client);
    } finally {
      await client.close();
    }
  }

  async listTools(server: Server): Promise<ToolInfo[]> {
    return this.withSession(server, async (c) => {
      const { tools } = await c.listTools();
      return tools.map((t) => ({
        name: t.name,
        description: t.description,
        inputSchema: t.inputSchema,
      }));
    });
  }

  async call(server: Server, tool: string, args: Record<string, unknown> = {}): Promise<unknown> {
    return this.withSession(server, async (c) => {
      const result = await c.callTool({ name: tool, arguments: args });
      return unwrap(result);
    });
  }
}

function unwrap(result: { content?: Array<{ type: string; text?: string }> }): unknown {
  const content = result.content;
  if (!content || content.length === 0) return null;
  if (content.length === 1) {
    const block = content[0];
    if (block.type === "text" && typeof block.text === "string") return maybeJson(block.text);
    return block;
  }
  return content.map((b) => (b.type === "text" ? maybeJson(b.text ?? "") : b));
}

function maybeJson(text: string): unknown {
  const s = text.trim();
  if (s.startsWith("{") || s.startsWith("[")) {
    try {
      return JSON.parse(s);
    } catch {
      /* fall through */
    }
  }
  return text;
}
