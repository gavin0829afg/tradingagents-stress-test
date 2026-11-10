# TradingAgents Stress Test — Instructions（项目执行手册）

> 本文件是项目的**执行手册**：每一步做什么、怎么做、做到什么程度算完成。研究动机、文献和背景见 `PROJECT_SUMMARY.md`。
>
> **写法约定：** 流程说明用中文；项目内容（研究问题、实验设计、指标、配置）以英文为主、中文为辅。
>
> **Not financial advice.** Research and learning project only.（仅用于研究与学习，不构成投资建议。）

---

## 0. 怎么用这份手册

- 按周推进。每周开始前先看该周的**目标**和**完成标准**，结束时逐项打勾。
- 和原计划不一样的决定，一律写进 §11 Decision Log（日期 + 决定 + 原因），不要只记在脑子里。
- 标 **⚠️** 的条目是相对 `PROJECT_SUMMARY.md` 的修订，原因汇总在 §12。
- 标 **🔍** 的条目涉及 TradingAgents 的具体接口（类名、参数名、配置键）。这里写的是常见写法，**以你 pin 住的版本源码为准**，第一次用时请打开源码核对。
- 命令默认在 Windows PowerShell 中运行。

---

## 1. Project at a glance（项目一览）

**Core question:** Does any edge of TradingAgents survive a clean, cost-aware, statistically honest test?
（核心问题：在无前视偏差、计入交易成本、统计上诚实的测试下，TradingAgents 还剩下多少优势？）

| ID | Research question | 中文 | Exp |
|---|---|---|---|
| **RQ1** | Does the model perform better on dates **inside** its training data than **after** its cutoff? | 模型在"见过"的日期上是否表现更好（记忆 / 前视偏差） | 1 |
| **RQ2** | After costs and across seeds, is there a statistically meaningful edge over simple baselines? | 扣除成本、多种子之后，是否仍有显著超额 | 2 |
| **RQ3** | Is the multi-agent debate worth its extra cost? | 多智能体辩论是否值回额外成本 | 3 |
| **RQ4** *(side)* | Around earnings, does behavior change, and is the memorization gap larger? | 财报窗口内行为是否不同、记忆效应是否更强 | 4 |

### 1.1 Fixed settings（固定设定）

一旦定下，全程不改；如需修改，写进 Decision Log 并重跑受影响的实验。

| Setting | Value | 说明 |
|---|---|---|
| Model | `llama3.1:8b` via Ollama, served as `llama3.1-8k` | 知识截止 Dec 2023；本地免费 |
| Context length | `num_ctx = 8192` | 写进 Modelfile（见 §4.2） |
| Temperature | `0.7` ⚠️ | temperature=0 时不同 seed 几乎相同，多 seed 失去意义 |
| Seeds | `{1, 2}` default, `{1, 2, 3}` if budget allows ⚠️ | 视 Week 1 测速决定 |
| Analysts | `market` + `fundamentals` | news / social 只反映"现在"，不能用于历史回测 |
| Debate rounds | 1 (bull/bear), 1 (risk) | 控制 prompt 长度和耗时 |
| Decision frequency | Weekly, last trading day of each week | 每周最后一个交易日做决策 |
| Entry / holding | Enter at next close, hold 5 trading days | 下一个收盘价进场，持有 5 个交易日 |
| Universe | **Plan B default:** `JPM`, `BAC`, `WFC`, `C` ⚠️ | 加拿大银行作为可选（理由见 §12） |
| Benchmark | `SPY` + buy-and-hold of each stock | 可选补充：银行业 ETF `KBE` |
| In-sample period | 2023-01-01 → 2023-06-30 | 模型训练数据覆盖的时期 |
| Out-of-sample period | 2025-01-01 → 2025-06-30 | 模型知识截止之后，同一组日历月 |

---

## 2. Ground rules（全程规则）

1. **Pin everything.** TradingAgents commit hash, Ollama version, model digest → `results/RUN_INFO.md`. 项目中途不升级。
2. **Log every run, including failures.** 失败、超时、输出无法解析的运行都要记录，不能悄悄重跑覆盖。
3. **Point-in-time only.** 每条输入数据的时间戳必须 ≤ decision date。财报数据看 **filing date（提交日期）**，不是 period end（报告期末）。
4. **Pre-register before OOS.** 在看到 2025 结果之前，把实验网格、指标、显著性标准写进 Decision Log 并 commit。之后不再改。
5. **No cherry-picking.** 所有配置、所有种子的结果都进最终表格。
6. **Never commit** `.env`, API keys, Bloomberg data, or large raw logs.（大文件放 `results/raw/` 并 gitignore。）
7. **Findings, not advice.** 结论写成 "edge disappears out-of-sample after costs" 这种研究发现，不写交易建议。

---

## 3. Repo layout（仓库结构）

```
tradingagents-stress-test/
├── PROJECT_SUMMARY.md        # background & motivation（背景与动机）
├── INSTRUCTIONS.md           # this file（本执行手册）
├── README.md                 # public summary + results（对外展示）
├── .env.example              # key template; never commit .env
├── .gitignore                # .env, .venv/, external/, results/raw/
├── external/
│   └── TradingAgents/        # pinned clone, gitignored（锁定版本的上游代码）
├── configs/
│   ├── Modelfile             # llama3.1-8k definition
│   └── *.yaml                # experiment grids（每个实验一个 yaml）
├── src/
│   ├── run_grid.py           # resumable grid runner（可断点续跑）
│   ├── masking.py            # ⚠️ ticker / date / price masking layer
│   ├── costs.py              # commission + spread model
│   ├── stats.py              # Sharpe SE, block bootstrap, DiD
│   ├── baselines.py          # buy-and-hold, random, SMA rule
│   ├── earnings_events.py    # 8-K Item 2.02 dates + yfinance cross-check
│   ├── leak_check.py         # timestamp <= decision date checks
│   └── nodes/                # my own LangGraph node(s)
├── results/
│   ├── RUN_INFO.md           # versions & settings
│   ├── raw/runs.jsonl        # one line per run (gitignored if large)
│   └── tables/               # final CSV / markdown tables
├── notebooks/                # analysis + charts
└── writeup/                  # final report
```

---

## 4. Week 1 — Setup & pilot（第一周：环境搭建与试跑）

**目标：** 跑通 TradingAgents + 本地模型，测出单次运行的耗时、prompt 长度、失败率，填完 §4.6 的 go / no-go 表。
**完成标准：** §4.6 表格每一行都有结果和结论。

### 4.1 运行前准备

- 关闭 Discord / Steam / ChatGPT / Spotify / Snipping Tool（RAM 平时占用约 74%）。
- 电源设为"最佳性能"，接通电源；长时间运行前确认系统不会自动睡眠。

### 4.2 Install Ollama + model（安装 Ollama 和模型）

```powershell
winget install Ollama.Ollama
ollama pull llama3.1:8b
```

创建 `configs/Modelfile`：

```
FROM llama3.1:8b
PARAMETER num_ctx 8192
```

```powershell
ollama create llama3.1-8k -f configs/Modelfile
ollama run llama3.1-8k "Say hi in one word."
ollama ps
```

- **为什么要单独建 `llama3.1-8k`：** TradingAgents 通过 OpenAI 兼容接口调用 Ollama，这条路径通常不会传 `num_ctx`，默认 4K 会**静默截断**长 prompt。把 8192 写进模型本身最可靠。
- **检查 GPU：** `ollama ps` 的 PROCESSOR 列应显示 `100% GPU`。如果显示 CPU/GPU 混合，说明显存不够，速度会大幅下降。
- 记录 `ollama --version` 和 `ollama list` 里的模型 digest → `RUN_INFO.md`。

### 4.3 Install TradingAgents, pinned（安装并锁定版本）

```powershell
git clone https://github.com/TauricResearch/TradingAgents external/TradingAgents
cd external/TradingAgents
git checkout v0.7.1          # 修复了 EDGAR 日期泄漏 (#1488)，不要用 v0.7.0
git rev-parse HEAD           # 把 hash 写进 results/RUN_INFO.md
cd ../..
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e external/TradingAgents
```

🔍 最小调用示例（参数名以源码为准）：

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "ollama"
config["backend_url"] = "http://localhost:11434/v1"
config["deep_think_llm"] = "llama3.1-8k"
config["quick_think_llm"] = "llama3.1-8k"
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

ta = TradingAgentsGraph(selected_analysts=["market", "fundamentals"], config=config, debug=True)
final_state, decision = ta.propagate("JPM", "2023-03-10")
print(decision)
```

核对清单：
- [x] `temperature` 可从 config 传到 LLM；`seed` 不受 v0.7.1 config 支持，需在 Week 2 wrapper 层处理并验证。
- [ ] 数据源配置里 news / social 确实关闭了。
- [x] v0.7.1 最终评级为 5 档（Buy / Overweight / Hold / Underweight / Sell），未解析输出为 REVIEW；Week 2 按此确认 §5.3 映射。

#### v0.7.1 source audit（2026-11-06；只读源码）

- Config entry: `tradingagents/default_config.py` (`DEFAULT_CONFIG`). Ollama uses `llm_provider="ollama"`, with `backend_url="http://localhost:11434/v1"`; tier models use `deep_think_llm` / `quick_think_llm`.
- `temperature` is supported through config and forwarded by `tradingagents/llm_clients/factory.py`. There is no `seed` config key or forwarding in the factory, so seed control needs a wrapper-level implementation and verification.
- Create `TradingAgentsGraph(selected_analysts=["market", "fundamentals"], config=config)` to select the analysts. Set `max_debate_rounds` and `max_risk_discuss_rounds` in config.
- Final `propagate()` rating is five-tier: `Buy`, `Overweight`, `Hold`, `Underweight`, `Sell`, or `REVIEW` if no rating is parseable. The Portfolio Manager schema is in `tradingagents/agents/schemas.py`; fallback parsing is in `tradingagents/agents/rating.py`. The Trader's separate transaction action is three-tier (`Buy`, `Hold`, `Sell`).
- Built-in backtest: `tradingagents/backtest.py::run_backtest`. `holding_period_days` defaults to 5. Settlement in `tradingagents/memory/settlement.py::fetch_returns` enters at the first close after `trade_date` and exits after five more instrument trading sessions.
- Analyst-facing data tools are in `tradingagents/agents/tools.py`: `get_stock_data`, `get_indicators`, and fundamentals tools (`get_fundamentals`, `get_balance_sheet`, `get_income_statement`, `get_cashflow`). Vendor implementations are routed through `tradingagents/dataflows/router.py`; Yahoo price/indicator data is in `dataflows/vendors/yahoo/market.py`, and filing-date-filtered SEC statements are in `dataflows/vendors/sec_edgar.py`.
- Masking implication: tool-output wrapping belongs at the analyst tool boundary, but masking tool outputs alone does not hide identity/date because the graph resolves and injects real instrument context and `trade_date`. The wrapper must account for those graph inputs/context too.

### 4.4 Pilot runs（5 次试跑）

| # | Ticker | Date | 目的 |
|---|---|---|---|
| 1 | `JPM` | 2023-03-10 | SVB collapse week — strongest memorization probe（硅谷银行倒闭当周，记忆效应最可能出现） |
| 2 | `JPM` | 2025-03-07 | Same calendar week, after cutoff（截止日之后的同一周） |
| 3 | `RY` | 2023-03-10 | Plan A test: does EDGAR return fundamentals for a 40-F filer?（测试加拿大银行能否拿到基本面） |
| 4 | `BAC` | 2023-05-05 | Normal in-sample week（普通样本内周） |
| 5 | `WFC` | 2025-05-02 | Normal out-of-sample week（普通样本外周） |

每次运行记录：
- **Runtime**（总耗时，秒）
- **Max prompt tokens**（最长一次调用的输入长度；看 Ollama 返回的 `prompt_eval_count`，或查 `%LOCALAPPDATA%\Ollama\server.log` 里是否有截断提示）
- **Tool-call failures**（工具调用失败次数）
- **Fundamentals data dates**（基本面分析师拿到的数据最新 filing date 是否 ≤ decision date）
- **Final rating** and whether it parsed cleanly（最终评级能否被正确解析）

然后用相同 seed + temperature 把 #1 再跑一次，检查结果是否一致（determinism check）。

### 4.5 Read ai-hedge-fund（学习用，不运行）

- 读旧版 ai-hedge-fund 的代码，重点看：各 analyst 用哪些技术面 / 基本面信号、仓位和风控怎么写。
- 输出：`notes/ai-hedge-fund.md`，列出 5–10 个学到的投资概念，每个配一句中文解释。

### 4.6 Go / no-go checks（第一周检查表）

| Check | Pass criterion | Result | If fail |
|---|---|---|---|
| Install + 5 pilots | All finish without errors | | 修环境；必要时求助 |
| `RY` fundamentals on 2023 date | Fundamentals analyst has dated data ≤ decision date | | 维持 Plan B（默认已是 Plan B） |
| Tool calls (`llama3.1:8b`) | ≤ 1 failed run of 5 | | Exp 1 换 API 模型，缩短 OOS 窗口 |
| Prompt length | Most calls < 8K tokens, no truncation | | 减少 analyst，或长步骤用 API 模型 |
| Time per run | Measured & logged | | 按 §8 缩小网格 |
| Seed / temperature control | Same seed → same output; different seed → different | | 在 wrapper 层直接设置 LLM 参数 |
| Masking feasibility ⚠️ | Can intercept tool outputs for alias / rebasing | | 退回仅做 2023 vs 2025 对比，并在报告中写明局限 |

---

## 5. Week 2 — Evaluation wrapper（第二周：评估框架）

**目标：** 搭好可复用的评估框架，并亲手写一个 LangGraph node。
**完成标准：** 用小网格（2 stocks × 4 weeks × 1 seed × normal/masked）端到端产出一张完整结果表。

### 5.1 Modules（模块说明）

| Module | Responsibility | 要点 |
|---|---|---|
| `run_grid.py` | Expand a yaml grid into runs; call TradingAgents; append to `runs.jsonl` | **必须能断点续跑**：启动时跳过已完成的 `run_id`。笔记本跑通宵很可能中断。 |
| `masking.py` ⚠️ | Wrap data tools so the agent sees an alias, not the real company | 详见 §5.2 |
| `costs.py` | Commission + half-spread per trade | Default 5 bps per side; sensitivity 0 / 5 / 10 bps |
| `baselines.py` | Buy-and-hold, random (same trade frequency), SMA(10/30) crossover | Baselines 不调用 LLM，免费 |
| `stats.py` | Sharpe, Sharpe SE, block bootstrap by week, DiD CI | 详见 §7 |
| `earnings_events.py` | Earnings dates from 8-K Item 2.02 filing dates; cross-check with `yfinance` | 两个来源差 > 1 天的要人工核对 |
| `leak_check.py` | Assert every data item's timestamp ≤ decision date | 对每次运行的 tool 输出做检查，违规直接标记该 run |
| `nodes/` | My own LangGraph node | 推荐写 masking node 或 single-agent node（Exp 3 也要用） |

### 5.2 Masking design ⚠️（遮蔽设计，Exp 1 的关键）

**Goal:** the agent cannot tell which company or which date it is looking at, but receives the same information otherwise.
（目标：让模型认不出是哪家公司、哪个日期，但其他信息不变。）

| Item | Normal | Masked |
|---|---|---|
| Ticker / company name | `JPM`, "JPMorgan Chase" | `STOCK_A`, "a large US bank" |
| Dates | Real dates | Relative labels or a fixed synthetic offset |
| Prices | Raw | Rebased to 100 at window start |
| Volume | Raw | Normalized by trailing average |
| Fundamentals | Absolute $ values | Ratios & growth rates only (ROE, ROA, EPS growth, ...) |

实现思路：
- Wrapper 内部保存 `alias → real ticker` 和 `synthetic date → real date` 的映射；工具用真实值取数，再把输出遮蔽后交给 agent。
- 遮蔽后用正则扫描所有 tool 输出，确认没有残留的真实名称、ticker 或年份。
- **为什么需要 2025 年的 masked 组：** 遮蔽本身也会去掉合理信息（比如"JPM 是一家稳健的大银行"），所以即使没有记忆效应，masked 也可能比 normal 差。2025 年的 normal − masked 差距就是这部分"正常损失"的对照。

### 5.3 Run log schema（每次运行记录的字段）

`results/raw/runs.jsonl`, one JSON object per line:

```json
{
  "run_id": "exp1|JPM|2023-03-10|normal|full|seed1",
  "exp": "exp1", "ticker": "JPM", "decision_date": "2023-03-10",
  "period": "IS", "variant": "normal", "config": "full", "seed": 1,
  "model": "llama3.1-8k", "temperature": 0.7, "num_ctx": 8192,
  "ta_commit": "<hash>",
  "operator": "gav | aya", "machine": "<GPU model>",
  "status": "ok | tool_error | parse_error | timeout | leak",
  "rating_raw": "BUY", "position": 1,
  "max_prompt_tokens": 6120, "total_tokens": 31500, "runtime_s": 214,
  "log_path": "results/raw/logs/<run_id>.json",
  "started_at": "2026-11-12T22:01:03"
}
```

**Rating → position mapping（评级 → 仓位）:**
- 3-level: BUY = +1, HOLD = 0, SELL = −1
- 5-level: Buy = +1, Overweight = +0.5, Hold = 0, Underweight = −0.5, Sell = −1
- Report both **long-short** and **long-only**（long-only 把负仓位记为 0）
- **Failed runs are NOT silently HOLD.** 失败单独计数；主结果把失败按 HOLD 处理，同时报告失败率，并做一次剔除失败样本的稳健性检查。

---

## 6. Experiments（实验设计）

### Exp 1 — Memorization test (RQ1)（记忆效应测试）⚠️

**Design:** 2 × 2 grid — period (2023 IS vs 2025 OOS) × variant (normal vs masked).

| | Normal | Masked |
|---|---|---|
| **2023 (in-sample)** | A | B |
| **2025 (out-of-sample)** | C | D |

**Memorization gap（记忆差距）, difference-in-differences:**

$$
\text{Gap} = (A - B) - (C - D)
$$

- 对 hit rate、5-day alpha、Sharpe 分别计算，CI 用按周的 block bootstrap（§7）。
- **解读：** Gap 显著 > 0 → 模型在认得出公司和日期时，在见过的时期表现更好，支持记忆效应。只看 A vs C 不够，因为 2023 和 2025 的市场环境本身就不同。
- 单独报告 SVB 周（2023-03-06 ~ 2023-03-17）作为案例分析。

### Exp 2 — Costs + statistics (RQ2)（成本与统计）

**Design:** reuse Exp 1 "normal" runs; apply costs post-hoc（直接复用 Exp 1 的 normal 组运行，事后计算成本，不需要额外 LLM 调用）.

- **Costs:** commission + half-spread per side; sensitivity at 0 / 5 / 10 bps.
- **Baselines:** buy-and-hold, always-BUY, random trades (same turnover), SMA(10/30) crossover.
- **Report:** net-of-cost return, Sharpe with SE and bootstrap 95% CI, turnover.
- **Key comparison:** agent vs always-BUY. 如果 hit rate 不比"永远买入"高，所谓的方向判断能力就不存在。

### Exp 3 — Is the debate worth it? (RQ3)（辩论是否值得）

| Config | Pipeline |
|---|---|
| `full` | analysts → bull/bear debate → trader → risk team → portfolio manager |
| `no_debate` | analysts → trader → risk team → portfolio manager |
| `single` | one LLM reads the same tool outputs and decides directly |

- **Period:** 2025 OOS only（只在样本外跑，避免记忆效应干扰对比）。`full` 复用 Exp 1 的 C 组。
- **Record:** net-of-cost return, Sharpe, **tokens per decision, runtime per decision**.
- `single` 可以作为你自己写的 LangGraph node（Week 2 的 node 作业）。

### Exp 4 — Earnings event lens (RQ4, side)（财报事件视角，副实验）

- **Events:** quarterly earnings dates for each stock in 2023 and 2025（美国银行一般在 1/4/7/10 月中旬发布）。只用落在 Exp 1 时间窗口内或相邻的季度。
- **Offsets:** run at **T−1** and **T+1** trading days.
- **Matched controls:** same stock, same offset, 2–3 weeks away from any earnings date ⚠️（原计划的 160 次没有算对照组）。
- **Metrics:** direction hit rate, 5-day alpha; compare earnings vs control × IS vs OOS × normal vs masked if budget allows.
- **预期：** news 关闭时，T+1 的 agent 通常还看不到财报结果（10-Q 要几周后才上 EDGAR），所以 T+1 测的主要是记忆，而不是对财报的真实反应。这正是它作为 RQ1 "放大镜"的价值。
- **Stretch:** point-in-time 8-K Item 2.02 exhibit reader（让 agent 在 T+1 读到真实财报新闻稿），仅在进度很好时做。

---

## 7. Metrics & statistics（指标与统计方法）

| Metric | Definition | 中文说明 |
|---|---|---|
| Hit rate | Share of non-HOLD decisions where sign(position) = sign(5-day excess return vs SPY) | 只算非 HOLD 决策；同时报告 HOLD 比例 |
| Base rate | Share of weeks with positive 5-day excess return | "永远买入"能达到的 hit rate，是真正的对照线 |
| 5-day alpha | Position × (stock return − SPY return) over the holding window | 简单超额，不做因子回归 |
| Sharpe | Mean / std of weekly net returns × √52 | 年化 |
| Failure rate | Failed runs / total runs, by period & config | 2025 失败率更高本身就可能制造假"记忆差距" |

**Sharpe standard error (iid approximation):**

$$
\text{SE}(\widehat{SR}) \approx \sqrt{\frac{1 + \tfrac{1}{2}\widehat{SR}^{2}}{T}}
$$

- T = 26 周时，周度 SE ≈ 0.2，年化后约 **1.4**。在写作中明确说明：短窗口下 Sharpe 几乎无法区分好坏。

**Bootstrap（重抽样）:**
- Resample **weeks**, not individual decisions — 同一周的 4 只银行股高度相关，按决策抽样会严重低估误差。
- Block bootstrap with block length ≈ 4 weeks, 10,000 resamples, percentile 95% CI.
- DiD 的 CI 用同一套 bootstrap：每次重抽样同时重算 A、B、C、D。

**Power check（功效估算）:**
- 约 100 次非 HOLD 决策时，hit rate 的 95% CI 大约是 ±10 pp。小于这个量级的差异检测不出来，结果部分要直说。

---

## 8. Run budget（算力预算）

Week 1 测出单次耗时后，替换下表中的 3 分钟。

| Exp | Grid | Runs |
|---|---|---|
| 1 | 4 stocks × 26 weeks × 2 periods × 2 variants × 2 seeds | 832 |
| 2 | Reuses Exp 1 normal runs; baselines are free | 0 |
| 3 | 4 stocks × 26 weeks × 2 new configs × 2 seeds (2025 only) | 416 |
| 4 | 4 stocks × 4 quarters × 2 years × 2 offsets × 2 seeds × (event + control) | 256 |
| **Total** | | **≈ 1,500** |

按每次 3 分钟算约 75 小时 GPU 时间。每晚跑 10 小时，大约需要 8 个晚上。

**超预算时按以下顺序缩减：**
1. Exp 4 只跑 masked = normal（不做遮蔽对比）
2. Exp 3 的 `no_debate` 只跑 1 个 seed
3. Exp 1 窗口从 26 周缩到 13 周（Q1 only）
4. 最后才减股票数量（Exp 1 至少保留 3 只）

---

## 9. Weeks 3–6（第三到六周）

| Week | Work | 完成标准 |
|---|---|---|
| 3 | **Pre-register**（写入 Decision Log 并 commit）→ Exp 1 IS + OOS runs start | Exp 1 至少完成一半，`runs.jsonl` 通过 `leak_check` |
| 4 | Finish Exp 1; Exp 2 analysis; Exp 4 runs | Exp 1 / 2 结果表进 `results/tables/` |
| 5 | Exp 3 ablation; Exp 4 analysis | 所有实验结果表完成 |
| 6 | Charts, README, write-up, 2-min demo; upstream issue / PR if a leak is found | Repo 公开 |

每周结束时的固定动作：
- [ ] `RUN_INFO.md` 与实际设置一致
- [ ] Decision Log 已更新
- [ ] 失败 run 已统计，没有被覆盖
- [ ] commit + push

### 9.1 Write-up outline（报告结构）

1. **Question & why it matters** — the evidence gap in the original paper
2. **Setup** — model, data, universe, costs, masking
3. **Results** — one table per RQ, with CIs and failure rates
4. **What this does and does not show** — power limits, short windows, single small model
5. **Lessons** — what I learned about agents and about backtesting

结果表述示例：*"The memorization gap in hit rate is +X pp (95% CI: [a, b]); we cannot rule out zero."*（"记忆差距为 +X 个百分点，95% CI 包含 0，无法排除无效应。"）

---

## 10. Budget（费用）

| Item | Cost |
|---|---|
| TradingAgents, Yahoo, SEC EDGAR, Ollama, local model | $0 |
| Optional API model (Exp 2/3 only if local fails) | Hard cap **$30** |

使用 API 模型时：在服务商后台设置消费上限，并在 `runs.jsonl` 里记录每次运行的 token 数。

⚠️ **Cutoff rule（知识截止规则）：** any model used to *evaluate performance* must have a knowledge cutoff **before** the test window. 新一代 API 模型（如 Claude Haiku / Sonnet / Opus 5.5）的训练数据已经覆盖 2023 和 2025，在这两个时期上跑出的收益不能作为干净的样本外结果。它们只能用于：(a) 对照性的记忆探针（预期 normal ≫ masked），或 (b) 截止日之后的时期。

---

## 11. Decision log（决策日志）

| Date | Decision | Reason |
|---|---|---|
| 2026-11-05 | TradingAgents (main) + ai-hedge-fund (read-only learning) | — |
| 2026-11-05 | Local model, 8 GB VRAM, `num_ctx` 8K; analysts = market + fundamentals | 免费；news/social 无法回测 |
| 2026-11-06 | Added Exp 4 (earnings event lens) as side experiment tied to RQ1 | 财报窗口是记忆效应最强的地方 |
| 2026-11-06 | Exp 1 → 2×2 normal/masked design (DiD) | 区分记忆效应与市场环境变化 |
| 2026-11-06 | Plan B (US banks) as default universe | 加拿大银行季报为 6-K，通常无 XBRL |
| 2026-11-06 | Temperature 0.7, seeds vary | temperature=0 下 seed 几乎无效 |
| 2026-11-06 | Per-run isolated memory_log_path; project-local data_cache_dir | 默认共用的记忆文件会造成时间泄漏和遮蔽失效 |
| 2026-11-06 | Pin TradingAgents **v0.7.1** (commit `c4544913a14e`), not v0.7.0 | v0.7.1 修复了前视泄漏：未补零的日期（如 `2024-7-5`）会让 EDGAR 返回决策日之后的财报 (#1488)；还修复了财报季度错位 (#1517) 和按未收盘 K 线计分 (#1548) |
| 2026-11-06 | Agent model built: `llama3.1-8k`, verified 8K context on `/v1`, 100% GPU | 7,025-token 测试 prompt 未被截断 |
| | *(Week 1 results go here)* | |

---

## 12. Changes vs `PROJECT_SUMMARY.md`（相对原计划的修订）

| # | Change | 原因 |
|---|---|---|
| 1 | Exp 1 adds a **masked** variant; main metric is DiD | 只比较 2023 vs 2025 时，记忆效应和市场环境差异混在一起，无法区分 |
| 2 | Default universe → **US banks** (`JPM`, `BAC`, `WFC`, `C`) | 加拿大五大行是外国私人发行人：年报为 40-F，季报为 6-K（通常无 XBRL 财务数据），也不提交 8-K Item 2.02 |
| 3 | Temperature fixed at **0.7** | temperature=0 时不同 seed 的输出几乎一样 |
| 4 | Bootstrap **by week**, not by decision | 同周的银行股高度相关，有效样本量接近周数而不是决策数 |
| 5 | Compare hit rate to **always-BUY base rate** | 上涨行情中"永远买入"本身就有 > 50% 的 hit rate |
| 6 | Failed runs logged as their own status | 失败默认变成 HOLD 会压低 hit rate；如果 2025 更容易失败，会制造假的记忆差距 |
| 7 | Exp 4 adds matched controls (160 → 256 runs incl. seeds/stocks change) | 原计数没有包含非财报对照组 |
| 8 | Pre-registration before OOS runs | 防止看到结果后再调整指标 |
