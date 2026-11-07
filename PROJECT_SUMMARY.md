# TradingAgents Stress Test — Project Summary

> A 6-week portfolio project. I take the open-source **TradingAgents** framework (multi-agent LLM trading, built on LangGraph) and test it under stricter conditions: a model that cannot "remember" the answers, real trading costs, proper statistics, and a look at earnings weeks.

- **Owner:** Gav (Gavin Li), University of Waterloo — FARM + Statistics
- **Start date:** Nov 2026
- **Status:** Week 1 (setup + pilot runs)
- **Not financial advice.** This is a research and learning project only.

---

## 1. Goals

**Learning goals**
1. Understand how an agent workflow really works: tools, state, parallel nodes, multi-agent debate, structured output, memory, checkpoints (LangGraph).
2. Learn practical trading / investing concepts: technical and fundamental signals, alpha vs. benchmark, trading costs, backtest biases (look-ahead, overfitting), earnings events.

**Deliverable**
A public GitHub repo with: a reusable evaluation wrapper around TradingAgents, a clear results table, charts, and a short write-up that answers the research questions below honestly — even if the answer is "the edge disappears."

---

## 2. Why this project

TradingAgents is one of the most-starred LLM trading repos, but its published results are weak evidence:

- The original paper backtested only about three months (Jan 1 – Mar 29, 2024) on a few large US tech stocks, without slippage or taxes.
- An outside check found that one buy-and-hold baseline in the paper had the wrong sign (paper: AAPL −5.23%; recomputed from Yahoo adjusted prices: +9.12%).
- Another paper reports that a TradingAgents portfolio's Sharpe fell from 0.43 to 0.22 after costs, and that short-window Sharpe ratios have very wide confidence intervals.
- **Parametric look-ahead bias:** an LLM trained on later data may already "know" what happened on the backtest dates. Data-level filtering does not fix this (see TradingAgents issue #805).

So the interesting question is not "can it make money?" but **"does any edge survive a clean, cost-aware, statistically honest test?"**

References: `arxiv.org/abs/2412.20138` (TradingAgents), `alphaxiv.org/abs/2605.16895` (Alpha Illusion), `arxiv.org/abs/2601.13770` (Look-Ahead-Bench), `arxiv.org/abs/2512.23847` (LAP test for look-ahead bias).

---

## 3. Research questions

| ID | Question | Main or side |
|---|---|---|
| **RQ1** | Does the same model perform better on dates **inside** its training data than on dates **after** its knowledge cutoff? (memorization / look-ahead) | Main |
| **RQ2** | After trading costs and across several random seeds, is there any edge over simple baselines, and is it statistically meaningful? | Main |
| **RQ3** | Is the multi-agent debate worth its extra cost? (full pipeline vs. no debate vs. single agent) | Main |
| **RQ4** | Around **earnings announcements**, does the agent behave differently, and is the memorization gap larger there? | Side (event lens) |

---

## 4. Setup

### 4.1 Hardware
- Windows laptop: Intel Core Ultra 7 255HX, 16 GB RAM, NVIDIA RTX GPU with **8 GB VRAM**.
- Close Discord / Steam / ChatGPT / Spotify / Snipping Tool before long runs (RAM sits ~74% otherwise).

### 4.2 Software
- Python 3.11+ (venv or uv), Git, GitHub.
- **TradingAgents — pin one version** (latest checked: v0.7.0, Oct 2026). Record the commit hash in `results/RUN_INFO.md`. Do not upgrade mid-project.
- Ollama for Windows (local models).

### 4.3 Models
| Use | Model | Why |
|---|---|---|
| RQ1 (main) | `llama3.1:8b` via Ollama | Known knowledge cutoff: **Dec 2023**. Free, runs on 8 GB VRAM. |
| RQ2 / RQ3 (optional) | Cheap API model or ChatGPT Plus subscription mode | Better tool calling; use only if local model is unstable. |

**Ollama settings:** context length **8192** (`num_ctx`). Default is 4K on GPUs under 24 GB VRAM, which can silently cut long prompts. 32K does not fit in 8 GB VRAM.

### 4.4 Data (all free)
| Data | Source | Note |
|---|---|---|
| Prices, indicators | Yahoo Finance (built into TradingAgents) | Canada uses `.TO`; US listings use plain tickers |
| US fundamentals | SEC EDGAR (built in, point-in-time, no key) | Covers foreign SEC filers too |
| Earnings dates | SEC 8-K **Item 2.02** filing dates (US filers); `yfinance` `get_earnings_dates(limit=...)` as cross-check | Bloomberg only for manual cross-checking — **never commit Bloomberg data** |

### 4.5 Fixed design choices
- **Analysts:** `market` + `fundamentals` only. News / social sources are not reliable for historical dates (the README notes they reflect "now"), so they are excluded from backtests.
- **Debate rounds:** 1 (shorter prompts, lower cost).
- **Decision frequency:** weekly.
- Entry at the first close after each decision date (TradingAgents backtest default).

### 4.6 Stock universe
- **Plan A:** Canadian big banks through their US listings — `RY`, `TD`, `BMO`, `BNS`, `CM`.
- **Plan B (if historical fundamentals fail for Plan A):** US large banks — `JPM`, `BAC`, `WFC`, `C`.
- Benchmark: TradingAgents' regional benchmark + buy-and-hold of each stock.

---

## 5. Experiments

### Exp 1 — Memorization test (RQ1)
- Same model (`llama3.1:8b`), same settings, two periods:
  - **In-sample:** 6 months in 2023 (model "has seen" this period)
  - **Out-of-sample:** the same 6 calendar months in 2025 (after the cutoff)
- Compare hit rate, alpha, Sharpe. A clear drop out-of-sample suggests memorization.

### Exp 2 — Costs + statistics (RQ2)
- Apply commission + bid-ask spread to every trade.
- 3 random seeds per configuration (LLM output is non-deterministic).
- Baselines: buy-and-hold, random trades, simple moving-average rule.
- Bootstrap confidence intervals for Sharpe. Approximate standard error:

$$
\text{SE}(\widehat{SR}) \approx \sqrt{\frac{1 + \tfrac{1}{2}\widehat{SR}^{2}}{T}}
$$

where $\widehat{SR}$ = estimated Sharpe ratio and $T$ = number of return periods. Short windows → large error.

### Exp 3 — Is the debate worth it? (RQ3)
| Config | Pipeline |
|---|---|
| Full | analysts → bull/bear debate → trader → risk team → portfolio manager |
| No-debate | debate removed |
| Single | one LLM decides directly |

Record net-of-cost return, Sharpe, and **token cost / runtime per decision**.

### Exp 4 — Earnings event lens (RQ4, side)
**Idea (from my Bloomberg Trading Challenge experience):** price moves around earnings are large, so earnings weeks are a natural stress test.

**Why it is a side experiment, not the main goal**
1. **Small sample:** about 4 earnings per stock per year.
2. **Information gap:** with news turned off, the agent does not "see" the earnings result until the 10-Q / 40-F reaches EDGAR, often weeks later. So post-earnings reaction cannot be tested cleanly.
3. **Literature:** post-earnings drift in large caps has mostly disappeared since the mid-2000s (Martineau, 2022), so a big post-earnings edge is not expected.

**Why it is still valuable**
- Earnings outcomes are heavily reported online, so this is where **memorization should be strongest**. If Exp 1 finds a memorization gap, it should be **largest in earnings windows**. That makes Exp 4 a sharp test of RQ1.

**Design**
- Event list: earnings dates for each stock, in-sample year (2023) and out-of-sample year (2025).
- Run the agent at **T−1** (day before earnings) and **T+1** (day after) trading days.
- Compare with matched **non-earnings dates** (same stock, nearby weeks).
- Metric: direction hit rate and 5-day alpha; in-sample vs. out-of-sample; earnings vs. non-earnings.

Run count (5 stocks × 4 quarters × 2 years × 2 offsets × 2 seeds):

$$
5 \times 4 \times 2 \times 2 \times 2 = 160 \text{ runs}
$$

**Main-goal upgrade (only if week-1 checks go very well):** turn on a point-in-time earnings-release reader (8-K Item 2.02 exhibit text) so the agent can read the actual results at T+1. Treat as stretch work.

---

## 6. Week-1 checks (go / no-go)

| Check | Pass | If fail |
|---|---|---|
| Install + 5 pilot runs on Windows | Runs finish without errors | Fix env; ask for help |
| `RY` (US ticker) gets historical fundamentals from EDGAR | Fundamentals analyst has data on a 2023 date | Switch to Plan B (US banks) |
| `llama3.1:8b` tool calls | Low failure rate in 5 runs | Use API model for Exp 1, shorter OOS window |
| Prompt length vs 8K | Most prompts < 8K tokens | Fewer analysts or API model for long steps |
| Time / cost per run | Measured and logged | Shrink grid |

Total runs estimate (adjust after pilot):

$$
\text{total runs} = \text{stocks} \times \text{dates} \times \text{configs} \times \text{seeds}
$$

---

## 7. Timeline (6 weeks)

| Week | Work | Done when |
|---|---|---|
| 1 | Install Ollama + TradingAgents; read old ai-hedge-fund code (free, for investing concepts); pilot runs; week-1 checks | Checks table filled in |
| 2 | Evaluation wrapper: costs, seeds, bootstrap CI, timestamp-leak check; **write one custom LangGraph node** myself | One full results table from a tiny grid |
| 3 | Exp 1 + Exp 2 | Results saved |
| 4 | Exp 1 + Exp 2 (finish) + **Exp 4** (reuses same machinery) | Results saved |
| 5 | Exp 3 (ablation) | Results saved |
| 6 | Charts, README, write-up, 2-min demo; open issue/PR upstream if a leak is found | Repo public |

---

## 8. Budget

| Item | Cost |
|---|---|
| TradingAgents, Yahoo, SEC EDGAR, Ollama, local model | $0 |
| ai-hedge-fund (read old version's code) | $0 |
| Optional API model for Exp 2/3 | ~$10–40 (set a $30 cap) |
| **Expected total** | **$0–50** |

---

## 9. Proposed repo structure

```
.
├── PROJECT_SUMMARY.md        # this file
├── README.md                 # public-facing summary + results
├── .env.example              # keys template (never commit .env)
├── configs/                  # experiment configs (yaml)
├── src/
│   ├── run_grid.py           # wraps TradingAgents run_backtest
│   ├── costs.py              # commission + spread model
│   ├── stats.py              # bootstrap CI, Sharpe SE
│   ├── earnings_events.py    # earnings dates (8-K Item 2.02, yfinance)
│   ├── leak_check.py         # timestamp <= decision date checks
│   └── nodes/                # my own LangGraph node(s)
├── results/
│   ├── RUN_INFO.md           # TradingAgents version, model, settings
│   └── raw/                  # per-run logs (gitignored if large)
├── notebooks/                # analysis + charts
└── writeup/                  # final report
```

---

## 10. Rules for this repo

- Pin the TradingAgents version; log model name, temperature, context length, seed for every run.
- Never commit API keys or Bloomberg data.
- Report all runs, including failed or bad ones. No cherry-picking.
- Write results as findings ("edge disappears out-of-sample after costs"), not as trading advice.

---

## 11. Learning resources

- What are AI Agents? (IBM) — https://www.youtube.com/watch?v=F8NKVhkZZWI
- TradingAgents demo — https://www.youtube.com/watch?v=90gr5lwjIho
- Look-ahead bias in trading bots — https://www.youtube.com/watch?v=3oKGO96RHUw
- AI Agents in LangGraph (DeepLearning.AI, ~1.5 h) — https://www.deeplearning.ai/courses/ai-agents-in-langgraph
- TradingAgents repo — https://github.com/TauricResearch/TradingAgents

---

## 12. Decision log

| Date | Decision |
|---|---|
| 2026-11-05 | Chose TradingAgents (main) + ai-hedge-fund (read-only learning). |
| 2026-11-05 | Local model on Windows (8 GB VRAM), context 8K; analysts = market + fundamentals. |
| 2026-11-06 | Added Exp 4 (earnings event lens) as a side experiment tied to RQ1. |
