#!/usr/bin/env node
/** Smoke: mcp_execute_tool accepts server/tool aliases (patched mcp-lazy). */
import { createRequire } from "node:module";
import { join } from "node:path";

const repo = process.env.REPO_ROOT || join(import.meta.dirname, "../..");
const require = createRequire(
  join(repo, "ai-toolstack/data/local/node_modules/mcp-lazy/package.json")
);
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

const serveSh = join(repo, "ai-toolstack/bin/mcp-lazy-serve.sh");

async function main() {
  const transport = new StdioClientTransport({
    command: serveSh,
    args: [],
    cwd: repo,
    env: {
      ...process.env,
      AI_TOOLSTACK_TOKEN_STATS_CJS: join(repo, "ai-toolstack/lib/mcp-lazy-token-stats.cjs"),
    },
    stderr: "pipe",
  });
  const client = new Client({ name: "execute-alias-smoke", version: "1.0.0" });
  await client.connect(transport);
  try {
    const alias = await client.callTool({
      name: "mcp_execute_tool",
      arguments: {
        server: "memory",
        tool: "search_nodes",
        arguments: { query: "__execute_alias_smoke__" },
      },
    });
    if (alias.isError) {
      console.error("FAIL alias:", JSON.stringify(alias.content).slice(0, 400));
      process.exit(1);
    }
    console.log("OK mcp_execute_tool server/tool aliases");
  } finally {
    await client.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
