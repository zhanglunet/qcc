---
name: qcc-ipr-portfolio
description: |
  企查查"知识产权 + 数字资产"工作流。聚合:专利(国内/国际) / 商标 / 著作权(作品+软件) / 集成电路布图 / 知产质押 / 标准 / 商业特许 / ICP 互联网服务 / App / 小程序 / 网店 / 公众号 / 微博 / 抖音 / 快手。
  适用于科技尽调 / 投前技术评估 / 反不正当竞争分析 / 商标抢注监测 / 渠道资产盘点 / 自媒体矩阵审计。
  IF user asks for 专利 / 商标 / 著作权 / IP 资产 / 数字资产 / 公众号矩阵 / 小程序 / App of a Chinese company, THEN this skill.
  Triggers: "...有多少专利", "查一下商标", "数字资产清单", "自媒体矩阵", "ICP 备案", "...的小程序"
  NOT for: 跨境海外专利单独核查(本 skill 只覆盖 QCC 的"国际专利"维度,不含 USPTO 等原始库).
---

# qcc-ipr-portfolio — 知识产权 + 数字资产清单

## 何时用

- 投前技术 / IP 尽调:专利 / 商标 / 软著 量化
- 商标 / 商号抢注监测
- 内容公司 / DTC 公司的"自媒体矩阵 + 渠道资产"盘点
- 反不正当竞争 / 商业秘密案件举证准备
- 看一家公司的"数字门面"完整度

## 不用的场景

- 想看专利原文 / 权利要求 → 走国家知识产权局 / Google Patents
- 海外商标(欧盟 / 美国 / 日本)细查 → 用 TMview / USPTO

## 调用流程

**步骤 0**:`qcc-anchor` → USCC

**步骤 1-18**(全部并行,USCC 作 `searchKey`)。

### IP 核心(8 个)

| tool | 维度 |
|---|---|
| `get_patent_info` | 国内专利(发明 / 实用新型 / 外观) |
| `get_international_patent` | 国际专利(PCT / 各国授权) |
| `get_integrated_circuit_layout` | 集成电路布图设计 |
| `get_trademark_info` | 商标注册(45 类) |
| `get_trademark_document` | 商标文档 / 异议 / 撤三 / 转让 |
| `get_copyright_work_info` | 作品著作权(美术 / 文字 / 摄影 / 视听等) |
| `get_software_copyright_info` | 软件著作权 |
| `get_ipr_pledge` | 知产质押 / 出质登记 |

### 标准 / 资质(2 个)

| tool | 维度 |
|---|---|
| `get_standard_info` | 国家 / 行业 / 团体标准参与情况 |
| `get_commercial_franchise` | 商业特许经营备案 |

### 数字资产(8 个)

| tool | 维度 |
|---|---|
| `get_internet_service_info` | ICP / 互联网信息服务备案 |
| `get_app_info` | App 备案 / 上架信息 |
| `get_mini_program` | 小程序(微信 / 支付宝 / 抖音 / 百度 等) |
| `get_online_store` | 电商网店(天猫 / 京东 / 拼多多 / 抖店 等) |
| `get_wechat_official_account` | 微信公众号矩阵 |
| `get_weibo_account` | 微博账号 |
| `get_douyin_account` | 抖音账号(含蓝V) |
| `get_kuaishou_account` | 快手账号 |

## 输出契约

```yaml
ip_core:
  patents:                   # 国内
    total: int
    by_type: {发明: int, 实用新型: int, 外观: int}
    sample: [...]
  international_patents: {total, sample}
  trademarks:
    total: int
    by_class: {01: int, ..., 45: int}
    sample: [...]
  copyrights:
    works: {total, sample}
    software: {total, sample}
  ic_layouts: {total, sample}
  ipr_pledge: {records: []}

standards: {total, sample}
franchise: {records: []}

digital:
  icp: [...]
  apps: [...]
  mini_programs: [...]
  online_stores: [...]
  social:
    wechat_oa: []
    weibo: []
    douyin: []
    kuaishou: []

flags:
  - "..."   # 例如:近 12 个月商标异议突增 / ICP 备案与官网域名不一致 / 公众号矩阵未实名匹配
```

## 实用 flag

- 自媒体账号在 QCC 库的"主体名"与公司名称不一致 → 可能是关联人个人持有,合规上拉清单
- ICP 备案域名与官网域名不一致 → 主体迁移痕迹
- 商标量 ≫ 专利量(品牌驱动型);专利量 ≫ 商标量(技术驱动型);两者都少 → 轻资产 / 早期
- "知产质押"非零 → 资金链可能紧张
