# 平台验证矩阵

**v0.1.8 说明**：本文件中标记为 `passed` 的"自然语言自动触发 + 实际研究行为"两条历史记录（用例1旧版、用例4），是针对 v0.1.0/v0.1.7 期间的六模块工作流（行业地图/交易与交付/商业模式/用户与渠道/竞争结构/变化与问题）实际跑通的子 Agent 测试，测试时 `evidence.json` 还没有 `coverage`/`dimensions` 字段。v0.1.8 把研究主线改为"定义与边界 → 五维 → 关系解释 → 建议"（见 [../references/industry-framework.md](../references/industry-framework.md)）。**2026-09-04 已补测一次**：先用 `tools/install.py --platform claude --replace` 把本机 Claude Code 的 Skill 安装从 v0.1.7 替换为 v0.1.8，再开一个全新无先前上下文的子 Agent，输入中性措辞"帮我快速了解中国预制菜行业。"，产出的 `evidence.json` 确认 `schema_version: "1.2"`、`coverage` 五键齐全、全部 claim 带 `dimensions`，本机独立复验 `structural_ok: true`；详细记录见 [validation-report.md 第4节"用例1执行记录（v0.1.8 五维框架复测）"](validation-report.md)。**这只证明了1个用例（用例1，中性措辞、overview 默认）在 v0.1.8 下真实可用**，不能代表 client-prep（用例4）、opportunity 用途，或新增用例14-21（多角色平台、组合收入、上游议价反例、无份额数据、成熟行业新细分、纯趋势观点、用户框架图等边界场景）也已验证——这些仍是明确的已知缺口，建议下一次有可用 Agent 运行环境时继续补测。

记录格式：

```text
平台 / 版本 / 日期 / OS / 安装位置 / 发现结果 / 显式调用 /
相对参考文件读取 / 材料模式输出 / 联网模式输出 /
脚本执行 / 降级行为 / 证据位置 / 未测原因
```

四个层次互不替代：**静态结构合规**（文件/路径/格式满足检查）、**宿主发现与加载**（该版本平台能找到并读取 Skill）、**行为验证**（在记录的模型/权限/工具组合下完成了指定用例）、**联网验证**（搜索、网页读取实际可用）。状态用 `passed` / `failed` / `not_tested`。

## Claude Code

- 版本：Claude Code VSCode 扩展 **2.1.201**（darwin-arm64，取自 `~/.vscode/extensions/anthropic.claude-code-2.1.201-darwin-arm64/package.json` 的 `version` 字段，2026-09-03 核对；本机没有独立安装的 `claude` CLI 二进制，无法交叉核对 CLI 版本号是否一致）
- OS：macOS (Darwin 23.5.0, arm64)
- 安装位置：`~/.claude/skills/industry-research/`（`python3 tools/install.py --platform claude` 安装，随后用 `--replace` 覆盖了一份 2026-09-03 16:44 创建的、内容不同的旧版本，旧版本已备份到 `~/.industry-research-backups/claude-20260903T095226Z/`，未纳入本仓库）

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | `tools/check_skill.py` 通过；frontmatter `name: industry-research` 正确；相对引用全部可解析 |
| 宿主发现与加载 | passed | 安装后，当前会话的可用 Skill 列表中出现 `industry-research`（系统提示自动列出），说明 Claude Code 从 `~/.claude/skills/industry-research/` 正确发现了本 Skill |
| 显式调用 `/industry-research` | not_tested | 本次验证在非交互式 harness 中完成，未实测斜杠命令的交互式输入；发现层已确认该命令会被注册（Claude Code 文档：Skill 目录名即为命令名） |
| 自然语言自动触发 + 实际研究行为（对应 evals/cases.md 用例4，client-prep） | passed（单次抽样） | 另开一个全新、无先前上下文的子 Agent，给出"我需要在商务通话前快速了解中国协作机器人行业"。**注意措辞**："商务通话前"这个短语本身会触发 client-prep 用途，因此这次实测验证的是用例4（明确 client-prep），不是用例1（普通行业名、未指定深度/用途、理应默认 overview）——本文件先前的记录把它错误归为用例1，已更正。**实际结果**：子 Agent 在系统提示的可用 Skill 列表中看到 `industry-research`（发现层的直接证明）并主动调用，读取了 SKILL.md 及多个 references 文件，产出 24 条 claim / 27 个来源，其中 3 条冲突数字被并列展示而非取平均 |
| 自然语言自动触发 + 实际研究行为（对应 evals/cases.md 用例1，overview 默认） | passed（单次抽样） | 用中性措辞"帮我快速了解中国预制菜行业"（不含深度/用途信号词）单独另开一个子 Agent 重测。**实际结果**：正确默认 Quick + overview（与 SKILL.md 默认值表一致），15 个来源 / 10 条主张（9 fact / 1 unknown），evidence_status 分布 4 supported / 4 partial / 1 conflicted / 1 unverified，实际运行 `validate_evidence.py` 通过。报告明确指出不同来源的市场规模数字口径不一致（近20%差异）并拒绝给出单一精确数字，符合证据规则。详细记录见 `docs/validation-report.md` |
| 相对参考文件读取（references/、assets/） | passed | 子 Agent 明确报告读取了 `research-workflow.md`、`evidence-rules.md`、`evidence-schema.md`、`source-strategy.md`、`industry-guides/industrial-b2b.md` 及两个模板文件 |
| 材料模式输出（无联网，仅用户材料） | not_tested | 本次抽样测试子 Agent 具备联网能力，未构造"无联网"场景 |
| 联网模式输出 | passed | 子 Agent 实际发出 12 次 WebSearch、5 次 WebFetch（追读原文全文，非仅用摘要） |
| 脚本执行（`scripts/validate_evidence.py`） | passed | 本机直接运行验证（见 `docs/validation-report.md`、`examples/public-industry-case/validation.json`），子 Agent 测试中也独立运行了一次，`structural_ok: true` |
| 降级行为（无 Python） | not_tested | 未构造无 Python 的环境 |
| 证据位置 | 见 `docs/validation-report.md`；两次子 Agent 的完整 transcript 未保留在仓库中（属于运行时会话记录，不属于可公开分发的仓库内容）；产出文件在本机 `industry-research-output/协作机器人-20260903/`（用例4）和 `industry-research-output/yuzhicai-prepared-meals-20260903/`（用例1），均未纳入版本控制（符合 SKILL.md 输出规则） |

**发现的一个环境限制（记录以供其他用户参考，不是本 Skill 的设计缺陷）**：子 Agent 尝试按模板约定写入 `report.md` 时，被当前 harness 的 Write 工具拒绝（"Subagents should return findings as text, not write report files"）——这是 Claude Code 对**子 Agent**写入 `report`/`summary`/`findings`/`analysis` 类命名文件的一个防护策略，与主对话无关。子 Agent 改用其他文件名后不受影响。也就是说：**通过主对话调用本 Skill 时（`examples/public-industry-case/` 即如此）没有这个限制；只有当调用发生在子 Agent 上下文里、且所在 harness 有类似防护时，可能需要避免使用以 report 开头的文件名。**

## Codex

- 安装位置（默认）：`~/.agents/skills/industry-research/`；项目级 `.agents/skills/industry-research/`
- 调用：CLI/IDE 中 `$industry-research`；ChatGPT Work 中 `@industry-research`
- 元数据：`agents/openai.yaml` 提供 UI 展示名称、简介、默认 prompt

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | 路径、frontmatter、`agents/openai.yaml` 均符合 [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills/)（2026-09-03 核对，该 URL 会 308 重定向到 `learn.chatgpt.com/docs/build-skills`，内容一致）文档描述的格式 |
| 安装脚本可用性 | passed | `tools/install.py --platform codex --dest <path>` 在本机测试通过（见 `tests/test_install.py`），生成的目录结构符合 Codex 文档描述的 `.agents/skills/<name>/SKILL.md` |
| 宿主发现与加载 / 显式调用 / 行为验证 / 联网验证 | not_tested | 本次执行环境中没有可用的 Codex CLI/账号，无法实测。原因：Codex 需要独立的账号登录和运行时，本会话运行在 Claude Code harness 中，不具备该运行时 |

## OpenClaw

- 安装位置（默认，管理型目录）：`~/.openclaw/skills/industry-research/`
- 调用：`openclaw skills list` / `openclaw skills info industry-research` 确认发现；`/skill industry-research <任务>` 调用
- Git 直接安装：`openclaw skills install git:jiguang9/industry-research@v0.1.9`——该命令要求"`SKILL.md` 位于源仓库根目录"，本仓库正好符合这一结构（单 Skill、仓库根目录即 Skill 根目录），因此理论上应可用；但由于本机没有 OpenClaw 运行时，**该命令本身未实际执行验证**

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | 路径与 SKILL.md frontmatter（`name`、`description`）符合 [docs.openclaw.ai/tools/skills](https://docs.openclaw.ai/tools/skills)（2026-09-03 核对）描述的最小格式 |
| 安装脚本可用性 | passed | `tools/install.py --platform openclaw --dest <path>` 本机测试通过 |
| 宿主发现与加载 / 显式调用 / 行为验证 / 联网验证 / Git 直接安装 | not_tested | 本机未安装 OpenClaw CLI，也没有可用账号/Gateway，无法实测 `openclaw skills list`、`/skill` 调用或 `openclaw skills install git:...` 命令的实际效果 |

## Hermes Agent

- 安装位置（默认 profile）：`~/.hermes/skills/industry-research/`
- 调用：让当前 Agent 列出/描述其技能确认发现后，`/industry-research <任务>`
- GitHub 直接安装：官方文档描述的格式是 `hermes skills install owner/repo/skills/<name>`，即期望仓库内有 `skills/<name>/SKILL.md` 这样的子路径。**本仓库是单 Skill、SKILL.md 位于仓库根目录，不符合这个子路径形态**，因此 `hermes skills install jiguang9/industry-research/skills/industry-research` 这类命令**不适用**，本文档不虚构一个能跑通的子路径命令。
- Direct URL 安装（`hermes skills install https://raw.githubusercontent.com/jiguang9/industry-research/main/SKILL.md`）：**2026-09-03 重新核对官方文档后更正**——该方式并非只拉取 `SKILL.md` 单个文件，文档原文为"Hermes also fetches explicitly referenced files under `references/`, `templates/`, `scripts/`, `assets/`, and `examples/`, then scans and installs the complete bundle"。本仓库 SKILL.md 中以 Markdown 链接形式引用了 `references/*.md`、`assets/*.md` 和 `scripts/validate_evidence.py`，这部分预期能被 Hermes 的引用扫描一并拉取；**但这只是基于文档描述的推断，Direct URL 安装的实际行为本次未在真实 Hermes 环境中验证**。仍建议优先使用 `git clone` 后运行 `tools/install.py --platform hermes`，可确定性地保证 `references/`、`assets/`、`scripts/` 全部到位。

| 层次 | 状态 | 说明 |
|---|---|---|
| 静态结构合规 | passed | 路径与 frontmatter 符合 [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)（2026-09-03 核对）描述的格式 |
| 安装脚本可用性 | passed | `tools/install.py --platform hermes --dest <path>` 本机测试通过 |
| 宿主发现与加载 / 显式调用 / 行为验证 / 联网验证 | not_tested | 本机没有 Hermes Agent 运行时或账号，无法实测 |

## 已知限制与后续验证计划

- 四平台中只有 Claude Code 在本次交付中完成了"宿主发现"和"行为验证"层的实测（且行为验证只有一次抽样，不代表所有措辞和场景下都稳定触发）；Codex、OpenClaw、Hermes 三个平台目前只做到了"静态结构合规"和"本项目安装脚本可用性"两层。
- 后续如果能获得 Codex/OpenClaw/Hermes 的可用账号或本地运行时，应按本文件顶部的记录格式补齐对应条目，不应把"能被 `tools/install.py` 正确安装"误报为"该平台已实测可用"。
- Windows 未在本次验证范围内；CI（`.github/workflows/ci.yml`）目前只跑 Linux 和 macOS。
- v0.1.8 引入的五维框架（`coverage`/`dimensions`、report.md 前部总览表、"关键关系解释"一节）已有 1 次真实 Agent 会话行为验证（用例1，见上方说明和 [validation-report.md](validation-report.md)），但 evals/cases.md 中其余 20 个用例（尤其新增的 14—21）仍未在新框架下实际执行；建议下次有可用运行环境时优先补齐 client-prep（用例4）和新增的边界场景用例。
