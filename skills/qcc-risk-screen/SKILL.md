---
name: qcc-risk-screen
description: |
  企查查"全维度风险扫描"工作流。一次性跑 34 个 risk 维度:司法 / 失信 / 限消 / 限出 / 限高 / 经营异常 / 严重违法 / 行政处罚 / 税务异常 / 破产清算 / 股权冻结 / 质押 / 抵押 / 担保 / 公告 / 开庭 等。
  适用于授信风控 / 投后监控 / M&A 红线扫描 / 重大合同前最后一道闸 / 供应商准入。**配额消耗大**(34 次/家),只在真的需要全维度时跑。
  IF user asks for 风险扫描 / 司法风险 / 失信 / 限高 / 经营异常 / 严重违法 / DD 红线 of a Chinese company, THEN this skill.
  Triggers: "查司法风险", "...有没有被列入失信", "看下风险情况", "全维度风险扫描", "红线扫描", "授信前风险"
  NOT for: 个人(法代/高管)司法风险 → qcc-executive-background; 知识产权侵权诉讼 → 拿 qcc-ipr-portfolio 输出 + qcc-risk-screen 关联.
---

# qcc-risk-screen — 全维度风险扫描

## 何时用

- 授信 / 担保 / 合同审批的最后一道闸
- 供应商 / 经销商准入审核
- M&A 标的红线扫描
- 投后监控(定期跑 + diff 上次结果)
- 客户 / 合作方异动告警

## 不用的场景

- 只是想知道有没有失信(单点查询):直接调单个 tool 即可,不需要 skill
- 个人(法代 / 高管)的司法风险 → `qcc-executive-background`
- 想找特定案号的判决书原文 → QCC 只给摘要,要原文走裁判文书网

## 调用流程

**步骤 0**:`qcc-anchor` → USCC

**步骤 1**:按 4 个优先级分组并行调用(配额紧张时只跑 P0)。

### P0 — 直接 red flag(12 个,必跑)

| tool | 触发即高危 |
|---|---|
| `get_dishonest_info` | 被执行人 / 失信被执行人 |
| `get_exit_restriction` | 限制出境 |
| `get_high_consumption_restriction` | 限制高消费 |
| `get_judgment_debtor_info` | 被执行人 |
| `get_serious_violation` | 严重违法失信名单 |
| `get_business_exception` | 经营异常 |
| `get_bankruptcy_reorganization` | 破产重整 |
| `get_tax_violation` | 税收违法 |
| `get_tax_abnormal` | 税务异常 |
| `get_tax_arrears_notice` | 欠税公告 |
| `get_simple_cancellation_info` | 简易注销中(主体可能即将消失) |
| `get_disciplinary_list` | 联合惩戒名单 |

### P1 — 在册案件 / 诉讼(7 个)

| tool | 含义 |
|---|---|
| `get_judicial_documents` | 裁判文书摘要 |
| `get_case_filing_info` | 在册立案 |
| `get_court_notice` | 在册法院公告 |
| `get_hearing_notice` | 在册未审开庭公告 |
| `get_pre_litigation_mediation` | 诉前调解 |
| `get_service_notice` | 送达公告 |
| `get_service_announcement` | 送达通知 |

### P2 — 财产 / 股权 / 抵质押(8 个)

| tool | 含义 |
|---|---|
| `get_equity_freeze` | 股权冻结 |
| `get_equity_pledge_info` | 股权出质 |
| `get_stock_pledge_info` | 股票质押 |
| `get_chattel_mortgage_info` | 动产抵押 |
| `get_land_mortgage_info` | 土地抵押 |
| `get_judicial_auction` | 司法拍卖 |
| `get_property_asset_announcement` | 财产公告 |
| `get_valuation_inquiry` | 询价评估 |

### P3 — 行政 / 清算 / 终本(7 个)

| tool | 含义 |
|---|---|
| `get_administrative_penalty` | 行政处罚 |
| `get_environmental_penalty` | 环保处罚 |
| `get_default_info` | 违约 / 欠款 |
| `get_guarantee_info` | 对外担保 |
| `get_liquidation_info` | 清算 |
| `get_cancellation_record_info` | 注销记录 |
| `get_public_exhortation` | 公开催告 |
| `get_terminated_cases` | 终结本次执行 |

## 优先级 cutoff(用户没指定时的默认行为)

- 默认跑 **P0 + P1**(19 个 tool)
- 用户说"全维度" / "深度" → 跑完整 34 个
- 用户说"快速" / "授信前 30 秒" → 只跑 P0(12 个)

## 输出契约

```yaml
red_flags:                     # P0 命中
  - dimension: 失信被执行人
    count: 0
    records: []
litigation:                    # P1
  - dimension: 在册立案
    count: 3
    records: [{case_no, plaintiff, defendant, date, status}]
encumbrance:                   # P2
  - dimension: 股权出质
    count: 2
financial_admin:               # P3
  - dimension: 行政处罚
    count: 0
risk_score_hint:               # 给 Agent 用的速读
  level: "low | medium | high"
  reasoning: "..."
```

## 风控规则

- 任何 P0 命中 → `level=high`,立即停止其余流程,要求人工复核
- P1 命中数 ≥ 5 → `level=medium`,提示"诉讼缠身"
- P2 + P3 累计 ≥ 10 → `level=medium`
- 全无命中 → `level=low`,但**不代表零风险**(未覆盖隐性担保 / 跨境诉讼 / 监管约谈)
