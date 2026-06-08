---
name: qcc-basic-profile
description: |
  企查查"工商基础摘要"工作流。一次性拉齐:登记信息 / 简介 / 联系方式 / 主要人员 / 税务发票 / 分支机构 / 上市信息 / 年报(社保人数)。
  适用于 KYB 初步、立项尽调前置、法务对接资料、合同/发票主体校验、供应商入库审核。
  IF user asks for 工商信息 / 基础尽调 / KYB 摘要 / 注册信息 / 公司概况 of a specific Chinese company, THEN this skill.
  Triggers: "查...的工商信息", "做基础尽调", "拉 KYB 摘要", "看下这家公司的注册资本", "...的法定代表人是谁".
  NOT for: 股权穿透 (→ qcc-ownership-trace) / 司法风险 (→ qcc-risk-screen) / 个人背调 (→ qcc-executive-background).
---

# qcc-basic-profile — 工商基础摘要

## 何时用

- 第一次接触某家公司,需要 5 分钟内了解概貌
- 给合同 / 招标 / 入库 / 法务对接 准备资料
- 校验对方提交的"营业执照副本扫描件"信息真伪
- 把多个工商字段(8 个 tool)一次性聚合,免去逐字段逐工具调用

## 不用的场景

- 只是想知道一个具体字段(如法定代表人) → 可以直接调 `qcc-company:get_company_registration_info`
- 需要历史变更轨迹 → 用 `qcc-ownership-trace`(里面会调 `get_change_records`)
- 需要司法 / 失信 / 限消查询 → 用 `qcc-risk-screen`

## 调用流程

**步骤 0**(如用户输入非 USCC):走 `qcc-anchor` 拿到 USCC。

**步骤 1-8**(均以 USCC 作 `searchKey`,可并行):

| 序 | tool | 输出字段(节选) | 用途 |
|---|---|---|---|
| 1 | `get_company_registration_info` | 法代 / 注册资本 / 实缴 / 类型 / 注册地址 / 经营范围 / 登记机关 | **核心** — 唯一不能省 |
| 2 | `get_company_profile` | QCC 自有简介 + 行业归类 | 业务一句话理解 |
| 3 | `get_contact_info` | 电话 / 邮箱 / 网址列表(含 ICP) | 客服 / 法务 / BD 对接 |
| 4 | `get_key_personnel` | 董事 / 监事 / 经理 / 财务负责人 | 看治理结构 |
| 5 | `get_tax_invoice_info` | 纳税人识别号 / 开户行 / 账号 | 开发票 / 转账校验 |
| 6 | `get_branches` | 分支机构(存续 / 注销 / 负责人 / 地区) | 看实际经营布局 |
| 7 | `get_listing_info` | A股 / 港股 / 美股 / 新三板 | 看是否上市 / 上市主体 |
| 8 | `get_annual_reports` | 历年年报(社保人数 / 联系信息历史) | **人员规模趋势** + 自报口径 |

## 输出契约

```yaml
basic_info: {法定代表人, 注册资本, 实缴, 成立日期, 登记状态, 企业类型, 经营期限, 国标行业}
profile:     {简介, QCC 行业归类}
addresses:   {注册地址, 通信地址, 登记机关}
contacts:    {电话: [...], 邮箱: [...], 网址: [...]}
key_people:  [{姓名, 职务, 持股}]
tax:         {纳税人识别号, 开户行, 账号, 纳税人资质}
branches:    {存续: [...], 注销: [...]}
listing:     null | {上市地, 代码, 简称}
annual:      {社保趋势: [{年度, 人数}], 资产负债: [企业是否公示]}
```

## 注意

- 母公司常常把"营业总收入 / 利润 / 资产"选择不公示,如需财务数字优先用 `qcc-operation-pulse`(融资 / 招标 / 资质)或外部审计报告
- 大公司的"参保人数"是单体母公司口径,**不代表集团总人数**(子公司各自单算)
