---
name: qcc-ownership-trace
description: |
  企查查"股权穿透"工作流。聚合:实际控制人 / 受益所有人 (UBO, 25% AML 口径) / 一层股东 / 对外投资 / 工商变更记录(股权与资本变更线索)。
  适用于关联交易识别 / 反洗钱合规 (KYB AML) / M&A 标的实控人确认 / 集团股权结构梳理 / 关键股东退出预警。
  IF user asks about 实控人 / 股东 / UBO / 受益所有人 / 股权穿透 / 谁控制 / 对外投资 / 集团结构, THEN this skill.
  Triggers: "实控人是谁", "穿透股权", "查受益所有人", "对外投资了哪些", "股东结构", "股权变更", "谁拿了多少股".
  NOT for: 法代/高管个人对外投资 → qcc-executive-background; 上市主体股东 → 用上市公司公告.
---

# qcc-ownership-trace — 股权 / 实控 / UBO 穿透

## 何时用

- KYB AML 合规:必须识别持股 ≥25% 的最终自然人受益所有人
- 关联交易识别 / 关联方清单
- M&A:确认标的最终实控人是否是宣称的同一人
- 监测股东变更(套现 / 引战 / 员工持股平台调整)
- 看一家公司的"集团版图"

## 不用的场景

- 只想知道法代的对外投资 → `qcc-executive-background`(它有 `get_executive_investments`)
- 港股 / A 股上市公司的公众持股结构 → 用监管公告 / 招股书,QCC 工商数据只有境内 OpCo 股东
- 历史层级股东追溯 → 部分在 `history` server(目前账户拿不到)

## 调用流程

**步骤 0**:`qcc-anchor` → USCC

**步骤 1-5**(均用 USCC,可并行):

| 序 | tool | 关键字段 | 何时不可省 |
|---|---|---|---|
| 1 | `get_actual_controller` | 实控人姓名 / 直接持股 / 表决权 | 任何"谁控制"问题 |
| 2 | `get_beneficial_owners` | UBO 自然人 / 受益类型 / 最终受益股份 / 形成日期 | AML / 合规审查 |
| 3 | `get_shareholder_info` | 一层股东 / 持股 / 认缴 / 实缴 | 看直接股东(含法人股东 / LP) |
| 4 | `get_external_investments` | 被投企业 / 持股 / 认缴出资 | 集团版图 / 子公司清单 |
| 5 | `get_change_records` | 41 类变更记录(自动聚合) | 看股权 / 资本变动时间线 |

## 三个工具的区别(高频混淆 — 看清楚再选)

| 问题 | 选哪个 |
|---|---|
| "谁控制这家公司"(可能法人) | `get_actual_controller` |
| "最终受益自然人是谁"(AML) | `get_beneficial_owners` |
| "有哪些股东" | `get_shareholder_info` |

❌ 不要为了"保险"三个都调一遍 —— actual_controller 已完成穿透分析,beneficial_owners 已 25%+ 过滤,重复调浪费配额。

## 输出契约

```yaml
controller:
  name: str
  direct_pct: float       # 直接持股 %
  voting_pct: float       # 表决权 %
ubo:                       # AML 口径
  - name: str
    benefit_pct: float
    voting_pct: float
    formation_date: str
    role: str              # 法定代表人 / 董事长 等
shareholders:              # 一层直接股东
  - name: str
    pct: float
    subscribed: str
    paid: str
investments:               # 对外投资
  - target: str
    pct: float
    amount: str
    status: str
changes:                   # 变更记录(聚合)
  - date: str
    type: str              # 股东 / 经营范围 / 法代 等
    before: str
    after: str
```

## 风控速读规则(给 Agent 用)

跑完后,Agent 应自动 flag 这些信号:

- ⚠️ 近 12 个月股东大变(整体退出 ≥ 10%)→ 高优关注
- ⚠️ UBO 在多家子公司同时是 UBO → 关联交易关注
- ⚠️ 实控人与法定代表人不一致 → 影子控制可能
- ⚠️ 一层股东中有"X米企业管理合伙(有限合伙)"批量出现 → 员工持股平台(正常),但 LP/GP 结构需另查
- ⚠️ 对外投资有"金融科技""支付""小贷""典当""融资租赁"字样 → 金融牌照,需另跑监管审查
