# AGENTS.md — Guide for Coding Agents（给 Codex 的协作说明）

> 本文件写给在本仓库里工作的 AI 编程助手（Codex 等）。开始任何任务前请先读完本文件，再看 `README.md` 的 **Status**（当前进度）和分配给你 owner 的 GitHub Issue（当前任务），然后按需读 `INSTRUCTIONS.md`（执行手册）和 `PROJECT_SUMMARY.md`（背景）。
>
> **写法约定：** 流程和说明用中文；项目内容（模块、规则、指标）以英文为主、中文为辅。

---

## 1. Project context（项目背景）

This repo stress-tests the open-source **TradingAgents** framework (multi-agent LLM trading on LangGraph) under clean, cost-aware, statistically honest conditions.
（本项目在无前视偏差、计入成本、统计诚实的条件下测试 TradingAgents。）

- **Main question:** does any edge survive? "The edge disappears" is a valid, publishable result.（"没有优势"也是有效结论。）
- **Agent model under test:** `llama3.1-8k` (= `llama3.1:8b`, `num_ctx` 8192) via local Ollama at `http://localhost:11434/v1`.
- **Key experiment:** Exp 1 memorization test, 2×2 design — period (2023 in-sample / 2025 out-of-sample) × variant (normal / masked). 详见 `INSTRUCTIONS.md` §6。

这是一个研究项目：**代码"能跑"不等于"正确"**。一个悄悄的数据泄漏或统计错误会让整个结论作废，所以本文件里的规则优先级高于"尽快完成任务"。

---

## 2. Collaboration setup（分工方式）

本项目由 **Gav**（Gavin Li）和 **Aya**（艾亚）两人共同负责，同时使用两个 AI 助手。署名、分支和 PR 规则见 `CONTRIBUTING.md`。下文中的 "owner" 指发起当前任务的那位负责人（Gav 或 Aya）。

| Role | Who | 负责内容 |
|---|---|---|
| Design & review | Claude (Opus 5.5) | 实验设计、masking / 统计方案、代码审查、排错 |
| Implementation | **Codex (you)** — Gav and Aya each run their own Codex | 按 spec 实现模块、写测试、修 bug、开 PR |
| Owners | Gav & Aya | 决定设计、批准改动、运行长时间实验；预注册设定的修改需要两人都同意 |

协作规则：
1. **一次只做一个模块或一个任务。** 不顺手重构无关文件。
2. **不和另一个助手同时改同一个文件。** 如果发现某文件近期被改过且与你的任务冲突，停下来说明。
3. **Spec 不清楚就停下来问**，不要自己发明实验设计、指标定义或数据处理方式。这类决定属于 owner（Gav / Aya，在 Claude 协助下）。
4. **高风险模块（§5）完成后需要交叉审查**：你实现，Claude 审查，或反过来。请在汇报里明确标出需要审查的部分。

---

## 3. Hard rules（硬性规则，任何情况下不得违反）

### Research integrity（研究诚信）
1. **Point-in-time only.** Every data item fed to the agent must have timestamp ≤ decision date. For financial statements use the **filing date**, never the period-end date.
   （喂给 agent 的所有数据时间戳都必须 ≤ 决策日；财报看提交日期，不看报告期末。）
2. **Never silently convert failures.** A failed / timed-out / unparseable run gets its own `status` (`tool_error`, `parse_error`, `timeout`, `leak`). Do not default it to HOLD inside the runner.
   （失败的运行必须单独标记状态，不能在 runner 里悄悄变成 HOLD。）
3. **Never overwrite or delete run logs.** `results/raw/runs.jsonl` is append-only. Re-runs get a new `started_at`; deduplication happens in analysis, explicitly.
   （运行日志只追加，不覆盖、不删除。）
4. **Do not change pre-registered settings** (grid, metrics, thresholds, cost assumptions, fixed settings in `INSTRUCTIONS.md` §1.1) without explicit agreement from both owners (Gav and Aya), recorded in the Decision Log.
   （预注册的设定不能自行修改。）
5. **No tuning on out-of-sample data.** Do not adjust prompts, parameters, or parsing rules based on 2025 results.
   （不能根据 2025 年的结果调整任何东西。）
6. **Model cutoff rule.** Do not suggest swapping the agent model for a newer API model (GPT, Claude, Gemini, etc.) for performance evaluation — their training data covers 2023 and 2025, which contaminates the test.
   （不要建议换成更新的 API 模型来评估收益，它们见过测试时期的数据。）
6a. **Isolate agent memory per run.** TradingAgents keeps a persistent lesson log (`memory_log_path`, default `~/.tradingagents/memory/trading_memory.md`) shared by all runs. Every run must use its own fresh, empty memory file under `results/raw/<exp>/<run_id>/`. Shared memory leaks future outcomes into earlier dates, leaks real identities into masked runs, and couples seeds. `data_cache_dir` must point inside the project (`results/raw/cache/`) so cached data can be audited.
   （每次运行必须使用独立的空记忆文件：共用记忆会把未来结果泄漏给更早的日期、把真实身份泄漏给遮蔽组，并让不同种子互相影响。数据缓存放在项目目录内，便于审查。）

### Repo hygiene（仓库规范）
7. **Do not modify `external/TradingAgents/`.** It is pinned. Change behavior via wrappers, config, or monkeypatching in `src/`, and document each patch.
   （上游代码已锁定版本，只能在 `src/` 里包装，不能直接改。）
8. **Never commit** `.env`, API keys, tokens, Bloomberg data, or large raw logs. Never print secrets in logs.
9. **Never start long runs** (anything beyond a tiny smoke test, roughly > 5 LLM calls) without the owner's go-ahead. Local GPUs are small and runs are slow.
   （不要擅自启动长时间实验。）
10. **No new dependencies** without saying why. Prefer the standard library, `numpy`, `pandas`, `yfinance`, `pyyaml`, `pytest`.

---

## 4. Environment（环境）

| Item | Value |
|---|---|
| OS / shell | Windows 11, PowerShell |
| Python | 3.11+, venv at `.venv/` |
| TradingAgents | pinned clone in `external/TradingAgents/`, commit in `results/RUN_INFO.md` |
| LLM server | Ollama, model `llama3.1-8k`, `http://localhost:11434/v1` |
| Hardware | Gav: 16 GB RAM, RTX 5060 Laptop 8 GB VRAM; Aya: *(待补充)* — one Ollama run at a time, no parallel LLM calls |

- 路径用 `pathlib`，不要写死 `C:\Users\...`。
- 读 `configs/*.yaml` 获取实验参数，不要在代码里硬编码网格。
- TradingAgents 的类名、参数名、配置键**以源码为准**；如果和 `INSTRUCTIONS.md` 的示例不一致，以源码为准并在汇报里指出差异。

---

## 5. High-risk modules（高风险模块与验收要求）

以下模块写错不会报错，但会让结论无效。每个都必须带测试，并在完成后交给 Claude 审查。

| Module | What can go wrong | Required tests（必须有的测试） |
|---|---|---|
| `src/masking.py` | Real ticker / name / year leaks into masked tool output | Regex scan of masked outputs finds no real ticker, company name, or 4-digit years 2000–2030; alias ↔ real mapping round-trips |
| `src/leak_check.py` | Uses period-end instead of filing date; misses one data source | Synthetic record with filing date > decision date is flagged; record with filing date ≤ decision date passes |
| `src/stats.py` | Bootstrap resamples decisions instead of weeks; wrong annualization | Sharpe SE matches formula on a known input; bootstrap is reproducible with a fixed seed; resampling unit is the week (all tickers in a week move together) |
| `src/costs.py` | Cost charged once instead of per side; charged on HOLD→HOLD | Known position sequence → exact expected cost; no cost when position unchanged |
| `src/run_grid.py` | Overwrites results; not resumable; failure → HOLD | Re-running skips completed `run_id`s; failed run is logged with non-`ok` status; file only grows |
| Rating → position mapping | 5-level ratings mapped wrongly; unparseable → HOLD | Every documented rating string maps correctly; unknown string → `parse_error` |

Key formulas & definitions: `INSTRUCTIONS.md` §5.3 (log schema, rating mapping) and §7 (metrics, Sharpe SE, block bootstrap, DiD).

---

## 6. Coding conventions（代码规范）

- Type hints on public functions; short docstrings stating inputs, outputs, and units (e.g. "returns weekly simple returns, not percent").
- Keep `stats.py` and `costs.py` **pure** (no I/O, no globals) so they are easy to test.
- Use `logging`, not `print`, in `src/`.
- Tests in `tests/`, run with `pytest`. Tests must not call Ollama or the network — mock or use fixtures.
- Dates as ISO strings `YYYY-MM-DD` or `datetime.date`; never naive timestamps mixed with dates.
- Small commits, one topic each. Commit message format: `[Gav] <module>: <what changed>` or `[Aya] ...` — the tag is the owner who started the task, even when an AI wrote the code. Add an `AI-assisted: Codex` trailer line. Branches: `gav/<topic>` or `aya/<topic>`. Never push directly to `main`; open a PR. Full rules: `CONTRIBUTING.md`.
  （commit 前缀写发起任务的人，AI 写的代码也一样；末尾加 AI-assisted 说明；分支用 gav/ 或 aya/ 开头；不直接推 main，走 PR。）

---

## 7. Definition of done（任务完成标准）

一个任务只有在以下全部满足时才算完成：

- [ ] Code implements the spec in `INSTRUCTIONS.md` (or the task description) — no extra features
- [ ] Tests added and `pytest` passes locally
- [ ] No hard rule in §3 violated
- [ ] Any deviation from `INSTRUCTIONS.md` or upstream API differences are written down
- [ ] Report sent in the format of §8

---

## 8. Report format（每次任务结束的汇报格式）

请按下面格式汇报，方便 owner（Gav / Aya）贴到 PR 里，并转给 Claude 审查：

```
## Task
<一句话：做了什么>

## Files changed
- src/xxx.py — <改动>
- tests/test_xxx.py — <新增测试>

## Tests
<pytest 命令与结果；失败的也要列出>

## Deviations / assumptions
<与 spec 不同的地方、对 TradingAgents 源码的发现、做出的假设>

## Needs review
<需要重点审查的函数或逻辑，尤其是 §5 中的高风险部分>

## Open questions
<需要 owner 决定的问题>
```

不要声称"已测试"或"已验证"而实际没有运行；没跑的就写没跑。

---

## 9. Git & PR workflow for agents（AI 的分支与 PR 流程）

Human-facing version with diagrams: `CONTRIBUTING.md` §4.（给人看的完整流程见 CONTRIBUTING.md §4。）

1. **Know whose task it is.** The owner (Gav or Aya) who gave you the task sets the tag. If unsure, ask before committing.
   （先确认任务属于谁，前缀和分支都跟着这个人走。）
2. **Read the task from its GitHub Issue** when one exists: `gh issue view <n>`. Link it in the PR body with `Closes #<n>`.
3. **Start from fresh `main`:** `git switch main && git pull`, then `git switch -c <tag>/<topic>` (e.g. `aya/masking-spec`).
4. **Commit** as `[Tag] <module>: <what changed>` with a trailer line `AI-assisted: Codex` (or `Claude`). Use the repo's git identity; never pass `-c user.name/user.email`.
5. **Push only your task branch.** Never push to `main`. Never push to, rebase, or force-push another person's branch. Do not force-push your own branch once review has started — add new commits instead.
6. **Open the PR** with the same title as the commit; fill the body from `.github/pull_request_template.md` (it mirrors the §8 report). Use `--draft` if the task is not done.
7. **Never approve a PR, and never merge on your own initiative.** A PR is merged after the other owner approves; only merge when the PR's human author explicitly tells you to merge that specific PR.
   （AI 不点 Approve，也不自行合并；只有 PR 作者明确让你合并某个 PR 时才能合并。）
8. **Label AI comments:** start PR comments with `**Claude review (via Gav)**` or `**Codex (Aya)**` etc.
9. **If you cannot push or run `gh`** (sandbox / network), stop after the local commit and write "not pushed" in your report with the exact commands the human should run.
10. **Keep the README Status current.** The PR that finishes a task also updates the `📍 Status` section of `README.md`（完成任务的 PR 要同时更新 README 的进度表）.
11. **If `main` moved and your PR conflicts**, update your branch with `git merge origin/main` (not rebase after review started) and report what conflicted.
