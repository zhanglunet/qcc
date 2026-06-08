---
name: qcc-operation-pulse
description: |
  企查查"经营动态 + 资质 + 招投标 + 融资 + 舆情"工作流。35 个维度:行政许可 / 电信牌照 / 食品安全 / 游戏审批 / 广告审查 / 资质荣誉 / 评级 / 信用承诺 / 科技成果 / 招投标 / 招聘 / 融资 / 融资租赁 / 投资机构 / 私募管理人 / 舆情 / 公告 / 政府公告 / 政府约谈 / 假冒化妆品 / 产品召回 / 抽检 / 软件违规 / 拒之门外 / 土地出让 / 资产拍卖 / 排名榜单 等。
  适用于深度尽调 / 投后跟踪 / 行业洞察 / 招标准入 / 合规审查 / 信用画像。
  IF user asks for 资质 / 招投标 / 招聘 / 融资 / 舆情 / 资质牌照 / 评级 / 抽检 / 政府公告 of a Chinese company, THEN this skill.
  Triggers: "有什么资质", "中标记录", "招聘情况", "融资历史", "舆情", "牌照", "评级", "近期动态", "招了多少人"
  NOT for: 司法风险(走 qcc-risk-screen);专利商标(走 qcc-ipr-portfolio);股权(走 qcc-ownership-trace).
---

# qcc-operation-pulse — 经营动态与资质画像

## 何时用

- 投后跟踪:招聘 / 融资 / 中标 / 舆情 / 监管动态
- 招标准入:对方资质 / 信用评级 / 历史中标
- 合规审查:许可证 / 牌照 / 抽检 / 召回 / 政府约谈
- 行业洞察:某家公司的资质组合反推业务边界

## 不用的场景

- 单点查"有没有 ICP 备案" → 用 `qcc-ipr:get_internet_service_info`
- 单点查"近半年有没有融资" → 直接调 `qcc-operation:get_financing_records`
- 司法/失信 → `qcc-risk-screen`

## 调用流程

**步骤 0**:`qcc-anchor` → USCC

**6 个子组**(全部并行,USCC 作 `searchKey`):

### A. 资质 / 许可(8 个)

| tool | 维度 |
|---|---|
| `get_qualifications` | 综合资质 |
| `get_administrative_license` | 行政许可 |
| `get_taxpayer_qualification` | 纳税人资质 / 一般 vs 小规模 |
| `get_telecom_license` | 电信业务许可证(ICP/EDI 等) |
| `get_food_safety` | 食品安全许可 |
| `get_game_approval` | 游戏版号 |
| `get_advertising_review` | 广告审查 |
| `get_import_export_credit` | 进出口信用 |

### B. 荣誉 / 评级(6 个)

| tool | 维度 |
|---|---|
| `get_honor_info` | 行业 / 政府荣誉 |
| `get_ranking_list_info` | 各类排名榜单(《财富》/ 行业 / 区域) |
| `get_credit_evaluation` | 综合信用评级 |
| `get_credit_commitments` | 信用承诺 |
| `get_tech_achievement` | 科技成果转化 |
| `get_random_check` | 双随机抽查结果 |

### C. 市场动态(5 个)

| tool | 维度 |
|---|---|
| `get_bidding_info` | 中标 / 招标记录 |
| `get_recruitment_info` | 招聘岗位(规模 + 方向) |
| `get_financing_records` | 融资轮次 / 估值 / 投资方 |
| `get_financing_lease_info` | 融资租赁 |
| `get_investment_institution` | 投资机构(若本主体是 VC/PE) |
| `get_private_fund_manager` | 私募基金管理人(中基协备案) |

### D. 舆情 / 公告(5 个)

| tool | 维度 |
|---|---|
| `get_news_sentiment` | 媒体新闻 + 情感倾向 |
| `get_company_announcement` | 企业自身公告 |
| `get_government_announcement` | 政府对该主体的公告 |
| `get_related_announcement` | 关联公告 |
| `get_government_interview` | 政府约谈(预警信号) |

### E. 负面 / 合规(6 个)

| tool | 维度 |
|---|---|
| `get_counterfeit_cosmetics` | 假冒化妆品(化妆品行业) |
| `get_product_recall` | 产品召回 |
| `get_product_spot_check` | 产品抽检 |
| `get_software_violation` | 软件违规通报 |
| `get_entry_denied` | 拒之门外(入境 / 注册等) |
| `get_spot_check_info` | 抽检详情 |

### F. 资产 / 交易(4 个)

| tool | 维度 |
|---|---|
| `get_land_grant_info` | 土地出让(获取土地) |
| `get_land_transfer_info` | 土地转让 |
| `get_asset_auction` | 资产拍卖(非司法) |
| `get_property_rights_transaction` | 产权交易 |

## 输出契约

```yaml
qualifications: {licenses: [...], counts_by_type: {}}
honors:         {records: [...], ranking_appearances: [...]}
market:         {bids: [...], hires: [...], financing: [...]}
sentiment:      {news: [...], net_sentiment_30d: float, alerts: [...]}
negative:       {recalls: [...], spot_check_fails: [...], govt_interviews: [...]}
assets:         {land: [...], auctions: [...]}
key_signals:    [...]    # Agent 速读
```

## 关键信号速读

- 近 12 个月融资 ≥ 1 笔 → 资金活跃
- 招聘岗位 ≥ 50 个 / 含"AI / 算法 / 大模型 / 新能源" → 业务方向信号
- 政府约谈 > 0 → **重要预警**,几乎一定影响后续合作
- 产品召回 / 抽检不合格 > 0 → 质量风险
- 中标记录密集(政府客户) → ToG 型企业
- 信用评级低或下调 → 准入门槛卡点
