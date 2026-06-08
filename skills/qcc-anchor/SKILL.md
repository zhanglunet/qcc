---
name: qcc-anchor
description: |
  企查查实体锚定。把用户输入的企业名 / 简称 / 品牌名 / 股票简称解析成唯一的统一社会信用代码 (USCC)。
  所有其他 qcc-* skill 的强制前置步骤 — 锚定后再用 USCC 调下游工具,避免重名 / 同名子公司误查。
  IF user pastes a Chinese company name and needs any QCC lookup, THEN run this first.
  Triggers: "锁定主体", "确认公司", "这家公司全称", "找一下 XXX 公司".
  NOT for: user already pastes an 18-char USCC (skip directly to downstream skill).
---

# qcc-anchor — 企查查实体锚定

## 何时用

- 任何 QCC 调用前,**只要用户给的不是 18 位 USCC**,都先跑本 skill
- 用户输入是企业简称 / 品牌名 / 股票简称 / 容易重名的全称(如"小米科技""阿里巴巴")
- 之前调用某个工具返回"无匹配" — 用本 skill 反向锁定再重试

## 不用的场景

- 用户已经给出 18 位 USCC(如 `91110108551385082Q`)→ 跳过,直接调下游
- 用户只是问元信息(QCC 本身怎么用) → 不用 skill

## 调用流程

1. 调 `qcc-company:get_company_by_query`,`searchKey` = 用户输入原文
2. 看返回的 **匹配结果** 字段:
   - **唯一精确匹配** → 取 `企业信息.统一社会信用代码`,继续下游
   - **多候选** → **必须**把候选清单完整展示给用户,等用户明确选定后才继续。**禁止**自动选第一个
   - **未匹配** → 提示用户检查拼写,或换关键词(品牌名 / 简称)重试
3. (可选)拿到 USCC 后,如果需要二次核验"名称-USCC 是否匹配",调 `qcc-company:verify_company_accuracy`

## 用到的 tool

| tool | server | 输入 | 用途 |
|---|---|---|---|
| `get_company_by_query` | company | searchKey | 模糊匹配 → 唯一/候选/未匹配 |
| `verify_company_accuracy` | company | searchKey + companyName | 二要素核验(可选) |

## 调用示例

```bash
# 锚定阶段
qcc-py call company get_company_by_query -a '{"searchKey":"小米科技"}'
# → 返回唯一匹配 USCC: 91110108551385082Q

# 后续调用全部用 USCC
qcc-py call company get_company_registration_info -a '{"searchKey":"91110108551385082Q"}'
```

## 输出契约

```json
{
  "anchor_status": "unique | multi_candidate | no_match",
  "uscc": "91110108551385082Q",
  "canonical_name": "小米科技有限责任公司",
  "candidates": [ /* multi_candidate 时填,最多 5 条 */ ]
}
```
