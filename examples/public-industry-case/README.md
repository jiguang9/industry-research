# 示例：协作机器人（中国）行业研究

这是一个用本 Skill 的研究流程和证据规则实际完成的公开案例，用于展示产出格式，不代表对该行业的最终或权威判断。

- 研究日期：2026-09-03，全部信息来自公开可访问的网页，未联系企业或行业协会一手核实。
- 研究深度：Quick（约 9 组搜索、9 个页面/来源）。
- `report.md`：完整报告正文，前部含五维总览表（市场/产业链/商业模式/竞争格局/趋势与风险）与"关键关系解释"一节。
- `evidence.json`：来源、主张（含五维 `dimensions` 标签）、口径、五维 `coverage` 覆盖记录、缺口的结构化记录，符合 `schema_version 1.2`（见 [../../references/evidence-schema.md](../../references/evidence-schema.md)）。
- `validation.json`：实际运行 `scripts/validate_evidence.py --report report.md` 的输出，`structural_ok: true`。
- `competitor-brief.md`：示范"用户要求继续做竞品比较"时的交接文件格式。
- `client-brief.md`：**示范文件**——本次研究的实际用途是 overview，不是 client-prep，所以这次运行本身不会产出 client-brief.md；这个文件说明如果同一份证据被用于 client-prep 场景，交接文件会长什么样，复用的是 report.md/evidence.json 中已有的证据，不是重新研究。

## v0.1.8：迁移到 schema 1.2（五维框架）

本案例最初在 v0.1.0（后经 v0.1.1—v0.1.7 多轮外部评审修复）以六模块工作流（行业地图/交易与交付/商业模式/用户与渠道/竞争结构/变化与问题）完成。v0.1.8 把研究主线统一为"定义与边界 → 五维（市场/产业链/商业模式/竞争格局/趋势与风险）→ 关系解释 → 建议"：为全部 16 条主张补充 `dimensions` 标签、新增顶层 `coverage` 五维覆盖记录、`report.md` 前部加入五维总览表、新增"关键关系解释"一节。原有 16 条主张的 `statement`、来源、`kind`、`evidence_status` 均未改动——这次迁移只是给已有证据补充维度归类和总览呈现，不是重新研究，因此不构成新的事实性变更。

同日验收复核发现行业定义卡和代表性交易在 report.md 第二、三节被压缩成了段落形式，没有逐条给出定义卡五问的实际回答，也没有走完"收费单位/交付内容/履约成本/盈利条件"这套代表性交易结构。已改为逐条列出，并新增 `G005`（记录此前一直隐性存在的缺口：具体计价方式、单价区间、交付范围本次均未获取证据；C001 的营收与销量是不同 scope 的数字，明确不能相除得出单台售价）。同时补充了 `client-brief.md` 示范文件。`assets/report-template.md` 和 `references/output-guidance.md` 已同步强化对应指引。

## 案例中记录的一次真实纠错

撰写过程中，搜索引擎对一篇财经报道的摘要把"2025年中国协作机器人市场销量约4.95万台"错误转述为约"495万台"（多了两个数量级）。通过 `WebFetch` 直接读取原文后确认正确数字是 4.95 万台，最终 `evidence.json` 采用了核实后的数字，并在 `checks.semantic_review.notes` 中记录了这次纠错过程。这也是为什么本 Skill 要求区分"仅读到搜索摘要"和"已读原文"两种来源状态（见 [../../references/evidence-rules.md](../../references/evidence-rules.md)）。

## 复现方法

```bash
python3 ../../scripts/validate_evidence.py evidence.json --report report.md
```
