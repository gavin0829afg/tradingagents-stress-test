# TradingAgents Stress Test

**Does any edge of an LLM multi-agent trading system survive a clean, cost-aware, statistically honest test?**
（一个多智能体 LLM 交易框架，在无前视偏差、计入成本、统计诚实的测试下，还剩多少优势？）

We take the open-source [TradingAgents](https://github.com/TauricResearch/TradingAgents) framework (pinned at v0.7.1), run it on a local model with a known knowledge cutoff (`llama3.1:8b`, Dec 2023), and test whether its results come from real skill or from the model having memorized the answers.
"The edge disappears" is a valid result.

> Research and learning project. **Not financial advice.**

---

## 👋 Start here（第一次打开仓库，按这个顺序看）

| If you are… | Read |
|---|---|
| **Anyone** | This README → **Status** below（项目在做什么、做到哪了） |
| **Gav / Aya** | [`CONTRIBUTING.md`](CONTRIBUTING.md) — 署名、分支、PR 流程 |
| **An AI agent (Codex / Claude)** | [`AGENTS.md`](AGENTS.md) — 硬性规则和 PR 流程（Codex 会自动读取；Claude 通过 `CLAUDE.md` 读取） |
| **Doing a task** | [`INSTRUCTIONS.md`](INSTRUCTIONS.md) — 每一步怎么做、做到什么程度算完成 |
| **Wanting the why** | [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) — 研究动机、文献背景 |

**Your next task** is an open GitHub Issue assigned to you（分配给你的 Issue 就是你的下一个任务）.

---

## Research questions（研究问题）

| ID | Question | 中文 |
|---|---|---|
| RQ1 | Does the model do better on dates **inside** its training data than **after** its cutoff? | 模型是不是在"背答案"？ |
| RQ2 | After trading costs and across seeds, is there a statistically meaningful edge over simple baselines? | 扣成本后还有没有显著优势？ |
| RQ3 | Is the multi-agent debate worth its extra cost? | 多智能体辩论值不值？ |
| RQ4 *(side)* | Is the memorization gap larger around earnings? | 财报周记忆效应是否更强？ |

Key design: a 2×2 test — period (2023, seen by the model / 2025, unseen) × variant (normal / **masked**: company name, dates, and absolute prices hidden). Memorization gap = difference-in-differences. Details: `INSTRUCTIONS.md` §6.

---

## Team & tools（分工）

| Who | Tools | Role |
|---|---|---|
| **Gav** (Gavin Li, `gavin0829afg`) | Claude (design & review) + Codex (implementation) | Owner |
| **Aya**（艾亚，`ayaw888`） | Codex (implementation) | Owner |

Every commit, branch, and PR is tagged with whose task it is: `[Gav]` / `[Aya]`, `gav/…` / `aya/…`. AI-written code carries an `AI-assisted:` line. Nothing goes to `main` without a PR approved by the other person.

---

## 📍 Status（当前进度）

> **Update this section in the PR that finishes a task.**（完成任务的 PR 顺手更新这里。）

**Week 1 of 6 — setup & pilot**（第一周：环境搭建与试跑）

| Done ✅ | Next ⬜ |
|---|---|
| Plan, rules, and docs | **Pilot script** (`src/pilot.py`, isolated memory per run, seed via Modelfile) — Gav |
| Repo skeleton, Python 3.12 venv, pinned deps | **5 pilot runs** + fill go/no-go table (`INSTRUCTIONS.md` §4.6) — Gav |
| Ollama + `llama3.1-8k` (8K context verified, 100% GPU) on Gav's machine | **Aya's environment setup** (`INSTRUCTIONS.md` §4.2–4.3) — Aya |
| TradingAgents pinned at v0.7.1 + source audit | **Masking spec** written into `INSTRUCTIONS.md` §5.2 (needed before Week 2) |
| Rule 6a: isolate agent memory per run (found a leak risk) | |

Key decisions so far: `INSTRUCTIONS.md` §11 Decision Log.

---

## Repo map（目录）

```
AGENTS.md / CLAUDE.md     rules for AI agents
CONTRIBUTING.md           rules for the two of us
INSTRUCTIONS.md           step-by-step plan, experiment design, decision log
configs/                  Ollama Modelfile, experiment grids (yaml)
src/                      our code (masking, costs, stats, leak checks, runner)
external/TradingAgents/   pinned upstream clone (gitignored — install per INSTRUCTIONS §4.3)
results/RUN_INFO.md       versions & settings of every machine that runs experiments
results/raw/              raw run logs (gitignored)
results/tables/           summary tables (committed)
```

## Setup（环境）

Full steps: `INSTRUCTIONS.md` §4. Reproduce the Python environment with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock
```
