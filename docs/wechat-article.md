# 把企查查塞进 AI Agent：一个下午搭完 6 server × 146 tool × 8 工作流的全过程

> 写在前面：这是 KYB / 尽调链路从 0 到 1 的接入笔记。从第一行 `.mcp.json` 到 GitHub 推送完成，**实际工时 2 小时**（16:06 起手 → 18:07 收尾），核心搭建 38 分钟（八个 skill 跑齐）。代码全部开源在 [github.com/zhanglunet/qcc](https://github.com/zhanglunet/qcc)（Apache-2.0），文末有 5 分钟跑通指引。

## 一、为什么要做这件事

做客户准入、供应商入库、投后监控时，绕不开三件事：

- **KYB（Know Your Business）**：合同主体真伪、注册资本实缴、法代是谁
- **司法风险**：被执行、失信、限消、限出境、行政处罚
- **关联版图**：实控人是谁、UBO 穿透到自然人、关键人对外控制了多少家公司

这三件事手工查可以，但有两个问题：

1. **慢**：一家公司散在十几个页面，复制粘贴半小时
2. **断**：信息进不了我们的 Agent 编排（OpenClaw / Hermes / Claude Code），AI 用不上

所以目标变成：**把企查查 146 个查询点变成 AI Agent 原生可调用的工具集**。

## 二、选型：为什么是企查查 MCP，不是 Aily / OpenClaw / 3 元 REST

评估过四条路：

| 选项 | 状态 | 否决理由 |
|---|---|---|
| Aily | ❌ | 不开放 API 直连，只能在 Aily 自己的产品里用 |
| OpenClaw 内置 | ❌ | 当时不稳定，且工具粒度不可控 |
| QCC 企业 REST API | ⏸️ | **3 元/次**，量起来贵；且需要走采购流程 |
| **QCC Agent MCP** | ✅ | 免费 tier + 日配额、**Streamable HTTP**、6 个 MCP server 覆盖全部场景 |

最后选了 [agent.qcc.com](https://agent.qcc.com/guide) 提供的 MCP 路径——付费 REST 后续要上量再切，原型期把链路先打通最重要。

## 三、上游长这样：6 个 MCP server，146 个 tool

QCC 把数据按业务域切成了 6 个独立的 MCP server，每个挂在 `https://agent.qcc.com/mcp/<server>/stream`，Bearer token 鉴权：

| server | tool 数 | 覆盖 |
|---|---:|---|
| `company` | 16 | 工商、股东、UBO、对外投资、年报、财务、分支、上市 |
| `risk` | 35 | 司法、失信、限消限出、经营异常、严重违法、行政处罚、税务异常、破产、抵质押 |
| `ipr` | 18 | 专利、商标、著作权、数字资产、自媒体矩阵 |
| `operation` | 35 | 资质、招投标、招聘、融资、舆情、公告、政府约谈、抽检、召回 |
| `executive` | 42 | 法代/高管个人背调（**双参数：USCC + 人名**，含历史轨迹） |
| `history` | — | 企业历史轨迹（需企业实名认证，免费 key 不可用） |

146 个 tool 的入参/出参 schema 全部抓下来固化成一个 `_inventory.json`——后面 Hermes 直接读这个文件注册工具，不需要再走一次 list_tools。

## 四、四层封装：从 MCP 协议到 8 个工作流 skill

裸 MCP tool 对 AI Agent 不友好：粒度太细，一个尽调要串十几个工具，且每个工具的调用顺序、参数依赖、配额都需要 Agent 自己推理。我们在上面叠了四层：

```
┌──────────────────────────────────────────────────────┐
│ Layer 4：8 个工作流 skill（按尽调动作切）            │
│   qcc-anchor / qcc-basic-profile / qcc-ownership-... │
├──────────────────────────────────────────────────────┤
│ Layer 3：_inventory.json（146 tool 单一事实源）      │
├──────────────────────────────────────────────────────┤
│ Layer 2：Python / TS 客户端（QccClient.call）        │
├──────────────────────────────────────────────────────┤
│ Layer 1：MCP Streamable HTTP（agent.qcc.com）        │
└──────────────────────────────────────────────────────┘
```

## 五、8 个工作流 skill：按"尽调动作"切，不按"工具"切

最关键的设计决策：**skill 边界 = 用户一次尽调动作**，不是工具的简单聚合。

| skill | 串了多少 tool | 单次配额 | 触发短语样例 |
|---|---:|---:|---|
| `qcc-anchor` | 2 | 1 | "锁定主体" / "确认公司" |
| `qcc-basic-profile` | 8 | 8 | "查工商信息" / "拉 KYB 摘要" |
| `qcc-ownership-trace` | 5 | 5 | "实控人是谁" / "穿透股权" / "UBO" |
| `qcc-risk-screen` | 34 | 12 / 19 / 34（quick/default/full） | "查司法风险" / "授信前风险" |
| `qcc-ipr-portfolio` | 18 | 8 / 10 / 18 | "查专利" / "查商标" / "自媒体矩阵" |
| `qcc-operation-pulse` | 35 | 6 / 12 / 35（按 group 选） | "中标记录" / "融资历史" / "舆情" |
| `qcc-executive-background` | 42 | 20 / 42 / 人 | "法代背调" / "高管个人风险" |
| `qcc-person-portfolio` | 7 | 7 / 人 | "查...所有公司" / "导出关联企业" |

每个 skill 是一个目录，里面只有两个文件：

- `SKILL.md` —— 给 Claude Code 用（frontmatter 里的 `description` 决定触发匹配）
- `manifest.yaml` —— 给 Hermes / 自定义 Agent 框架用（结构化 trigger + input schema + flow）

**为什么这样切？** 因为用户说的不是"调 get_company_registration_info"，而是"拉一下小米的工商摘要"。skill 是把"业务语言"翻译成"工具调用序列"的那一层。

## 六、四种接入形态：一鱼四吃

同一套 skill 目录，喂给四个不同的运行时：

| 接入形态 | 适合谁 | 入口 |
|---|---|---|
| **Claude Code 原生 MCP** | 一线员工、调研、临时尽调 | `.mcp.json` + `~/.claude/skills/` |
| **OpenClaw（龙虾）** | 常驻本地 Agent、跨 IM 消息侧 | `~/.openclaw/openclaw.json5` |
| **Hermes（自定义 Agent / LLM 框架）** | 服务端编排、多用户、配额管理 | 读 `_inventory.json` + 各 `manifest.yaml` |
| **Python / TS CLI 或 SDK** | 脚本任务、数据管道、Jupyter | `qcc-py` / `qcc-ts` 或 `import qcc_client` |

### A. Claude Code 原生 MCP（最快）

```bash
cp .mcp.json.example .mcp.json   # 6 个 server 已配好
for d in qcc-*; do
  ln -s "$(pwd)/$d" ~/.claude/skills/$d
done
```

重开 Claude Code，用户说"查一下小米科技的基础尽调"，Claude 自动匹配 `qcc-basic-profile` 并按 flow 调原生 MCP tool。

### B. OpenClaw（龙虾）

```bash
# 1) 把 6 个 server 合并到 ~/.openclaw/openclaw.json5
# 2) 注入 env + 重启
export QCC_API_KEY=你的_token
openclaw gateway restart
# 3) 验证
openclaw skills status              # 6 行 qcc-* connected
openclaw skills info qcc-company    # 列出 16 个 tool
```

### C. Hermes（自定义 Agent 框架）

三步：

1. 读 `skills/_inventory.json` 注册 146 个 MCP tool
2. 读 `skills/qcc-*/manifest.yaml` 装载 8 个工作流（`triggers` / `input` schema / `flow`）
3. 用任意 MCP HTTP 客户端 SDK 连 `.mcp.json` 里的 6 个 server，模板渲染 `{{anchor.uscc}}` 等占位

`_hermes.md` 里给了最小 Python loader 参考实现。

### D. Python / TS CLI

```python
import asyncio
from qcc_client import QccClient, Server

async def main():
    client = QccClient.from_env()
    result = await client.call(
        Server.COMPANY,
        "get_company_by_query",
        {"searchKey": "小米科技"},
    )
    print(result)

asyncio.run(main())
```

CLI 同样的事：

```bash
qcc-py servers                          # 6 个 server
qcc-py tools company                    # 16 个 tool
qcc-py call company get_company_by_query -a '{"searchKey":"小米科技"}'
```

## 七、5 分钟跑通：雷军 → 200 家关联公司

光说不练假把式。下面这套命令，从 clone 到出 Excel 大概 5 分钟：

```bash
# 1) 配 key
git clone https://github.com/zhanglunet/qcc && cd qcc
cp .env.example .env
# 编辑 .env，填上 QCC_API_KEY（裸 token，不带 Bearer 前缀）

# 2) 装 Python 客户端 + skills 额外依赖（openpyxl）
cd python && python3.10 -m venv .venv && source .venv/bin/activate
pip install -e ".[skills]"

# 3) 跑 qcc-person-portfolio —— 反查雷军在企查查全库的对外公司
python ../skills/qcc-person-portfolio/run.py \
  --person "雷军" \
  --anchor-by-name "小米科技"
# → ./雷军_companies.xlsx，8 sheet，约 200 家关联公司
```

打开 xlsx，主 sheet "汇总（去重）" 按企业名称去重，每一行标注这家公司是从哪几个维度命中的：

- 当前董监高任职 / 历史董监高任职
- 当前法定代表人 / 历史法定代表人
- 控制企业（可能截断 100 条）
- 关联企业

这套脚本背后串了 1 个 anchor + 6 个 executive 工具，**所有调用都用 (USCC, 人名) 双参数锚定**——避免重名误锁。

## 八、四条铁律：所有接入形态共享的调用规范

无论你走哪种接入形态，下面四条规则都要遵守：

### 1. 锚定先行

用户给非 USCC（简称 / 品牌名 / 股票简称）时，**第一步永远是** `qcc-company:get_company_by_query`。

返回多个候选时，**必须让用户选**，禁止自动取 top1——QCC 自己的工具描述里就明令禁止了。一个真实违规案例：用户输入"腾讯科技最新工商变更"，AI 自动补全成"腾讯科技深圳有限公司"调下游，命中的是"腾讯科技（深圳）有限公司"（外资子公司），而不是用户真正想要的运营主体"深圳市腾讯计算机系统有限公司"。

### 2. USCC 优先

锚定拿到 18 位统一社会信用代码（正则 `[0-9A-HJ-NPQRTUWXY]{18}`）后，**所有下游调用都用 USCC 作 `searchKey`**，不要再把原始企业名往下传。

### 3. executive server 双参数

`qcc-executive` 工具组例外：必须同时提供 `searchKey`（USCC）+ `personName`（姓名）——双锚定，避免同名误查。

### 4. 配额错误码

- `200001` —— 鉴权格式错（检查是不是带了 `Bearer` 前缀）
- `300008` —— 配额超 / 风控触发
- `-32001` —— 日频率超限

## 九、已知限制 + 后续路线

诚实地列一下没解决的：

- **`history` server 不能用**：需要企业实名认证，免费 key 不行。拿到 enterprise key 后跑一次 `python -m qcc_client.dump_inventory > skills/_inventory.json` 就能并入，再补一个 `qcc-historical-trail` skill 即可
- **`_inventory.json` 会漂移**：是 T+0 快照，QCC 服务端工具改名/增减不自动反映——**每月跑一次** dump_inventory 保持同步
- **单体 OpCo 财务字段大量"企业选择不公示"**：上市集团合并数据需另查港交所 / SEC
- **境外主体不在内**：开曼 / VIE 主体不在 QCC 工商数据，只能查境内 OpCo

## 十、写在最后

整个项目的核心判断只有一个：**AI Agent 时代，数据源接入的颗粒度不是"API"也不是"工具"，而是"工作流"**。

8 个 skill 看似只是把 146 个 tool 重新打包，但真正的价值在于把"用户一次尽调动作"沉淀成可复用、可触发、可被任意 Agent 框架消费的最小单元。Claude Code 拿去做对话式尽调，OpenClaw 拿去做 IM 侧助手，Hermes 拿去做服务端编排，Python 脚本拿去做批量导出——同一份 skill 目录，四个运行时无缝复用。

仓库地址：**https://github.com/zhanglunet/qcc**

如果你也在做 KYB / 尽调 / 投后监控 / 供应商准入，欢迎 fork、提 issue、交换打法。

---

## ⚠️ 免责声明

> 使用本项目前请仔细阅读。继续 clone / fork / 部署 / 调用本项目，即视为已知悉并同意以下全部条款。完整版见仓库 [DISCLAIMER.md](https://github.com/zhanglunet/qcc/blob/main/DISCLAIMER.md)。

**① 非官方第三方集成**
本项目是 `agent.qcc.com` 公开 API 的开源接入封装，**非企查查官方产品**，与 **苏州朗动信息技术有限公司** 无任何隶属、代理、合作关系。"企查查" / "QCC" 为其注册商标，本项目仅作描述性引用。

**② 数据来源与准确性**
所有数据由上游 API 返回，准确性、完整性、时效性由上游决定，可能与国家企业信用信息公示系统、裁判文书网、证监会、知识产权局等权威渠道存在出入。**重大决策必须交叉验证**。

**③ 合规使用义务**
使用者须遵守上游服务条款及《个人信息保护法》《数据安全法》《网络安全法》《征信业管理条例》等法律法规。**禁止**用于人肉搜索、骚扰、未授权大规模采集、转售数据等用途。

**④ 个人信息保护**
`executive` / `person-portfolio` 等 skill 触达自然人信息（姓名、任职、关联企业）。处理前须确认 PIPL 第十三条规定的合法基础；自动化决策须满足第二十四条；跨境传输须遵循第三章。"已合法公开" **不豁免**后续处理的合规义务。

**⑤ 仅供参考**
本项目的所有输出**仅供参考**，不构成法律意见、投资建议、税务建议、信贷决策依据。重大商业、法律、金融决策必须由有资质专业人士独立核实。

**⑥ 无担保 · 责任限制**
本项目"按现状"（AS-IS）提供，无任何明示或暗示担保。在适用法律允许的最大范围内，维护者及贡献者不对使用本项目产生的任何直接 / 间接 / 偶发 / 后果性损失承担责任。

**报告问题**：发现合规问题、数据准确性问题、商标 / 著作权争议，请提 [GitHub Issue](https://github.com/zhanglunet/qcc/issues) 并标注 `[urgent]` 前缀。
