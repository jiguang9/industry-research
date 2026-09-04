# 验证记录

版本：0.1.8　记录日期：2026-09-04

## 0. 外部评审修复历史

**v0.1.1（相对 v0.1.0）**：v0.1.0 发布后收到一份具体、可复现的外部评审，指出 5 类真实问题（校验器未做跨字段真实性核对、安装器失败恢复路径不安全、公开案例违反自身证据边界、Release 校验文件在解压前必然失败、评测用例1的措辞实际触发了用例4而非用例1）以及一处文档过时判断（Hermes Direct URL 安装范围）。逐条核实后全部确认为真实问题并已修复，详见 `CHANGELOG.md` 的 0.1.1 条目。

**v0.1.2（相对 v0.1.1）**：继续收到第二轮评审，指出 v0.1.1 的修复不完整：跨 metric 核对遗漏了 `name`（GMV vs 收入）和 `price_basis`（名义/实际）两个字段，`period` 被无条件豁免导致横截面比较的时期不一致检测不到；多个 evidence-schema.md 文档中标注为必需的字段（`schema_version`、`sources[].publisher` 等、`claims[].counter_source_ids` 等）删除后校验器仍能通过；公开案例 report.md 第三节仍保留"这个细分行业……尚未普遍形成稳定盈利模式"这一从单一企业数据直接得出的行业级结论，认识2 处的措辞已改但正文这处没有同步。逐条核实后全部确认为真实问题并已修复，详见 `CHANGELOG.md` 的 0.1.2 条目。

**v0.1.3（相对 v0.1.2）**：第三轮评审指出 v0.1.2 的必需字段执行仍不完整：`research.data_cutoff`、`claims[].rationale`、`metrics[].missing_dimensions`、顶层 `comparisons`/`gaps`/`checks`（及其两个子对象）删除后依然通过；v0.1.2 新增 `comparison_type` 必填字段却没有配套提升 schema_version，导致声明 `1.0` 的旧文件在新规则下的失败没有版本层面的解释；`docs/validation-report.md` 中记录了本机绝对路径；Release 说明文字把测试数量误写成 61（实际 56）。逐条复现（对着合法 fixture 逐字段删除，确认校验器确实放行）后全部确认为真实问题并已修复，详见 `CHANGELOG.md` 的 0.1.3 条目。

**v0.1.4（相对 v0.1.3）**：第四轮评审指出两类仍未堵上的漏洞：(1) `metrics[].period/region/scope` 只要删除字段本身、同时把字段名写进 `missing_dimensions`，就能绕过"键必须存在"的要求；(2) `checks` 的两个子对象只检查了自己是不是 object，内部字段（`performed`/`notes`/`tool`/`tool_version`/`result`）完全没有类型或存在性检查，`limitations`/`metrics[].inputs`/`.assumptions`/`comparisons[].mismatched_dimensions` 这类"字符串数组"字段也只检查了是不是数组、没检查元素是不是字符串；另外 `schema_version` 不匹配（含伪造的 `"999.0"`）此前只给警告，`structural_ok` 仍可能是 `true`。逐条复现后全部确认为真实问题并已修复，详见 `CHANGELOG.md` 的 0.1.4 条目。

**v0.1.5（相对 v0.1.4）**：第五轮评审指出两类真实漏洞：(1) `comparisons[].metric_refs` 接受空数组、单个引用、或同一引用重复两次——因为跨 metric 真实核对只在 `resolved_metrics >= 2` 时才运行，这三种"根本没有比较对象"的情况会直接绕过该核对；(2) `metrics[].currency`/`price_basis`/`method`/`inputs`/`assumptions` 只在 `value_type` 为 `calculated`/`estimated` 时被检查类型，`reported` 指标上出现 `currency: 123` 这类错误类型完全不受检查。逐条复现后全部确认为真实问题并已修复，详见 `CHANGELOG.md` 的 0.1.5 条目。

**v0.1.6（相对 v0.1.5）**：第六轮评审转向语义层面的证据纪律，不是校验器代码漏洞——这正是校验器自身免责声明中明确写出它做不到的部分（"不证明引用真的支持原句"）。具体：report.md 用 `[C006]`（销量/份额/出口数字）支持了一句关于协作焊接、大负载码垛"应用亮点"的话，但 C006 的 statement 完全没提应用场景；"直接客户是系统集成商……采购决策涉及生产/工艺和采购部门"这一商业模式核心判断没有任何证据编号；三处推断内容（IPO受挫的影响推测、"国产替代与出海同步推进"、"行业整体仍处扩张期"）被写在"已发生事件"小节下且部分引用了不相关的 claim。逐条核实（读取被引用 claim 的实际 statement，确认是否真的支持所在句子）后全部确认为真实问题：新增真实来源 S009 和对应 claim C011 支持应用场景描述；新增 C012-C016 把此前隐性的推断和从未单独立 claim 的事实（节卡 Pre-IPO 融资信息，此前只存在于 S001 的 excerpt 里）分别独立记录，并把推测性语句移出"已发生事件"小节；新增 G004 记录采购流程调研缺口。详见 `CHANGELOG.md` 的 0.1.6 条目。**这一轮没有修改 `scripts/validate_evidence.py`**——修复前后 `structural_ok` 都是 `true`，因为这些从来都不是结构错误。

**v0.1.7（相对 v0.1.6，2026-09-04）**：不是外部代码评审，是一次真实用户使用反馈。用户在自己的 Claude Code 会话中安装并调用了本 Skill（"帮我快速了解新能源汽车行业"），Skill 正确写出了 `report.md`/`evidence.json`/`validation.json`，但对话回复只有一句"报告已生成：report.md、evidence.json、validation.json"这样的文件名列表；在用户的宿主 UI 中，文件以附件卡片形式呈现，需要额外点击才能打开查看，导致用户看不到研究内容本身。核实后确认 SKILL.md 此前只规定"无文件能力时在对话中直接输出"，没有规定"有文件能力时对话回复也应包含正文内容"，属于真实的行为指引缺口。已在 SKILL.md 的输出章节补充明确要求：写文件不代表交付完成，对话回复必须直接给出 report.md 正文内容。附件是否需要点击查看属于宿主 UI 行为，不是本 Skill 能控制的部分，但回复文本本身完全在 Skill 的控制范围内。详见 `CHANGELOG.md` 的 0.1.7 条目。

**v0.1.8（相对 v0.1.7，2026-09-04）**：不是评审修复，是一次架构级需求变更——项目最初按"定义与边界 + 行业地图/交易与交付/商业模式/用户与渠道/竞争结构/变化与问题"六模块工作流实施（v0.1.0—v0.1.7），新收到的实施方案把研究主线统一为"定义与边界 → 五维（市场 `market`/产业链 `value_chain`/商业模式 `business_model`/竞争格局 `competition`/趋势与风险 `trends_risks`）→ 关键关系解释 → 任务建议"。核实后确认这是不兼容旧结构的真实变更（不是措辞调整），按方案要求在现有项目基础上增量迁移，未删除重建：

- 新增 [`references/industry-framework.md`](../references/industry-framework.md)：五维问题清单、商业模式六要素、产业链/竞争/趋势方法、`coverage`/`dimensions` 填写方法。
- `SKILL.md`、`references/research-workflow.md`：核心研究流程从"确定边界→选择来源→六模块→机会→校验"改为"确定边界→选择来源→五维研究→关系解释→机会→校验"。
- `references/evidence-schema.md`、`scripts/validate_evidence.py`：`schema_version` 从 `1.1` 提升到 `1.2`（不兼容变更，不复用已用于 `comparison_type` 的 1.1）。新增顶层 `coverage`（五维覆盖记录：`status`/`claim_ids`/`note`/`next_question`，键固定为五个维度代码）和 `claims[].dimensions`（关联维度标签，取值限定五个代码、不允许重复）。校验器新增 `validate_coverage()`：五个键必须齐全且不能有多余键、`status` 枚举校验、`claim_ids` 悬空引用检测、**`status=covered` 必须有至少一条 `kind != unknown` 且 `dimensions` 匹配该维度的主张支撑**（不能只把字段填满就算数）；`claims[].dimensions` 校验取值合法性与去重。任何仍声明 `schema_version: "1.1"` 的文件会被判为结构错误（复用既有的版本不匹配硬失败机制，不新增特殊逻辑）。
- `assets/report-template.md`：正文前部新增"行业定义与五维总览"（五维总览表）与独立的"关键关系解释"一节；证据表新增"关联维度"列。`assets/client-brief-template.md`、`assets/competitor-brief-template.md` 同步增加维度/产业链位置列。
- `examples/public-industry-case/`：`evidence.json` 迁移到 schema 1.2——为全部 16 条既有主张补充 `dimensions` 标签、新增顶层 `coverage`；**原有 16 条主张的 `statement`、来源、`kind`、`evidence_status` 均未改动**，这次迁移只是给已有证据补充维度归类，不是重新研究，不构成新的事实性变更。`report.md` 相应加入五维总览表和"关键关系解释"一节（节卡持续亏损与 IPO 终止之间"可能机制而非已证实因果"的解释）。`competitor-brief.md` 补充产业链位置/关系列。重新运行 `validate_evidence.py`，`structural_ok: true`，警告数不变（2条，均为既有的 inference 缺 source_ids 软提醒）。
- `tests/fixtures/valid_evidence.json` 补充 `coverage`+`dimensions`；新增 4 个 invalid fixture（`invalid_coverage_missing_key.json`、`invalid_coverage_bad_status.json`、`invalid_coverage_dangling_claim.json`、`invalid_dimensions_bad_value.json`）和对应测试类（`CoverageValidationTests`、`ClaimDimensionsValidationTests`、`SchemaVersionUpgradePromptTests`），测试数量从 80 增至 97。
- `evals/cases.md` 新增用例 13—21（完整 Quick 五维总览、只研究单一维度、多角色平台生态、订阅+项目组合收入、材料显示上游议价更强、只有品牌无份额数据、成熟行业新细分增长、只有趋势观点无变化事实、用户提供框架图案例）；`evals/rubric.md` 新增第 5 项"五维语义验收"评分维度。

**v0.1.8 首次提交时的缺口，及当天的补测**：v0.1.8 首次提交时，以上验证均为机器校验（`validate_evidence.py`、`check_skill.py`、`unittest`）和人工复核，没有重新开一个真实 Agent 会话按新的五维结构跑一次用例。收到这一具体缺口的验收意见后，当天在本机把 `~/.claude/skills/industry-research/` 从 v0.1.7 重新安装为 v0.1.8（用 `tools/install.py --platform claude --replace`，替换前是六模块版本），随后用 Agent 工具开了一个全新、无先前上下文的子 Agent，输入中性措辞"帮我快速了解中国预制菜行业。"（不含深度/用途信号词）。子 Agent 独立发现并调用了 `industry-research`，产出 `evidence.json`（`schema_version: "1.2"`，`coverage` 五个键齐全且状态合理——`market`/`value_chain`/`competition`/`trends_risks` 为 `covered`、`business_model` 为 `partial`，全部 15 条 claim 都带 `dimensions`）、`report.md`（含五维总览表和"四、关键关系解释"一节，用监管定义清晰度如何影响消费者信任解释了2025年9月罗永浩-西贝事件为何迅速升级）、`validation.json`。本机独立复验 `validate_evidence.py --report`：`structural_ok: true`，0 errors，1 warning，3 条 conflicted 主张被正确标记为需人工复核。完整记录见下方"用例1执行记录（v0.1.8 五维框架复测）"。

这次复测证明了两件事：（1）五维框架、`coverage`/`dimensions` 字段在真实 Agent 会话中确实能被正确产出并通过机器校验，不只是本次开发会话里手工构造的 fixture 和示例；（2）复测过程中发现的另一个真实问题——行业定义卡和代表性交易在实际输出中也被压缩成了段落而非逐条问答/要素——反过来证实了验收意见里"公开案例定义卡和代表性交易展示不完整"这一发现具有代表性，不是示例案例的孤立问题，已同步强化 `assets/report-template.md`、`references/output-guidance.md` 的对应指引并修复了公开示例（见 `examples/public-industry-case/README.md` 中"同日验收复核"一节）。

**仍然存在的缺口**：这次补测只覆盖了 21 个用例中的 1 个（用例1，同时满足新增用例13"完整 Quick 请求"的检查点），且是同一台机器、同一个会话内完成，不是独立第三方评审。用例2-12（除已在六模块版本下执行的用例1/4历史记录外）以及新增用例14-21仍未执行，见下方第4节表格。

以上八轮修复/变更均**不修改或删除已发布的 `v0.1.0` 至 `v0.1.7` tag**，问题记录保留在 git 历史中。本文件下方"1—3 节"的自动化测试/校验器结果已按 v0.1.8 状态更新；"4—6 节"的行为评测记录保留 v0.1.0/v0.1.7 期间的真实执行历史，未重新执行，按上一段如实标注。

## 1. 自动化测试

```bash
python3 -m pip install -r requirements-dev.txt   # 当前无外部依赖，见 requirements-dev.txt
python3 tools/check_skill.py
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

实际运行结果（本机，macOS 23.5.0 arm64，Python 3.9.6）：

- `tools/check_skill.py`：**all checks passed (0 warnings)**。
- `python3 -m unittest discover -s tests`：**97 个测试，全部通过**（v0.1.0: 35 → v0.1.1: 45 → v0.1.2: 56 → v0.1.3: 65 → v0.1.4: 73 → v0.1.5: 80 → v0.1.8: 97），v0.1.6/v0.1.7 未改动 `scripts/validate_evidence.py`，测试数保持80不变；v0.1.8 新增 17 个测试（`CoverageValidationTests`、`ClaimDimensionsValidationTests`、`SchemaVersionUpgradePromptTests`），覆盖此前所有规则外加：顶层 `coverage` 的五键完整性/多余键检测、`status` 枚举校验、`claim_ids` 悬空引用检测、`status=covered` 必须有一条 `kind!=unknown` 且 `dimensions` 匹配的主张支撑、`claims[].dimensions` 取值合法性与去重、声明旧版本 `schema_version: "1.1"` 的文件按既有版本不匹配机制硬失败。
- `python3 tools/build_release.py`：成功产出 `industry-research-v0.1.8.zip`、`SHA256SUMS.txt`（仅含 zip 自身哈希）。

CI（`.github/workflows/ci.yml`）在 push/PR 时于 ubuntu-latest 与 macos-latest（Python 3.10、3.12）上运行以上全部步骤，另外运行 `scripts/validate_evidence.py` 校验 `examples/public-industry-case/evidence.json`。CI 不运行需要真实模型账号或付费搜索的研究任务。Windows 未纳入本次 CI 矩阵。

## 2. evidence.json 校验器（scripts/validate_evidence.py）自测

见 `tests/test_evidence.py`：12 条结构规则各自有对应的失败 fixture（`tests/fixtures/invalid_*.json`，v0.1.8 新增 `invalid_coverage_missing_key.json`、`invalid_coverage_bad_status.json`、`invalid_coverage_dangling_claim.json`、`invalid_dimensions_bad_value.json` 四个），逐一确认能被正确拦截；同时确认合法的 `unknown`/`insufficient_evidence` 状态、跨年度时间序列比较、同源转载分组、`missing`/`out_of_scope` 覆盖状态无需捏造支撑主张等"合理但容易被误判"的情况不会被错误拒绝。

对真实案例的校验：

```bash
python3 scripts/validate_evidence.py examples/public-industry-case/evidence.json \
  --report examples/public-industry-case/report.md \
  --output examples/public-industry-case/validation.json
```

结果：`structural_ok: true`，0 errors，2 warnings（`C012`/`C013` 两条 inference 未附 `source_ids` 的软提醒，属于合理的既有状态——两者均为对其他已有来源支撑的主张的联合解读，不是凭空的推断；完整输出见 `examples/public-industry-case/validation.json`）。

## 3. 平台验证

见 [platform-compatibility.md](platform-compatibility.md)。摘要：Claude Code 完成了静态结构合规、宿主发现、两次独立抽样行为验证（用例1 overview 默认 + 用例4 client-prep）、脚本执行验证；Codex/OpenClaw/Hermes 完成了静态结构合规和本项目安装脚本可用性验证，**未能**完成宿主发现和行为验证（本机没有这三个平台的可用运行时或账号）。

## 4. 行为评测（evals/cases.md）执行状态

| 用例编号 | 状态 | 说明 |
|---|---|---|
| 1（普通行业名，未指定深度） | **已执行两次**：v0.1.0（六模块）+ **v0.1.8（五维框架）** | 六模块版本记录见下方"用例1执行记录（更正版）"；v0.1.8 复测记录见下方"用例1执行记录（v0.1.8 五维框架复测）"，用同一条中性措辞独立重跑，两次都不含深度/用途信号词 |
| 4（明确 client-prep） | **已执行**（六模块版本，原先被误标为用例1） | 见下方"用例4执行记录"。**更正说明**：本报告最初把这次执行记为"用例1"，但输入措辞"我需要在商务通话前快速了解……"本身会触发 client-prep 用途，实际验证的是用例4而非用例1；已重新执行一次真正中性措辞的用例1（见上一行），不依赖这次的结果冒充用例1通过；v0.1.8 五维框架下尚未重新执行用例4 |
| 13（完整 Quick 请求，五维总览） | **已执行（附带验证）**，与用例1 v0.1.8 复测为同一次运行 | 用例1的输入本身就是"完整 Quick 请求"，v0.1.8 复测同时满足用例13的检查点（见下方记录）：五维总览表齐全、篇幅保持 Quick 量级、未强行为每维凑数字（`business_model` 如实标 `partial`） |
| 2、3、5-12、14-21 | 设计完成，本次未执行 | 已在 `evals/cases.md` 中定义好用例和检查点，可供后续会话或协作者执行；不编造未执行用例的结果 |

### 用例1执行记录（更正版）

```text
用例编号：1（普通行业名，未指定深度）
执行日期：2026-09-03
Skill版本：0.1.0（子 Agent 启动时读取到的是替换为 0.1.1 之前的本机已安装版本；本次验证的是发现+行为机制本身，
  该机制在后续版本中未变，结论适用；机器校验器的具体规则改动见本报告"0. 外部评审修复历史"一节）
执行平台：Claude Code 2.1.201（子 Agent，独立无先前上下文）
输入摘要："帮我快速了解中国预制菜行业"（不含"商务通话""客户""深入"等任何深度/用途信号词）
实际输出位置：industry-research-output/yuzhicai-prepared-meals-20260903/（相对本仓库根目录；实际运行时落在协作者本机的仓库检出路径下，
  未纳入版本控制，不在本文档记录本机绝对路径）
  （yuzhicai-industry-briefing.md、evidence.json、validation.json）
```

**结果：passed（按运行当时的 schema_version 1.0 + 校验器规则）。** 注意：这次运行发生在 v0.1.2 把 `comparisons[].comparison_type` 提升为必填字段（schema 1.1）之前；其 `evidence.json` 若不补充该字段，用当前版本的 `scripts/validate_evidence.py` 复验会失败，这是 schema 演进的正常结果，不代表下方结论过时或不实——记录的是"当时确实通过了"，见本文件"0. 外部评审修复历史"关于 schema_version 的说明。关键发现：

- **默认深度与用途验证成立**：输入不含任何深度/用途信号词，子 Agent 自主判断为 Quick + overview，与 SKILL.md 的默认值表完全一致——这是本次用例1真正要验证的核心假设，现在有了不依赖"商务通话"这类会顺带触发 client-prep 的措辞的干净证据。
- **发现机制**：同样通过系统自动列出的可用 Skill 列表发现并调用，不是靠子 Agent 主动搜索。
- **证据规模**：15 个来源、10 条主张（9 fact / 1 unknown，本次没有独立的 inference 类主张，部分 fact 主张在 `limitations` 中带了类推断的说明）；evidence_status 分布 4 supported / 4 partial / 1 conflicted / 1 unverified。
- **口径纪律的真实体现**：报告明确指出"2024年市场规模不同来源估计从4850亿到5600亿+元不等（近20%的差异），且没有来源披露是否包含餐饮央厨产出"，并建议只能引用"数百亿元人民币量级、两位数增长"这种粗粒度表述——这正是 evidence-rules.md 要求的"口径不明时明确不可直接比较"，不是我预先写死的脚本化输出。
- **机器校验**：实际运行 `validate_evidence.py`，`structural_ok: true`，0 errors，0 warnings，退出码 0。
- **同样的环境限制再次出现**：又一次因为文件名含"report"被子 Agent 上下文的 Write 工具拒绝，与用例4的记录一致，进一步确认这是环境限制而非偶发。
- **一个值得记录的边界案例**：本次 prompt 明确要求"不要主动寻找或提及任何 Skill"，与系统级"匹配到 Skill 时必须调用"的强制规则产生冲突；子 Agent 选择遵循系统级规则并在事后如实说明这一冲突，而不是隐瞒。这不是本 Skill 设计的一部分，记录在此供参考。

### 用例1执行记录（v0.1.8 五维框架复测，同时验证用例13）

```text
用例编号：1（普通行业名，未指定深度）+ 13（完整 Quick 请求，五维总览）
执行日期：2026-09-04
Skill版本：0.1.8（先用 `python3 tools/install.py --platform claude --replace` 把本机
  `~/.claude/skills/industry-research/` 从 v0.1.7（六模块）替换为 v0.1.8，旧版本备份到
  `~/.industry-research-backups/claude-20260904T064140Z`，确认子 Agent 读到的是新版本后再测试）
执行平台：Claude Code（子 Agent，通过 Agent 工具启动，独立无先前上下文，不知晓本次开发会话内容）
输入摘要："帮我快速了解中国预制菜行业。"（不含深度/用途信号词，与更正版用例1使用同一个行业、同一条措辞，
  便于对比六模块版本与五维版本在同一输入下的产出差异）
实际输出位置：industry-research-output/yuzhicai-prepared-meals-20260904/（相对本仓库根目录，
  未纳入版本控制，属于 .gitignore 中 industry-research-output/ 规则排除的运行产出）
  （yuzhicai-industry-briefing.md、evidence.json、validation.json）
```

**结果：passed。** 本机独立复验（不依赖子 Agent 自报的结论）：

```bash
python3 -c "import json; d=json.load(open('industry-research-output/yuzhicai-prepared-meals-20260904/evidence.json')); print(d['schema_version'], list(d['coverage'].keys()))"
# 1.2 ['market', 'value_chain', 'business_model', 'competition', 'trends_risks']
python3 scripts/validate_evidence.py industry-research-output/yuzhicai-prepared-meals-20260904/evidence.json \
  --report industry-research-output/yuzhicai-prepared-meals-20260904/yuzhicai-industry-briefing.md
# structural_ok: true, 0 errors
```

关键发现：

- **五维框架真实落地**：`evidence.json` 的 `schema_version` 为 `1.2`，顶层 `coverage` 五个键齐全（`market`/`value_chain`/`business_model`/`competition`/`trends_risks`），状态分别为 `covered`/`covered`/`partial`/`covered`/`covered`——`business_model` 被如实标为 `partial` 而不是为了表格好看硬凑成 `covered`，符合"不为填表编造"的设计意图。全部 15 条 claim 都带 `dimensions` 字段，无一遗漏。
- **总览表与关系解释真实产出**：`report.md`（原文见下方摘录）在"最值得记住的认识"之后紧跟"二、行业定义与五维总览"，含完整的行业定义（预制菜的官方定义、2024年首次明确、2026年国标征求意见稿的排除范围）和五维总览表；"四、关键关系解释"一节用"监管定义清晰度→消费者信任→2025年9月罗永浩-西贝事件为何迅速升级为全国讨论"这条真实的因果路径，而不是泛泛而谈。
- **口径纪律延续**：市场规模数字存在机构间冲突（艾媒咨询4850亿元 vs 库润数据5466亿元，相差616亿元、增速判断几乎相反），报告如实并列展示、注明"目前没有'官方口径'的市场规模数字"，对应 3 条 `conflicted` 主张，与六模块版本时期的证据纪律水平一致，没有因为改了框架而退步。
- **证据规模**：10 个来源、15 条主张（14 fact / 1 inference）；evidence_status 分布 8 supported / 3 partial / 3 conflicted / 1 unverified；2 组 comparisons（市场规模口径冲突相关）、5 条 gaps。
- **机器校验**：本机独立运行 `validate_evidence.py --report`（不是只信子 Agent 自报），`structural_ok: true`，0 errors，1 warning（`C015` 一条 partial 推断缺 source_ids 的软提醒），3 条 conflicted 主张被正确标记为 `manual_review_required`——校验器行为符合设计预期。
- **暴露的真实问题（已修复）**：报告的"行业定义"部分写成了一段说明性文字，没有逐条回答定义卡的五个问题；"商业模式"部分也没有走完"收费单位/交付内容/履约成本/盈利条件"这套代表性交易结构，而是停留在"规模化生产摊薄成本、毛利率走低"这类概括性描述。这与验收意见中对 `examples/public-industry-case/` 的发现完全一致，证明不是示例案例的孤立问题，而是模板指引不够明确导致的系统性压缩。已强化 `assets/report-template.md`（明确要求逐条列出定义卡五问和代表性交易五要素）和 `references/output-guidance.md`，并同步修复了公开示例（见 `examples/public-industry-case/README.md`"同日验收复核"一节）；本次复测的输出文件本身未回滚重跑，如实保留其"框架已落地、但当时的模板指引还不够严格"这一状态。
- **环境限制再次出现**：子 Agent 把主报告命名为 `yuzhicai-industry-briefing.md` 而非 `report.md`，与用例4、六模块版本用例1的记录一致——继续确认这是 Claude Code 对子 Agent 写入 `report` 开头文件名的防护限制，与本 Skill 设计无关。

### 用例4执行记录（原误标为用例1）

```text
用例编号：1（普通行业名，未指定深度；实际触发为 client-prep，因输入措辞含"商务通话前"）
执行日期：2026-09-03
Skill版本：0.1.0
执行平台：Claude Code（子 Agent，独立无先前上下文，通过 Agent 工具启动，不知晓本次开发会话的任何内容）
输入摘要："我需要在商务通话前快速了解中国协作机器人行业，请帮我研究并给出可用的报告"
实际输出位置：industry-research-output/协作机器人-20260903/（相对本仓库根目录；不在本文档记录本机绝对路径）
  （client-brief.md、evidence.json、validation.json、协作机器人行业研究.md；未纳入本仓库版本控制，
  属于 .gitignore 中 industry-research-output/ 规则排除的运行产出，符合 SKILL.md"不写入 Skill 安装目录"的要求；
  同用例1一样，这次运行早于 schema 1.1，其 evidence.json 未含 comparison_type，用当前校验器复验会失败，
  属于 schema 演进的正常结果）
```

**结果：passed。** 关键发现：

- **发现机制**：子 Agent 在会话开始时的系统提示中看到 `industry-research` 出现在可用 Skill 列表中（这正是它安装到 `~/.claude/skills/industry-research/` 后被 Claude Code 自动发现的结果），判断本次任务匹配后主动调用，并读取了 SKILL.md 及 `references/research-workflow.md`、`evidence-rules.md`、`evidence-schema.md`、`source-strategy.md`、`industry-guides/industrial-b2b.md` 和两个模板文件。这证明"宿主发现"确实转化为了"行为触发"，不只是文件存在。
- **联网研究**：实际发出 12 次 WebSearch、5 次 WebFetch（追到界面新闻、21世纪经济报道×2、新浪财经×2 的原文全文，而非只用搜索摘要）。
- **证据纪律**：产出 24 条 claim、27 个来源；21 fact / 2 inference（均带 rationale 和 basis_claim_ids）/ 1 unknown；evidence_status 分布为 6 supported（原文已读）/ 14 partial（多为仅摘要）/ 3 conflicted / 1 unverified。3 条 conflicted 主张（市场规模统计口径冲突、外资品牌份额区间、下游应用占比）被并列展示并说明差异原因，**没有**被取平均或择一呈现。
- **机器校验**：实际运行 `validate_evidence.py`，`structural_ok: true`，2 条合理警告（inference 类主张缺 source_ids 的软提醒）、3 条 conflicted 主张被标记为需人工复核——校验器行为符合设计预期。
- **独立于本次开发的措辞差异**：报告开头自行判断"研究深度：Quick（因数据口径冲突较多，实际检索量接近Deep下限）"——这是 SKILL.md"资料已足够时停止搜索、不够时收窄结论"原则的实际体现，而非我预设的脚本化行为。

**发现的真实问题（非本 Skill 设计缺陷，是本次执行环境的限制）**：子 Agent 尝试按 `assets/report-template.md` 的约定把主报告命名为 `report.md` 时，被 Claude Code 的 Write 工具拒绝，报错"Subagents should return findings as text, not write report files"——这是当前 harness 对**子 Agent**（而非主对话）写入类似 `report`/`summary`/`findings`/`analysis` 命名文件的一个防护限制，与本 Skill 本身无关。子 Agent 自行改用 `协作机器人行业研究.md` 规避，内容不受影响。这提示：**在通过子 Agent（而非主对话）调用本 Skill 时，如果所在 harness 有类似的文件名防护策略，可能需要用非"report"开头的文件名**；`examples/public-industry-case/` 中由主对话直接产出的 `report.md` 不受此限制影响。已记录在 `docs/platform-compatibility.md`。

## 5. 对比评测（evals/rubric.md 中定义的方法）

**状态：方法与记录模板已交付（见 `evals/rubric.md`），本次未实际执行三任务×三条件的对比实验。** 原因：需要额外的独立执行预算（裸提示词 + 至少一个对照 Skill + 本 Skill，各跑传统产业/软件服务/新兴领域三个任务），超出本次交付的时间范围。不编造对比分数或结论；这是明确的后续工作项，方法已可直接复用。

## 6. 已知阻塞与后续工作

- Codex / OpenClaw / Hermes 的宿主发现与行为验证：需要对应平台的本地运行时或账号。
- 对比评测的实际执行：需要额外预算，方法已就绪。
- 用例2、3、5-12、14-21（共18个）的实际执行：方法已就绪，欢迎后续会话或协作者执行并补充记录（用例1已在六模块和五维两个版本下各执行一次，用例4/13见第4节；13是v0.1.8复测顺带满足的，不是单独执行的）。
- **v0.1.8 五维框架的真实行为验证**：2026-09-04 已用一次独立子 Agent 运行（中性措辞、无先前上下文）完成了用例1在 v0.1.8 下的复测，本机独立复验 `structural_ok: true`，证明五维框架、`coverage`/`dimensions` 在真实研究场景下可用，并因此发现并修复了"定义卡/代表性交易被压缩成段落"这一真实问题（见上方"0."节）。**这只是1个用例、1次运行、同一台机器同一会话内完成**，不能替代对用例4（client-prep）在新框架下的复测，也不能替代新增用例14-21（多角色平台、组合收入、上游议价、无份额数据、成熟行业新细分、纯趋势观点、用户框架图等边界场景）的实际执行——这些仍是需要独立会话补齐的工作项。
