# qcc/skills — 企查查工作流 skill 集合

7 个按"尽调工作流"切的 skill,每个 skill 背后串多个 QCC MCP tool。

| skill | 用途 | 用到的 server | tool 数 | 输入 |
|---|---|---|---|---|
| [`qcc-anchor`](./qcc-anchor/) | 主体锚定(任何下游 skill 的前置) | company | 2 | 企业名 OR USCC |
| [`qcc-basic-profile`](./qcc-basic-profile/) | 工商基础摘要 / KYB 初步 | company | 8 | USCC |
| [`qcc-ownership-trace`](./qcc-ownership-trace/) | 股权穿透 / 实控人 / UBO | company | 5 | USCC |
| [`qcc-risk-screen`](./qcc-risk-screen/) | 全维度司法 / 失信 / 限消 / 异常风险 | risk | 35 | USCC |
| [`qcc-ipr-portfolio`](./qcc-ipr-portfolio/) | 专利 / 商标 / 著作权 / 数字资产 / 自媒体 | ipr | 18 | USCC |
| [`qcc-operation-pulse`](./qcc-operation-pulse/) | 资质 / 招投标 / 招聘 / 融资 / 舆情 / 公告 | operation | 35 | USCC |
| [`qcc-executive-background`](./qcc-executive-background/) | 法代 / 高管个人背调(当前+历史) | executive | 42 | USCC + 人名 |

`history` server(34 tool)需企业认证,目前账户拿不到,**未生成 skill**;后续拿到 enterprise key 后补 `qcc-historical-trail` 即可。

完整工具目录:[`_inventory.json`](./_inventory.json) — 146 个 tool 全量 schema,Hermes / 自定义 agent 应当从此读取。

## 给 Claude Code 用

把 `qcc/skills/` 整个目录(或其中某个 skill 子目录)拷贝/软链到 Claude Code 的 skill 加载路径:

```bash
# 全部安装到本地(用户级)
ln -s "$(pwd)/qcc-anchor" ~/.claude/skills/qcc-anchor
ln -s "$(pwd)/qcc-basic-profile" ~/.claude/skills/qcc-basic-profile
# ... 其他 5 个同理

# 或一行批量
for d in qcc-*; do ln -s "$(pwd)/$d" ~/.claude/skills/$d; done
```

下次 Claude Code 启动后,用户说"做一下这家公司的基础尽调",Claude 会自动匹配 `qcc-basic-profile` 并按 SKILL.md 里的 flow 调原生 MCP tool(前提是 `.mcp.json` 已配,见仓库根的 [README.md](../README.md))。

## 给 OpenClaw(龙虾)用

详见 [`_openclaw.md`](./_openclaw.md)。HTTP transport 直接装,把 6 个 server 合并到 `~/.openclaw/openclaw.json5` 的 `skills.entries`,设环境变量 `QCC_API_KEY`,跑 `openclaw gateway restart` 即生效。

## 给 Hermes / CBC 内部 Agent 框架用

详见 [`_hermes.md`](./_hermes.md)。三步骤:
1. 读 `_inventory.json` 获取全量 tool 目录
2. 读每个 skill 的 `manifest.yaml` 获取工作流定义
3. 按 `flow` 字段顺序(支持 `parallel_group`)调用 `.mcp.json` 里的对应 server

## 调用规则(所有 skill 共享)

1. **锚定先行**:任何"按企业查"的 skill 第一步都是 `qcc-company:get_company_by_query`。返回多个候选时**必须**让用户选,禁止自动选 top1。
2. **USCC 优先**:锚定后用 18 位统一社会信用代码作 `searchKey`,不要把原始企业名继续往下传。
3. **配额意识**:免费额度有限,`qcc-risk-screen` / `qcc-operation-pulse` 单次 30+ 次调用,跑前先确认是否真的需要全维度。每个 skill 的 manifest 都有 `quota_hint`。
4. **error code**:`200001` 鉴权格式不对、`300008` 配额/风控、`-32001` 日调用频率超限。
