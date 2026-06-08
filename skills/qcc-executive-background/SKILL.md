---
name: qcc-executive-background
description: |
  企查查"法代/高管个人背调"工作流。42 个维度,**双参数**:USCC + 自然人姓名。当前 21 维度 + 历史 21 维度 同时覆盖:个人任职 / 对外投资 / 控制企业 / 关联企业 / 受益所有人;个人行政处罚 / 立案 / 法院公告 / 失信 / 股权冻结 / 出质 / 限制出境 / 限高 / 被执行 / 司法文书 / 开庭 / 诉前调解 / 送达 / 税收违法 / 终本 / 悬赏 / 询价。
  适用于:法代/高管入职背调 / 授信申请关键人合规审查 / M&A 团队背调 / 高风险个人识别 / 影子人物穿透。
  IF user asks for 法代背调 / 高管背调 / 个人对外投资 / 个人失信 / 关键人合规 / 个人司法风险 of named persons at a company, THEN this skill.
  Triggers: "查一下这家公司的法定代表人有没有问题", "做高管背调", "...本人的对外投资", "这个人控制了几家公司", "关键人个人风险"
  NOT for: 个人在其他公司的全维度数据(本 skill 锚定主体公司 + 人名,跨公司穿透不在本 skill 范围;要全网穿透需多次调用).
---

# qcc-executive-background — 法代/高管个人背调

## 何时用

- 入职 / 用印 / 授信申请的关键人合规审查
- M&A 标的核心团队个人风险扫描
- 影子人物识别:法定代表人 vs 实际操盘人
- 关联企业图谱构建(基于个人对外投资)

## 不用的场景

- 公司主体的司法风险 → `qcc-risk-screen`
- 公司层面的对外投资 → `qcc-ownership-trace` 里的 `get_external_investments`
- 个人在其他公司任职 / 历史职位的"全网"穿透 → QCC 本 skill 是按"公司+人名"双锚定;要把一个人在 N 家公司的所有数据找全,需要循环调本 skill N 次(配额谨慎)

## 调用流程

**步骤 0**:`qcc-anchor` → USCC,且**必须明确 personName**(由用户提供 / 从 `qcc-basic-profile.key_people` 自动遍历)。

**步骤 1**:把目标人物 + USCC 同时传给所有 42 个 executive tool(并行)。

### 当前数据(20 个,默认全跑)

**职务 / 关系**(6 个):
- `get_executive_positions` — 在该公司的职务
- `get_executive_legal_rep_roles` — 法代职位列表
- `get_executive_investments` — 个人对外投资
- `get_executive_controlled_companies` — 控制的企业
- `get_executive_related_companies` — 关联企业
- `get_executive_beneficial_owner` — UBO 身份(在哪些公司是 UBO)

**当前司法/失信**(14 个):
- `get_executive_admin_penalty` — 行政处罚
- `get_executive_case_filing` — 立案
- `get_executive_court_notice` — 法院公告
- `get_executive_hearing_notice` — 开庭公告
- `get_executive_dishonest` — 失信被执行
- `get_executive_equity_freeze` — 股权冻结
- `get_executive_equity_pledge` — 股权出质
- `get_executive_stock_pledge` — 股票质押
- `get_executive_exit_restriction` — 限制出境
- `get_executive_high_consumption_ban` — 限制高消费
- `get_executive_judgment_debtor` — 被执行人
- `get_executive_judicial_docs` — 司法文书
- `get_executive_pre_litigation_mediation` — 诉前调解
- `get_executive_service_notice` — 送达
- `get_executive_tax_violation` — 税收违法
- `get_executive_terminated_cases` — 终结本次执行
- `get_executive_property_reward_notice` — 财产悬赏
- `get_executive_valuation_inquiry` — 询价

### 历史数据(22 个,仅在 depth=full 时跑)

`get_executive_historical_*` 系列,字段与"当前"一一对应。还有专属于历史的:
- `get_executive_historical_partners` — 历史合伙人(P / GP)
- `get_executive_historical_legal_rep_roles` — 历史法代职位
- `get_executive_historical_positions` — 历史任职
- `get_executive_historical_investments` — 历史对外投资
- `get_executive_historical_related_companies` — 历史关联企业

## 输出契约

```yaml
person:
  name: "雷军"
  anchored_company: "小米科技有限责任公司"
  uscc: "91110108551385082Q"

current:
  positions: [...]
  legal_rep_roles: [...]
  investments: {total: int, by_status: {}, sample: [...]}
  controlled_companies: [...]
  related_companies: [...]
  ubo_in: [...]
  judicial:
    dishonest: {count, records}
    judgment_debtor: {count, records}
    high_consumption_ban: {count, records}
    exit_restriction: {count, records}
    ...

historical:                    # 仅 depth=full
  positions: [...]
  legal_rep_roles: [...]
  investments: [...]
  partners: [...]
  judicial: { ... }

risk_signals:
  - "个人在当前 25 家公司任法代" / "近 3 年涉及 2 起被执行" / ...
```

## 配额提醒

- 默认(当前 20 维度):20 次调用 / 人
- depth=full(+ 历史 22):42 次 / 人
- 如果 `qcc-basic-profile` 返回 5 个主要人员,全跑就是 100 ~ 210 次,谨慎

## 关键 flag

- 任一项 P0(失信 / 被执行 / 限消 / 限出 / 严重违法)命中 → 关键人高危
- 个人对外投资 > 30 家 → "投资专业户" / 可能是空壳
- 历史 vs 当前职位差异大 → 跳槽 / 退出可挖剧情
- 关联企业出现"已注销" / "经营异常" 集群 → 资金链断裂痕迹
