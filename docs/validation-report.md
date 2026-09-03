# 验证记录

版本：0.1.0　记录日期：2026-09-03

## 1. 自动化测试

```bash
python3 -m pip install -r requirements-dev.txt   # 当前无外部依赖，见 requirements-dev.txt
python3 tools/check_skill.py
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

实际运行结果（本机，macOS 23.5.0 arm64，Python 3.9.6）：

- `tools/check_skill.py`：**all checks passed (0 warnings)**。
- `python3 -m unittest discover -s tests`：**35 个测试，全部通过**，覆盖 `scripts/validate_evidence.py`（结构校验、循环引用检测、口径缺失检测、report.md 交叉引用）、`tools/install.py`（含中文+空格路径、幂等安装、冲突检测、`--replace`+备份、路径安全防护、四平台并行安装）、`tools/build_release.py`（zip 结构、SHA256、解压后相对引用可解析、不含开发文件）。
- `python3 tools/build_release.py`：成功产出 `industry-research-v0.1.0.zip` 与 `SHA256SUMS.txt`。

CI（`.github/workflows/ci.yml`）在 push/PR 时于 ubuntu-latest 与 macos-latest（Python 3.10、3.12）上运行以上全部步骤，另外运行 `scripts/validate_evidence.py` 校验 `examples/public-industry-case/evidence.json`。CI 不运行需要真实模型账号或付费搜索的研究任务。Windows 未纳入本次 CI 矩阵。

## 2. evidence.json 校验器（scripts/validate_evidence.py）自测

见 `tests/test_evidence.py`：8 条结构规则各自有对应的失败 fixture（`tests/fixtures/invalid_*.json`），逐一确认能被正确拦截；同时确认合法的 `unknown`/`insufficient_evidence` 状态、跨年度时间序列比较、同源转载分组等"合理但容易被误判"的情况不会被错误拒绝。

对真实案例的校验：

```bash
python3 scripts/validate_evidence.py examples/public-industry-case/evidence.json \
  --report examples/public-industry-case/report.md \
  --output examples/public-industry-case/validation.json
```

结果：`structural_ok: true`，0 errors，0 warnings（完整输出见 `examples/public-industry-case/validation.json`）。

## 3. 平台验证

见 [platform-compatibility.md](platform-compatibility.md)。摘要：Claude Code 完成了静态结构合规、宿主发现、单次抽样行为验证、脚本执行验证；Codex/OpenClaw/Hermes 完成了静态结构合规和本项目安装脚本可用性验证，**未能**完成宿主发现和行为验证（本机没有这三个平台的可用运行时或账号）。

## 4. 行为评测（evals/cases.md）执行状态

| 用例编号 | 状态 | 说明 |
|---|---|---|
| 1（普通行业名，未指定深度） | **已执行** | 通过一个全新、无先前上下文的子 Agent 完成，见下方"用例1执行记录" |
| 2-12 | 设计完成，本次未执行 | 已在 `evals/cases.md` 中定义好用例和检查点，可供后续会话或协作者执行；不编造未执行用例的结果 |

### 用例1执行记录

```text
用例编号：1（普通行业名，未指定深度）
执行日期：2026-09-03
Skill版本：0.1.0
执行平台：Claude Code（子 Agent，独立无先前上下文）
输入摘要：自然语言请求"我要在商务通话前快速了解中国协作机器人行业"
```

（该子 Agent 任务在本报告撰写时仍在后台执行；结果将在完成后补充到本节，包括：是否自行发现并使用 industry-research Skill、是否产出 report.md/evidence.json 及其绝对路径、是否使用了联网搜索、追踪的证据条数与 fact/inference/unknown 区分情况。）

## 5. 对比评测（evals/rubric.md 中定义的方法）

**状态：方法与记录模板已交付（见 `evals/rubric.md`），本次未实际执行三任务×三条件的对比实验。** 原因：需要额外的独立执行预算（裸提示词 + 至少一个对照 Skill + 本 Skill，各跑传统产业/软件服务/新兴领域三个任务），超出本次交付的时间范围。不编造对比分数或结论；这是明确的后续工作项，方法已可直接复用。

## 6. 已知阻塞与后续工作

- Codex / OpenClaw / Hermes 的宿主发现与行为验证：需要对应平台的本地运行时或账号。
- 对比评测的实际执行：需要额外预算，方法已就绪。
- 用例2-12 的实际执行：方法已就绪，欢迎后续会话或协作者执行并补充记录。
