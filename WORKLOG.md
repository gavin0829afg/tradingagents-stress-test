# WORKLOG — Who did what, when（工作记录）

> 按时间顺序记录两个人各自完成了什么。**做之前先看这里和 README 的 Status：别人已经做过的，不用再做。**
>
> 每个完成任务的 PR 在表格最下面加一行（AI 也要遵守，见 `AGENTS.md` §9）。只记已完成的事，计划中的事写在 README Status 和 GitHub Issue 里。

| Date | Who | What（做了什么） | Link |
|---|---|---|---|
| 2026-11-05 | Gav | Chose TradingAgents as the main framework; wrote the first project plan | `deceff7:PROJECT_SUMMARY.md` (first plan) |
| 2026-11-06 | Gav (+Claude) | Revised the design: 2×2 normal/masked memorization test, US banks as default universe, week-level bootstrap, temperature 0.7 | `INSTRUCTIONS.md` §11 |
| 2026-11-06 | Gav (+Claude) | Wrote the execution manual and AI rules | `INSTRUCTIONS.md`, `AGENTS.md`, `CLAUDE.md` |
| 2026-11-06 | Gav (+Codex) | Repo skeleton, Python 3.12 venv, pinned dependencies | `deceff7`, `d4d71f8` |
| 2026-11-06 | Gav (+Claude) | Installed Ollama 0.40.15; built `llama3.1-8k`, verified 8K context and 100% GPU on Gav's machine | `results/RUN_INFO.md` |
| 2026-11-06 | Gav (+Codex) | Pinned TradingAgents v0.7.1 (fixes an EDGAR look-ahead leak); read-only source audit (temperature, seed, ratings, identity injection) | `ec51944`, `INSTRUCTIONS.md` §4.3 |
| 2026-11-06 | Gav (+Claude, Codex) | Found that agent memory is shared across runs (leak risk); added rule 6a: isolate memory per run | `10d1e8c`, `AGENTS.md` rule 6a |
| 2026-11-09 | Gav (+Claude) | Created the private GitHub repo; wrote two-person collaboration rules; invited Aya | `a70587a`, PR #1 |
| 2026-11-09 | Gav (+Claude) | Made the repo self-explanatory: README start page, AI PR workflow, PR template, this worklog; consolidated docs (one topic per file, PROJECT_SUMMARY → background only) | PR #2 |
| 2026-11-09 | Aya | Invited as collaborator (`ayaw888`) | — |
| 2026-11-09 | Gav (+Claude) | Wrote masking spec v1: +56-year date shift, decision-date price anchor, indicator classes, ratio-only fundamentals, leak vs identity-guess scan | PR #3, `INSTRUCTIONS.md` §5.2 |
| 2026-11-16 | Gav (+Codex, Claude review) | Pilot runner: `src/pilot.py`, `configs/pilot.yaml`, seed Modelfiles, 9 tests (isolated memory per run, REVIEW → `parse_error`, append-only log) | PR #5, closes #4 |
| 2026-11-16 | Gav (+Claude) | Prepared the repo for public release: English README (method, findings so far, pending-results table, pipeline diagram), MIT license | PR #6 |
