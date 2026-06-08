# Hermes 集成指南

Hermes(自定义 Agent / LLM 框架)消费本目录的方式分三层:

```
┌─────────────────────────────────────────────────────┐
│ 1. 全量工具目录    _inventory.json   (146 个 tool)   │
│    Hermes 读这个,知道每个 MCP tool 的入参 schema    │
├─────────────────────────────────────────────────────┤
│ 2. 工作流 skill    qcc-*/manifest.yaml  (7 个)       │
│    Hermes 把每个 skill 当成一个"宏",流程已写好    │
├─────────────────────────────────────────────────────┤
│ 3. MCP 端点配置    qcc/.mcp.json                     │
│    Hermes 的 MCP 客户端用这个连 agent.qcc.com        │
└─────────────────────────────────────────────────────┘
```

## 1. 工具目录(`_inventory.json`)

由 `python -m qcc_client.dump_inventory > skills/_inventory.json` 生成,**T+0 重新生成一次**保证 schema 不漂移。

```json
{
  "company": [
    {
      "name": "get_actual_controller",
      "description": "查询企业的实际控制人详情... (T+0)",
      "input_schema": {
        "type": "object",
        "properties": {"searchKey": {"type": "string", "description": "..."}},
        "required": ["searchKey"]
      }
    },
    ...
  ],
  "risk": [...],
  "ipr": [...],
  "operation": [...],
  "executive": [...],
  "history": []
}
```

Hermes 应直接把这个 JSON 注册成"可用工具列表",每个工具的 fully-qualified name 是 `<server>:<tool>`,例如 `company:get_actual_controller`。

## 2. Skill manifest 协议(`qcc-*/manifest.yaml`)

每个 skill 是一段"按某个工作流串多个 tool"的预制配方。字段约定:

```yaml
name: qcc-basic-profile         # 唯一标识(目录名一致)
version: 0.1.0
display_name: ...               # 中文展示
display_name_en: ...
description: ...                # 中文,用于触发匹配 + 用户可读
description_en: ...
triggers:                       # 中文短语 / 英文短语,Hermes 用 embedding 匹配
  - "查...的工商信息"
  - "做基础尽调"
input:                          # JSON Schema
  type: object
  properties: {...}
  required: [...]
output:                         # 期望输出形状(契约,非强制)
  type: object
  properties: {...}
flow:                           # 有序步骤
  - id: anchor                  # 引用其他 skill
    skill: qcc-anchor
    args: {query: "{{input.company}}"}
    save_as: anchor
    skip_if: "uscc_pattern_matched({{input.company}})"
  - id: registration            # 调具体 MCP tool
    tool: qcc-company:get_company_registration_info
    args: {searchKey: "{{anchor.uscc || input.company}}"}
    parallel_group: profile     # 同组的步骤可并行
  - id: score                   # 后处理(在 Hermes 里跑)
    type: post_process
    rules: [...]
mcp_servers:                    # 本 skill 依赖的 server
  - qcc-company
quota_hint: 8 calls (+1 if anchor needed)
data_freshness: T+0
```

### 字段语义

| 字段 | Hermes 该怎么用 |
|---|---|
| `triggers` | 短语 embedding → 路由到本 skill。当用户原话包含其中之一或近义,激活 |
| `input` | 收集参数(可能要追问用户)。`oneOf` 表示二选一必填 |
| `flow[].tool` | `<server>:<tool_name>`,直接对应 `_inventory.json` |
| `flow[].args` | 简易模板 `{{path}}`,支持 `{{a || b}}` 的 fallback |
| `flow[].parallel_group` | 同名分一组并行 |
| `flow[].skip_if` | 表达式,真则跳过这一步 |
| `flow[].save_as` | 把这一步结果存到上下文 `key`,后续 `{{key.field}}` 引用 |
| `flow[].on_multi_candidate` | `qcc-anchor` 专属,触发追问 |
| `flow[].type: post_process` | 不调外部 tool,在 Hermes 内跑规则引擎 |

### 模板字面量约定(简化版,够 Hermes 实现)

- `{{input.X}}` — 用户输入字段
- `{{a.b.c}}` — 上下文取值
- `{{a || b}}` — 取 `a`,假值时回退 `b`
- 自带函数:`uscc_pattern_matched(s)`、`within_months(date, n)`

如果 Hermes 想更稳,把上面三种字符串模板替换成 Jinja2 / Liquid / mustache 任选一种均可,语义不变。

## 3. MCP 端点(`.mcp.json`)

Hermes 必须用一个能讲 **MCP Streamable HTTP** 的客户端 SDK,目前主流选择:

- Python:`mcp` 包,`mcp.client.streamable_http.streamablehttp_client`
- Node / TS:`@modelcontextprotocol/sdk`,`StreamableHTTPClientTransport`
- Go:`github.com/mark3labs/mcp-go`(社区实现)

`qcc/.mcp.json` 的内容(注意 **不要 commit 进 git,API key 是明文**):

```json
{
  "mcpServers": {
    "qcc-company":   {"type": "http", "url": "https://agent.qcc.com/mcp/company/stream",   "headers": {"Authorization": "Bearer ${QCC_API_KEY}"}},
    "qcc-risk":      {"type": "http", "url": "https://agent.qcc.com/mcp/risk/stream",      "headers": {"Authorization": "Bearer ${QCC_API_KEY}"}},
    "qcc-ipr":       {"type": "http", "url": "https://agent.qcc.com/mcp/ipr/stream",       "headers": {"Authorization": "Bearer ${QCC_API_KEY}"}},
    "qcc-operation": {"type": "http", "url": "https://agent.qcc.com/mcp/operation/stream", "headers": {"Authorization": "Bearer ${QCC_API_KEY}"}},
    "qcc-executive": {"type": "http", "url": "https://agent.qcc.com/mcp/executive/stream", "headers": {"Authorization": "Bearer ${QCC_API_KEY}"}},
    "qcc-history":   {"type": "http", "url": "https://agent.qcc.com/mcp/history/stream",   "headers": {"Authorization": "Bearer ${QCC_API_KEY}"}}
  }
}
```

Hermes 启动时从环境变量 / 密钥管理服务读 `QCC_API_KEY`,模板替换后建立 MCP 会话。

## 一份最小 Python loader(参考实现)

```python
"""hermes_qcc_loader.py — load skills + execute flow."""
import json, yaml, asyncio, re, os
from pathlib import Path
from qcc_client import QccClient   # 我们自己的客户端

SKILLS_DIR = Path(__file__).parent / "qcc" / "skills"

# 1. 工具目录
INVENTORY = json.loads((SKILLS_DIR / "_inventory.json").read_text())

# 2. 装载 7 个 skill
SKILLS = {}
for skill_dir in SKILLS_DIR.glob("qcc-*"):
    manifest = yaml.safe_load((skill_dir / "manifest.yaml").read_text())
    SKILLS[manifest["name"]] = manifest

# 3. flow 执行器(极简版,仅演示)
USCC = re.compile(r"^[0-9A-HJ-NPQRTUWXY]{18}$")

async def execute_skill(name: str, input: dict) -> dict:
    skill = SKILLS[name]
    ctx = {"input": input}
    client = QccClient.from_env()

    # 按 parallel_group 分桶
    groups = {}
    for step in skill["flow"]:
        groups.setdefault(step.get("parallel_group", step["id"]), []).append(step)

    for group_id, steps in groups.items():
        async def run_one(step):
            if step.get("skip_if") and eval_template(step["skip_if"], ctx):
                return
            if "skill" in step:
                result = await execute_skill(step["skill"], {"company": render(step["args"]["query"], ctx)})
            elif "tool" in step:
                server, tool = step["tool"].split(":", 1)
                args = {k: render(v, ctx) for k, v in step["args"].items()}
                result = await client.call(server.removeprefix("qcc-"), tool, args)
            else:
                return
            if "save_as" in step:
                ctx[step["save_as"]] = result
        await asyncio.gather(*[run_one(s) for s in steps])
    return ctx

def render(s, ctx):
    """简化模板:替换 {{path}} 和 {{a || b}}."""
    # 留给 Hermes 用 Jinja2 / 等价工具
    ...
```

## 路由策略建议

1. 用户原话 → 嵌入 → 与每个 skill 的 `triggers + description` 算 cosine 相似度,topk=2
2. 如果 top1 显著领先 → 直接选 top1;否则给用户二选一
3. 提取入参(LLM tool-use schema 模式,把 skill `input` 当 function signature)
4. 执行 flow,流式返回中间结果(每个 `parallel_group` 完成时回一次)
5. 跑完 `post_process` 规则后,产出 `risk_signals` / `key_signals` / `flags` 给上层 Agent 做总结

## 配额管理

- 免费 key 有日调用上限,各 skill 的 `quota_hint` 已给出每次执行的"近似消耗"
- 建议 Hermes 维护一个本地 token bucket,以每天 09:00 重置;`qcc-risk-screen` / `qcc-executive-background` 在桶不足时降级到 `quick` / `current`
- 错误码 `-32001` 表示日频超限,要立即停掉后续并行 group 避免雪崩

## 演进

- `history` server 暂未启用,等企业认证 key 拿到后加 8 个 skill(`qcc-historical-*`)
- 各 skill 的 `output` 字段目前是契约描述,不强制;Hermes 如想做强 schema 校验,把 output schema 转成 JSON Schema / Pydantic 类即可
- 触发器后期可以挂业务术语词典(投后 / KYB / 准入 / 红线 等)增强匹配
