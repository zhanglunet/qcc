# OpenClaw(龙虾)集成指南

OpenClaw 是 self-hosted MCP-compatible Agent runtime,通过 [openclaw.cn](https://openclaw.cn/) 中文社区文档接入。
本仓库的 6 个 QCC MCP server **可以直接当成 OpenClaw 的 skill 装载**,无需任何额外胶水代码。

> **OpenClaw 不是傅盛的 AI 产品**(尽管中文社区都叫"龙虾"且傅盛 perspective skill 提到过)。
> OpenClaw 是开源的本地 Agent 运行时,定位类似 Claude Desktop / Cline / Continue,本仓库支持的就是它。

## 0. 前置

- 已装 OpenClaw v2026.4+ (含 `@modelcontextprotocol/sdk@1.25.3+` 原生 MCP 支持)
- 已有 QCC API Key(参考根 README "0. 配 API Key")

## 1. 推荐:HTTP transport(零代码)

OpenClaw 的 MCP 配置在 `~/.openclaw/openclaw.json5`,把下面这段合并到 `skills.entries`:

```json5
{
  skills: {
    entries: {
      "qcc-company": {
        enabled: true,
        transport: "http",
        url: "https://agent.qcc.com/mcp/company/stream",
        apiKey: { source: "env", id: "QCC_API_KEY" }
      },
      "qcc-risk": {
        enabled: true,
        transport: "http",
        url: "https://agent.qcc.com/mcp/risk/stream",
        apiKey: { source: "env", id: "QCC_API_KEY" }
      },
      "qcc-ipr": {
        enabled: true,
        transport: "http",
        url: "https://agent.qcc.com/mcp/ipr/stream",
        apiKey: { source: "env", id: "QCC_API_KEY" }
      },
      "qcc-operation": {
        enabled: true,
        transport: "http",
        url: "https://agent.qcc.com/mcp/operation/stream",
        apiKey: { source: "env", id: "QCC_API_KEY" }
      },
      "qcc-executive": {
        enabled: true,
        transport: "http",
        url: "https://agent.qcc.com/mcp/executive/stream",
        apiKey: { source: "env", id: "QCC_API_KEY" }
      },
      "qcc-history": {
        enabled: false,   // 需要企业实名认证 key,默认关掉
        transport: "http",
        url: "https://agent.qcc.com/mcp/history/stream",
        apiKey: { source: "env", id: "QCC_API_KEY" }
      }
    }
  }
}
```

OpenClaw 的 `apiKey` 字段会自动以 `Authorization: Bearer ${value}` 头注入,刚好对上 QCC 的鉴权方式。

设环境变量:

```bash
export QCC_API_KEY=你的_token      # 不要带 Bearer 前缀
# 或写到 ~/.zshrc / ~/.bashrc / 启动时通过 launchctl setenv 注入
```

重启 gateway:

```bash
openclaw gateway restart
```

验证:

```bash
openclaw skills status
# 应该看到 6 个 qcc-* skill 状态 connected(history 显示 disabled)

openclaw skills info qcc-company
# 应该列出 16 个 tool:get_company_by_query / get_company_registration_info / ...

openclaw logs --filter skills --tail 20
# 看实时日志,确认没有 200001/300008 鉴权错误
```

## 2. Skill plugin(工作流封装,可选)

QCC 的 6 个 server 是"原子工具",`qcc/skills/` 下的 7 个工作流(`qcc-basic-profile` / `qcc-risk-screen` 等)是"组合配方"。OpenClaw 的 ClawHub 也支持 Skill plugin,可以把这 7 个工作流封装成 ClawHub 的 skill。

### 2.1 本地软链(最快验证)

```bash
cd /path/to/qcc/skills
mkdir -p ~/.openclaw/skills
for d in qcc-*; do
  ln -s "$(pwd)/$d" ~/.openclaw/skills/$d
done

openclaw skills reload
openclaw skills status | grep qcc-
```

> **注意**:OpenClaw 当前的 skill 格式是 ClawHub 自定义的(基于 npm 包 + ClawHub publish metadata),
> 跟本仓库的 `manifest.yaml` 不是同一套 schema。本仓库 manifest 给 Hermes 用,OpenClaw 想原生跑这些
> 工作流,需要写一个薄适配层(下面 2.2)。

### 2.2 适配层 — 把 manifest.yaml 翻译成 ClawHub skill

在 `qcc/openclaw_adapter/`(尚未创建,留作 TODO)写一个 Node.js 脚本:

```ts
// openclaw_adapter/build.ts (TODO)
// 读 ../skills/qcc-*/manifest.yaml
// 输出 ClawHub skill 包格式(package.json + index.js + manifest.json)
// 每个 skill 暴露一个 OpenClaw 工具,内部调多个 MCP tool
```

完成后:

```bash
cd qcc/openclaw_adapter
npm run build           # 输出到 dist/qcc-*
clawhub publish ./dist/qcc-basic-profile     # 发布到本地 ClawHub registry
```

**短期建议**:先用 1. 的 HTTP 配置让 OpenClaw 能调 146 个 atomic tool,工作流逻辑放到上层 prompt 里(粘 SKILL.md 内容当 system prompt)。等到调用量上来再投入写适配层。

## 3. 故障排查

| 症状 | 排查 |
|---|---|
| `skills status` 显示 `error: 200001` | `QCC_API_KEY` 没设 / 包含了 `Bearer ` 前缀(不要带) |
| `error: 300008` | 免费配额用完;登 [agent.qcc.com](https://agent.qcc.com/) dashboard 查 |
| `error: -32001` | 日调用频率超限;OpenClaw 配 token bucket 节流 |
| `transport: http` 不识别 | 升级 OpenClaw 到 2026.4+ |
| 6 个 server 加完后内存吃满 | OpenClaw 默认每个 skill 持久连接;按需 `enabled: false` 关一些 |
| `qcc-history` 永远连不上 | 正常 — 需企业实名认证,免费 key 拿不到 |

## 4. CBC 私有 Skill marketplace 思路(后续)

如果 CBC 想把"标准化的 DD 工作流"内部分发,推荐:

1. 在内网搭一个轻量的 ClawHub mirror(就是个 npm registry + 自定义 metadata index)
2. 把 7 个 skill 用 2.2 的适配层封装成 ClawHub 包,发到 mirror
3. CBC 员工本地 `clawhub install @cbc/qcc-basic-profile` 即装即用
4. Skill 内部的 `Authorization` 用员工各自的 `QCC_API_KEY`,**不共享**

这样跟"按使用量算 3 元/次"的企业 API 路径无关 — 每人各跑各的,配额各自管,审计粒度清晰。

## 5. 与本仓库其他三条接入路径的对比

| 路径 | 适合 | 工作流支持 | 复杂度 |
|---|---|---|---|
| Claude Code 原生 MCP + `~/.claude/skills/` | 一线员工 / 调研用 | ✅ 7 个 SKILL.md 触发 | 低 |
| **OpenClaw `~/.openclaw/openclaw.json5`** | 本地常驻 / 跨 IM 接入(WhatsApp/Slack 等) | ⚠️ 工作流需上层 prompt 或写适配层 | 低-中 |
| Hermes (CBC 内部框架) | 服务端编排 / 多用户 / 量化配额 | ✅ manifest.yaml 直接读 | 中 |
| Python / TS CLI | 脚本任务 / 数据管道 / Jupyter | ❌ 手写 | 低 |

## 6. 参考

- OpenClaw 中文社区:https://openclaw.cn
- MCP 协议规范:https://modelcontextprotocol.io
- OpenClaw GitHub Releases:https://github.com/openclaw/openclaw/releases
- 本仓库 Hermes 集成指南:[`_hermes.md`](./_hermes.md)
