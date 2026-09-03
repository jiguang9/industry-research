# industry-research

一个 Agent Skill：帮助营销、咨询和业务从业者快速理解一个陌生行业，产出有证据支持的行业地图、商业模式解释和下一步研究建议。默认中文输出。

## 解决什么问题，适合谁

最常见的场景是接到一个陌生行业的客户、需要准备第一次沟通；也适用于单纯的行业入门学习，或围绕某个行业探索业务机会。

**最小输入**：只需要一个可识别的行业或细分领域，例如"帮我快速了解中国工业软件行业"。已有材料、地区、客户名称、时间范围都是可选的，缺失时按 [SKILL.md](SKILL.md) 中的默认规则处理，不会用一堆问卷式问题挡住你。

**不适合**：只比较两三家具体公司谁更强（那是 [competitor-analysis](#与-competitor-analysis-的分工) 的工作）、证券估值和买卖建议、纯学术文献综述。

## 一个真实案例

[examples/public-industry-case/](examples/public-industry-case/) 是一份用本 Skill 实际完成的公开研究（中国协作机器人行业，Quick 深度，2026-09-03），包含 `report.md`、`evidence.json`、`validation.json`（真实运行校验器的输出）和一次真实发生的纠错过程（把搜索引擎摘要中被错误转述的数字，通过读取原文更正）。

## 安装与调用

四个平台共用同一份 `SKILL.md` + `references/` + `assets/` + `scripts/` payload。项目自带一个本地安装脚本（不是官方安装器，只是文件复制工具），也可以手动复制。

```bash
git clone https://github.com/jiguang9/industry-research.git
cd industry-research
python3 tools/install.py --platform claude    # 或 codex / openclaw / hermes
```

| 平台 | 默认安装目录 | 调用方式 | 验证状态 |
|---|---|---|---|
| Claude Code | `~/.claude/skills/industry-research/` | 输入 `/industry-research`，或直接描述任务让 Claude 自动触发 | 见 [docs/platform-compatibility.md](docs/platform-compatibility.md) |
| Codex | `~/.agents/skills/industry-research/` | CLI/IDE 中输入 `$industry-research`；ChatGPT Work 中 `@industry-research` | 见 [docs/platform-compatibility.md](docs/platform-compatibility.md) |
| OpenClaw | `~/.openclaw/skills/industry-research/` | `openclaw skills list` 确认发现后，`/skill industry-research <任务>`；也可 `openclaw skills install git:jiguang9/industry-research@v0.1.3` | 见 [docs/platform-compatibility.md](docs/platform-compatibility.md) |
| Hermes Agent | `~/.hermes/skills/industry-research/` | 让当前 Agent 列出/描述其技能确认发现后，`/industry-research <任务>` | 见 [docs/platform-compatibility.md](docs/platform-compatibility.md) |

自定义 profile、远程环境或项目级安装，用 `--dest` 指定确切目标目录：

```bash
python3 tools/install.py --platform codex --dest /absolute/path/to/industry-research
```

**四个平台的验证程度不同**——静态结构合规、宿主发现与加载、实际行为验证、联网验证是四个不同层次，不能互相替代。具体到每个平台在哪个层次通过了测试、哪些还未测试，见 [docs/platform-compatibility.md](docs/platform-compatibility.md)，请以该文件为准，不要假设"能安装"就等于"实测可用"。

## Quick 与 Deep

默认 Quick：建立正确的基础理解，通常 4—8 组搜索、6—10 个页面。用户说"深入""完整报告""正式研究"时切换到 Deep：支持一个明确业务问题，通常 8—16 组搜索、12—24 个页面。两档的真实性和证据要求完全相同，Deep 只是范围更大，不是"可以更随意"。详见 [SKILL.md](SKILL.md)。

## 能力要求与降级行为

核心研究流程不强制要求 Python，但没有搜索/文件写入/命令执行能力时会明显降级：

| 缺少的能力 | 实际行为 |
|---|---|
| 无法联网 | 只依据用户提供的材料研究，明确覆盖边界 |
| 无 Python | 继续研究、人工核对口径，机器校验标注为未执行 |
| 无文件写入 | 直接在对话中按报告结构输出，不虚构文件路径 |

完整降级行为表见 [SKILL.md](SKILL.md#能力不足时的行为)。

## 输出与校验器的实际边界

每次研究默认产出 `report.md` + `evidence.json`（结构定义见 [references/evidence-schema.md](references/evidence-schema.md)），按需产出 `client-brief.md` / `competitor-brief.md`。有 Python 时可运行：

```bash
python3 scripts/validate_evidence.py path/to/evidence.json --report path/to/report.md --output validation.json
```

**这个校验器只检查结构和内部一致性**：ID 是否唯一、引用是否悬空、`unknown` 是否被误标为 `supported`、数字口径缺失是否如实声明、估算值是否公开了方法。它**不能**、也不试图证明来源内容真实、证明引用真的支持原句、穷尽正文所有数字，或证明行业结论正确——这些仍然需要人工判断。`validation.json` 的输出里会带这句免责声明，不要把"校验通过"读成"研究真实性通过"。

## 升级

```bash
cd industry-research && git pull
python3 tools/install.py --platform <platform> --replace   # 会保留旧版本备份
```

当前版本：见 [VERSION](VERSION)。已知限制：见下方"已知限制"和 [docs/platform-compatibility.md](docs/platform-compatibility.md) 中标注为 `not_tested` 的项目。

## 与 competitor-analysis 的分工

`industry-research` 负责行业范围、结构、商业模式和变化；具体公司之间的深入比较交给 `competitor-analysis`。本 Skill 结尾可产出 `competitor-brief.md` 作为交接文件，但不自动展开完整的多家公司竞品分析；缺少 `competitor-analysis` 不影响本 Skill 独立使用。

## 已知限制

- 市场规模类数字依赖公开可检索资料，行业协会/付费数据库未接入。
- 机器校验器只做结构检查，不做事实核查（见上文"输出与校验器的实际边界"）。
- 四平台的实测覆盖程度不同，具体见 [docs/platform-compatibility.md](docs/platform-compatibility.md)。
- 不提供证券估值、买卖建议或收益承诺式判断。

## License 与贡献

MIT License，见 [LICENSE](LICENSE)。欢迎通过 Issue/PR 提出问题或改进；改动涉及 `references/`、`scripts/validate_evidence.py`、`tools/` 时请附带 `python3 tools/check_skill.py` 和 `python3 -m unittest discover -s tests` 的运行结果。
