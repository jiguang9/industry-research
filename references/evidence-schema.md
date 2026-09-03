# evidence.json 字段定义（schema_version 1.0）

本文件是 `evidence.json` 的完整字段参考，供撰写报告和运行 [scripts/validate_evidence.py](../scripts/validate_evidence.py) 时对照。完整可运行的示例见 `tests/fixtures/valid_evidence.json`；结构错误示例见 `tests/fixtures/invalid_*.json`。校验器实现以本文件为准，两者不一致时以校验器代码的实际行为为准并应修订本文件。

## 顶层结构

```text
{
  "schema_version": "1.0",
  "research": { ... },
  "sources": [ ... ],
  "claims": [ ... ],
  "comparisons": [ ... ],
  "gaps": [ ... ],
  "checks": { ... }
}
```

`comparisons` 和 `gaps` 在没有对应内容时可以是空数组 `[]`，不能省略字段本身。

## research（对象，必需）

| 字段 | 类型 | 说明 |
|---|---|---|
| industry | string | 行业名称，可含别名 |
| region | string | 地理范围；含"本次假设"时在 `assumptions` 中说明 |
| scope | string | 本次研究覆盖的细分范围 |
| exclusions | string | 明确排除的部分，没有则为空字符串 |
| purpose | enum | `overview` / `client-prep` / `opportunity` |
| depth | enum | `quick` / `deep` |
| research_date | string (YYYY-MM-DD) | 执行研究的日期 |
| data_cutoff | string \| null | 所引用数据的整体截止期；跨多个时期时可用文字范围描述，不明则为 `null` |
| assumptions | array of string | 本次做出的默认假设，允许为空数组 |
| status | enum | `complete` / `partial` / `insufficient_evidence` |
| capabilities | object | `{ "web_search": bool, "file_read": bool, "file_write": bool, "code_execution": bool }`，如实记录本次运行实际具备的能力 |

## sources（数组，元素必需字段见下）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 唯一 ID，建议 `S001` 递增 |
| title | string | 资料标题/名称 |
| publisher | string \| null | 发布主体，未知为 `null` |
| url | string \| null | 网页地址；用户提供的文件可为 `null` |
| file_ref | string \| null | 用户文件的相对引用或匿名标签；网页来源可为 `null` |
| source_type | enum | `official` / `company` / `association` / `research` / `media` / `public_feedback` / `user_supplied` / `other` |
| access_status | enum | `fetched`（已读原文）/ `supplied`（用户提供并已读）/ `snippet_only`（仅有搜索摘要）/ `failed`（访问失败） |
| published_at | string \| null | 资料发布日期，不明为 `null` |
| accessed_at | string (YYYY-MM-DD) | 本次访问或读取日期 |
| data_period | string \| null | 资料所述数据对应的时期，不明为 `null` |
| origin_id | string \| null | 用于把同源转载归为一组；未确认同源关系前为 `null`，不得仅凭 URL 相似猜测 |
| location | string \| null | 页码、章节、段落或表格位置 |
| excerpt | string \| null | 支持判断所需的必要短摘录，可为空 |
| access_note | string \| null | 失败原因、摘要限制等说明 |

`url` 与 `file_ref` 至少提供一个，不能同时为 `null`。

## claims（数组）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 唯一 ID，如 `C001` |
| statement | string | 主张正文 |
| kind | enum | `fact` / `inference` / `unknown` |
| evidence_status | enum | `supported` / `partial` / `conflicted` / `unverified` |
| source_ids | array of string | 引用的 `sources[].id`；`kind=unknown` 时允许为空数组 |
| counter_source_ids | array of string | 反证来源 ID，可为空数组 |
| basis_claim_ids | array of string | `kind=inference` 时引用作为前提的其他 claim id；不得形成引用环 |
| rationale | string \| null | 推断理由或置信度解释；`kind=inference` 时必须非空 |
| confidence | enum | `high` / `medium` / `low`，定性标签，不代表统计概率 |
| limitations | array of string | 已知限制，可为空数组 |
| metrics | array of metric object | 涉及数字数据时填写，无数字为空数组 |

约束（校验器会检查）：

- `kind=unknown` 时，`evidence_status` 不能为 `supported`。
- `kind=fact` 且 `evidence_status=supported` 时，`source_ids` 中至少有一个来源的 `access_status` 为 `fetched` 或 `supplied`（不能只靠 `snippet_only`/`failed` 的来源支撑一个"已证实"的事实）。
- `basis_claim_ids` 引用的 ID 必须存在于 `claims` 中，且不能形成循环引用（A 依赖 B、B 依赖 A）。

### metric 对象

| 字段 | 类型 | 说明 |
|---|---|---|
| name | string | 指标名称 |
| value | number \| {"min": number, "max": number} \| null | 数值；区间用对象；无法给出数值时为 `null` |
| unit | string | 单位 |
| period | string \| null | 数据对应时期 |
| region | string \| null | 数据对应地区 |
| scope | string \| null | 数据对应范围（行业整体/细分/单一企业等） |
| value_type | enum | `reported`（来源直接报告）/ `calculated`（对已知数字做计算）/ `estimated`（估算） |
| source_ids | array of string | 支持该数字的来源 ID |
| missing_dimensions | array of string | 缺失的口径维度，例如 `["region", "unit"]`；无缺失为空数组 |
| currency | string \| null | 涉及货币时填写（如 `CNY`、`USD`） |
| price_basis | string \| null | 涉及实际/名义价格时填写 |
| method | string \| null | `value_type` 为 `calculated`/`estimated` 时必须说明计算方法 |
| inputs | array of string | `calculated`/`estimated` 时列出输入数据来源（可引用其他 claim/metric） |
| assumptions | array of string | `calculated`/`estimated` 时列出计算假设 |

## comparisons（数组，可为空）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 唯一 ID，如 `CMP001` |
| metric_refs | array of string | 格式 `"<claim_id>.<metric_index>"`，例如 `"C002.0"`，指向具体 claim 下 metrics 数组中的某一项 |
| purpose | string | 比较目的说明 |
| comparable | boolean | 是否认为这组数字在关键口径上可比 |
| mismatched_dimensions | array of string | 不一致的口径维度；`comparable=true` 时应为空数组 |
| adjustment_note | string \| null | 如做过单位换算等调整，说明换算过程；未做调整为 `null` |

## gaps（数组，可为空）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 唯一 ID，如 `G001` |
| description | string | 缺口描述 |
| affected_claim_ids | array of string | 受影响的主张 ID，可为空数组 |
| next_step | string | 建议的下一步查证动作 |

## checks（对象）

| 字段 | 类型 | 说明 |
|---|---|---|
| semantic_review | object | `{ "performed": bool, "notes": string }`，记录研究者是否做过人工语义复核 |
| machine_validation | object | `{ "performed": bool, "tool": string, "tool_version": string \| null, "result": "passed" \| "passed_with_warnings" \| "failed" \| null }` |

`semantic_review` 和 `machine_validation` 互不替代：机器校验只检查结构和已声明的一致性，不证明网页内容真实、不证明引用真的支持原句、不穷尽正文所有数字，也不证明行业结论正确。
