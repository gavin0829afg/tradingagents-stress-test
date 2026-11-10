# TradingAgents Stress Test — Background（项目背景）

> **本文件只讲"为什么做"。** 当前的设计、设定、实验和进度一律以 [`INSTRUCTIONS.md`](INSTRUCTIONS.md) 和 [`README.md`](README.md) 为准。
> 第一版完整计划（加拿大银行、v0.7.0 等已被替换的设定）保存在 git 历史中：`git show deceff7:PROJECT_SUMMARY.md`。修改原因见 `INSTRUCTIONS.md` §11 Decision Log。
>
> **Not financial advice.** Research and learning project only.

A 6-week portfolio project by **Gav** (Gavin Li, University of Waterloo — FARM + Statistics) and **Aya**（艾亚）, started Nov 2026. We take the open-source **TradingAgents** framework (multi-agent LLM trading on LangGraph) and test it under stricter conditions: a model that cannot "remember" the answers, real trading costs, proper statistics, and a look at earnings weeks.

---

## 1. Goals（目标）

**Learning goals**
1. Understand how an agent workflow really works: tools, state, parallel nodes, multi-agent debate, structured output, memory, checkpoints (LangGraph).
2. Learn practical trading / investing concepts: technical and fundamental signals, alpha vs. benchmark, trading costs, backtest biases (look-ahead, overfitting), earnings events.

**Deliverable**
A public GitHub repo with a reusable evaluation wrapper around TradingAgents, a clear results table, charts, and a short write-up that answers the research questions honestly — even if the answer is "the edge disappears."

---

## 2. Why this project（为什么做）

TradingAgents is one of the most-starred LLM trading repos, but its published results are weak evidence:

- The original paper backtested only about three months (Jan 1 – Mar 29, 2024) on a few large US tech stocks, without slippage or taxes.
- An outside check found that one buy-and-hold baseline in the paper had the wrong sign (paper: AAPL −5.23%; recomputed from Yahoo adjusted prices: +9.12%).
- Another paper reports that a TradingAgents portfolio's Sharpe fell from 0.43 to 0.22 after costs, and that short-window Sharpe ratios have very wide confidence intervals.
- **Parametric look-ahead bias:** an LLM trained on later data may already "know" what happened on the backtest dates. Data-level filtering does not fix this (see TradingAgents issue #805).

So the interesting question is not "can it make money?" but **"does any edge survive a clean, cost-aware, statistically honest test?"**
（关键问题不是"能不能赚钱"，而是"去掉各种水分之后还剩多少"。）

Earnings weeks (RQ4) came from Gav's Bloomberg Trading Challenge experience: price moves around earnings are large, and earnings outcomes are heavily reported online — so that is where memorization should be strongest.

---

## 3. References（文献）

- TradingAgents — `arxiv.org/abs/2412.20138`
- Alpha Illusion — `alphaxiv.org/abs/2605.16895`
- Look-Ahead-Bench — `arxiv.org/abs/2601.13770`
- LAP test for look-ahead bias — `arxiv.org/abs/2512.23847`
- Post-earnings drift in large caps has mostly disappeared since the mid-2000s — Martineau (2022)

---

## 4. Learning resources（学习资源）

- What are AI Agents? (IBM) — https://www.youtube.com/watch?v=F8NKVhkZZWI
- TradingAgents demo — https://www.youtube.com/watch?v=90gr5lwjIho
- Look-ahead bias in trading bots — https://www.youtube.com/watch?v=3oKGO96RHUw
- AI Agents in LangGraph (DeepLearning.AI, ~1.5 h) — https://www.deeplearning.ai/courses/ai-agents-in-langgraph
- TradingAgents repo — https://github.com/TauricResearch/TradingAgents
- ai-hedge-fund (read the old version's code for investing concepts; not run)
