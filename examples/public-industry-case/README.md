# 示例：协作机器人（中国）行业研究

这是一个用本 Skill 的研究流程和证据规则实际完成的公开案例，用于展示产出格式，不代表对该行业的最终或权威判断。

- 研究日期：2026-09-03，全部信息来自公开可访问的网页，未联系企业或行业协会一手核实。
- 研究深度：Quick（约 9 组搜索、9 个页面/来源）。
- `report.md`：完整报告正文。
- `evidence.json`：来源、主张、口径、缺口的结构化记录，符合 `schema_version 1.1`（见 [../../references/evidence-schema.md](../../references/evidence-schema.md)）。
- `validation.json`：实际运行 `scripts/validate_evidence.py --report report.md` 的输出，`structural_ok: true`。
- `competitor-brief.md`：示范"用户要求继续做竞品比较"时的交接文件格式。

## 案例中记录的一次真实纠错

撰写过程中，搜索引擎对一篇财经报道的摘要把"2025年中国协作机器人市场销量约4.95万台"错误转述为约"495万台"（多了两个数量级）。通过 `WebFetch` 直接读取原文后确认正确数字是 4.95 万台，最终 `evidence.json` 采用了核实后的数字，并在 `checks.semantic_review.notes` 中记录了这次纠错过程。这也是为什么本 Skill 要求区分"仅读到搜索摘要"和"已读原文"两种来源状态（见 [../../references/evidence-rules.md](../../references/evidence-rules.md)）。

## 复现方法

```bash
python3 ../../scripts/validate_evidence.py evidence.json --report report.md
```
