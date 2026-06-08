---
name: qcc-person-portfolio
description: |
  给一个自然人姓名(中文董监高 / 法代 / 实控人),反查他在企查查全库里"作为董监高 / 法定代表人 / 控制企业 / 关联企业"的所有公司,合并去重导出 Excel。
  适用于:投资人 / 创始人对外版图摸底 / KOL 商业关联面排查 / 大股东实际能调动多少法人主体 / 关键人离职前关联资产盘点。
  IF user asks for "查 XXX 的所有公司" / "他在哪些公司任职 / 担任董监高" / "他控制了多少家公司" / "导出 XXX 的关联企业到 Excel", THEN this skill.
  Triggers: "查...所有公司", "...担任董监高的公司", "...控制了哪些企业", "...的对外任职清单", "导出某个人的关联公司", "...的法人版图"
  NOT for: 公司主体的尽调(→ qcc-basic-profile / qcc-ownership-trace); 同一个人在某 1 家公司的全维度风险(→ qcc-executive-background, 含司法历史等 42 维度)
---

# qcc-person-portfolio — 自然人对外公司清单(反查)

## 何时用

- 重要自然人(创始人 / 投资人 / 实控人 / 大股东)的"对外版图"摸底
- 客户 / 投后 / 上下游尽调时需要看"这个人的法人能量"
- 关键人离职 / 跳槽前的关联资产清单
- KOL / 公众人物的商业关联面排查
- 一次性导出 Excel 给业务 / 法务 / 投资团队传阅

## 不用的场景

- 只关心他在某 1 家公司的风险细节(失信 / 限消 / 被执行等) → `qcc-executive-background`
- 想看一家公司有谁是董监高 → `qcc-basic-profile` 里的 `get_key_personnel`
- 想要他全网穿透到没列名的代持 / 信托 → QCC 不到,需要外部数据源

## 调用流程

```
[人名输入]
   ↓
[Step 1] qcc-company:get_company_by_query
   ↓  查"已知关联公司"或品牌名(必要时让用户给 anchor)
[USCC anchor]   ←  避免同名误锁
   ↓
[Step 2] 并行调 qcc-executive 6 个 tool, 都用 (anchor_uscc, person_name) 入参:
   - get_executive_positions                  ← 当前董监高任职
   - get_executive_historical_positions       ← 历史董监高任职
   - get_executive_legal_rep_roles            ← 当前法定代表人
   - get_executive_historical_legal_rep_roles ← 历史法定代表人
   - get_executive_controlled_companies       ← 控制企业(可能截断 100 条)
   - get_executive_related_companies          ← 全部关联企业
   ↓
[Step 3] Python 脚本合并去重 → 8 sheet xlsx
   ↓
[Step 4] 输出到指定路径
```

## anchor 怎么找

一句话:**用这个人公开任过法代或董事的任何一家公司就行**。anchor 的唯一作用是消除同名歧义。

实操:
1. 谷歌 / 百科 / 招股书 / 财报里搜这个人最有名的关联公司(创始公司 / 上市公司 / 基金主体均可)
2. 先 `qcc-company:get_company_by_query` 模糊查那家公司
3. 在返回的候选列表里挑"法定代表人 = 目标人物"的那一条,取 USCC

**示例**:雷军 → 用 "小米" 模糊查 → 候选里"小米科技有限责任公司" 法代是雷军 → USCC `91110108551385082Q` 即可

## 怎么跑

```bash
# 前置:配好 QCC_API_KEY(参考仓库根 README "0. 配 API Key")
cd qcc/python && source .venv/bin/activate
pip install -e ".[skills]"   # 装 openpyxl

# 模式 A:已知 anchor USCC(最快)
python ../skills/qcc-person-portfolio/run.py \
  --person "雷军" \
  --anchor 91110108551385082Q \
  --out ./雷军_companies.xlsx

# 模式 B:让脚本自动 anchor(用公司名)
python ../skills/qcc-person-portfolio/run.py \
  --person "雷军" \
  --anchor-by-name "小米科技"
```

跑完打开 xlsx,8 个 sheet:
- **说明** — 元数据 + sheet 索引 + 截断提示
- **汇总(去重)** — 按公司名称去重的主表
- 当前董监高任职 / 历史董监高任职 / 当前法定代表人 / 历史法定代表人 / 控制企业 / 关联企业 — 各源原始数据

## 输出契约

xlsx 主表(`汇总(去重)`)字段:

| 列 | 说明 |
|---|---|
| 企业名称 | 唯一键(去重维度) |
| 出现的来源 | 该公司在哪几个 sheet 命中(如 "当前董监高任职 / 控制企业") |
| 职位 / 角色 汇总 | 跨 sheet 合并的角色集合 |
| 持股比例 / 状态 / 地区 / 行业 / 成立日期 / 注册资本 | 取最先非空的那次 |

## 已知坑

1. **controlled_companies 截断**:QCC 工具单次只回前 100 条;数据多的人会丢。`run.py` 会自动检测并在"说明"sheet 标 ⚠️
2. **anchor 错了**:如果 anchor 公司里这个人不是法代/董监高,executive 工具仍可能返回数据(QCC 不强校验),但**同名风险**会上来 — 务必 anchor 到他实名挂法代的主体
3. **配额**:本 skill 单次 7 个调用(1 anchor + 6 fetch),免费 key 一天约能跑 几十个人;批量跑前先看 dashboard
4. **结束时间**:`任职起止时间` 里 `结束时间:[]` 表示"未离任 / 当前在任"
5. **境外主体不在内**:港股 / 美股上市的开曼 / VIE 主体不在 QCC 工商数据,只能查境内 OpCo

## 关联 skill

- 想顺手补"他的个人司法风险"(限消 / 失信 / 被执行 / 限出) → 用 `qcc-executive-background` 把同样的 (USCC, person_name) 喂进去
- 想看其中某家有疑问公司的完整工商 → 把该公司 USCC 喂给 `qcc-basic-profile`
- 想看其中某家有疑问公司的股权穿透 → 喂给 `qcc-ownership-trace`
