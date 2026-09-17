# backtest-audit-kit

**"I verify whether your strategy is real — or whether the backtest lied to you."**

A tiny, dependency-free toolkit that audits a backtest the way an accountant
audits a ledger and a QA engineer audits a test suite. It does not sell you
returns; it finds the four ways a backtest most often lies.

---

## English

**What it is.** A pure standard-library (Python 3.9+) kit of four independent
checkers for a trading backtest:

| Checker | Question it answers |
|---|---|
| `checks/lookahead.py` | Does any decision on bar `i` see bars `i+1...`? (AST-based future-function lint) |
| `checks/invariants.py` | Does the ledger obey accounting invariants? (equity identity, `wd_cum` carry, monotonic counters, non-negative balances) |
| `checks/mutants.py` | Which bugs would your test suite *not* catch? (mutation testing; survivors = coverage blind spots) |
| `checks/fees.py` | Are fees two-sided, funding charged per bar, and slippage counted once per fill? |

**Who it is for.** Quant developers, prop-desk researchers, and anyone who has
ever shipped a strategy that looked great in a notebook and died in
production. If you are reviewing someone else's backtest — or your own — this
gives you a checklist, reproduction scripts, and before/after numbers instead
of opinions.

**What I deliver.** ① A ranked findings list plus a runnable reproduction
script for each problem. ② A minimal fix patch. ③ A before/after reconciliation
of the headline numbers (win rate, net PnL, multiple, MDD, t-stat).

**Three sample cases** (full write-ups in `cases/`):

1. **Look-ahead** — the exit scan ran on the entry bar, so every signal knew
   its outcome. Fixed: 91 trades / 90.1% / **+$214.37** → 26 trades / 65.4% /
   **-$0.12**; a tick-level re-run gives 27 trades / 66.7% / **+$0.37**. The
   leak was worth **≈ $214** of imaginary PnL — the whole profit.
2. **Withdrawal accounting** — the bust path dropped `wd_cum`, so any strategy
   with withdrawals was systematically understated. Fixed: same 2024–26 config
   **7.82x → 215.27x** (a ≈ 27x gap; withdrawal rules "double-keep-half" vs
   "double-keep-100" differ by ~27x).
3. **Drawdown metric** — the circuit-breaker reset the running peak, so the
   "reported MDD" was only the local drawdown. Investor-view raw drawdown
   **99.7%** vs reported **53.1%** — a **46 pp** gap. Conclusion: MDD must be
   written twice (breaker-local *and* raw).
   (*Bonus case 4:* 5-minute bar clustering inflated `n` ~11x and turned
   t = 15.60 into t = 1.75 after a 24h cooldown.)

**How to run.**

```bash
cd portfolio/backtest-audit-kit
python3 -m unittest discover tests      # stdlib only, no install
# or, if you have pytest:
python3 -m pytest tests/ -q
python3 examples/run_demo.py            # see all four checkers in action
```

**Honesty note.** The look-ahead checker is a heuristic linter, not a proof
engine: it flags the *shapes* that leak, and a stand-alone forward-simulation
pass is reported `MEDIUM` for human review rather than being declared safe.
Mutation testing reports blind spots; it never claims your strategy is
profitable. No checker here predicts returns.

---

## 中文

**是什么。** 一个纯 Python 标准库（3.9+）实现的回测审计工具包，四个互相独立
的检查器：

| 检查器 | 回答的问题 |
|---|---|
| `checks/lookahead.py` | 在 bar `i` 上的决策，是否读到了 `i+1...` 的数据？（基于 AST 的前视/未来函数检测） |
| `checks/invariants.py` | 账本是否满足会计不变量？（权益恒等式、`wd_cum` 结转、计数器单调、余额非负） |
| `checks/mutants.py` | 你的测试套件**抓不到**哪些 bug？（变异测试；存活的变异体 = 覆盖盲区） |
| `checks/fees.py` | 手续费是否双边计、资金费是否逐 bar 计、滑点是否每笔只算一次？ |

**给谁用。** 量化开发者、自营研究岗、以及任何"回测很美、实盘就死"过的
人。带看别人的回测（或自己的）时，它给你的是**问题清单 + 复现脚本 + 修复前后
的数字**，而不是一句"我觉得不太行"。

**交付物承诺。** ① 按严重度排序的问题清单，每个问题配一个可运行的复现脚本。
② 最小修复补丁。③ 修复前后的对账数字（胜率 / 净利 / 倍数 / 回撤 / t 值）。

**三个案例摘要**（完整写在 `cases/`）：

1. **前视 bug** —— 出场扫描写在开仓 bar 的循环内，每个信号都提前知道结果。
   修复后：91 笔 / 90.1% / **+$214.37** → 26 笔 / 65.4% / **-$0.12**；tick 级
   复跑得 27 笔 / 66.7% / **+$0.37**。这个泄漏值 **约 $214 的虚假收益**，
   即全部利润。
2. **提现会计 bug** —— 爆仓返程丢了 `wd_cum`，导致所有带提现的策略历史收益被
   系统性低估。修复后：同一配置 2024–26 **7.82x → 215.27x**（相差约 27 倍；
   提现规则"翻 2 留 1"与"翻 200 留 100"之间也差约 27 倍）。
3. **回撤口径 bug** —— 熔断触发时把 peak 重置为 cap，"报告 MDD"只是每段熔断
   后的局部回撤。投资者口径的原始回撤 **99.7%** vs 报告 **53.1%**，**差 46
   个百分点**。结论：MDD 必须双写（熔断口径 + 原始口径）。
   （**附赠案例 4**：一段暴跌连打十几根 5min bar 让样本量虚增约 11 倍，t 值从
   15.60 在 24h 冷却去重后掉到 1.75。）

**怎么跑。**

```bash
cd portfolio/backtest-audit-kit
python3 -m unittest discover tests      # 只用标准库，无需安装
# 若装了 pytest：
python3 -m pytest tests/ -q
python3 examples/run_demo.py            # 四个检查器全跑一遍
```

**诚实声明。** 前视检查器是启发式 linter，不是证明器：它抓的是会泄漏的**代码
形态**，独立的"向前模拟"循环会被标为 `MEDIUM` 交人工复核，而不是被判安全。
变异测试只报告覆盖盲区，从不声称你的策略赚钱。本工具包不预测任何收益。
