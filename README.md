# backtest-audit-kit

**"I verify whether your strategy is real — or whether the backtest lied to you."**

A tiny, dependency-free toolkit that audits a backtest the way an accountant
audits a ledger and a QA engineer audits a test suite. It does not sell you
returns; it finds the four ways a backtest most often lies.

> **回测审计 / 策略代码复核服务** — 一页说明与联系方式 → **[PORTFOLIO.md](PORTFOLIO.md)**
> **Backtest audits · strategy-code review** — one-page overview → **[PORTFOLIO.md](PORTFOLIO.md)**
> **Price and scope** → **[SERVICE.md](SERVICE.md)**  ·  **价格与范围** → **[SERVICE.md](SERVICE.md)**
>
> **Need a second pair of eyes on one number?** Send the trade-by-trade rows and your
> cost assumptions. In 48 hours you get a one-page finding, a repro script that prints
> the same number, and a minimal patch where the fix is local. **¥199 / $29 per issue**;
> if nothing reproducible turns up, you pay nothing.
>
> **Start here** → [open an issue](https://github.com/rytjy/backtest-audit-kit/issues/new) with the repo link or the core file; one concrete, reproducible finding comes back first.
>
> **想让人替你核一个数？** 把逐笔成交和你的成本假设发来，48 小时给你一页结论、一个能跑出同样数字的脚本、一处最小补丁。**¥199 / $29 一个问题**；查不出可复现的问题，不收钱。
>
> **从这里开始** → [开一个 issue](https://github.com/rytjy/backtest-audit-kit/issues/new)：贴仓库链接或核心文件，先给你一条具体的、可复现的问题。

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

**Sample cases** (full write-ups in `cases/`):

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
4. **Cost omission** (`cases/case5_cost_omission.md`) — a high-turnover 50x
   book charged **no** fee, funding or slippage; its take-profit needed only a
   **+0.08%** move while one round trip costs **0.09%** (the venue's real 4.5 bps
   taker), so the target sat below the toll and every win is a net loss. At the
   venue rate the omitted cost ran **~5.4x the starting capital** and **~17.8x the
   reported profit**.

5. **Numeric cancellation** (`cases/case6_numeric_cancellation.md`) — an
   expanding R² on a perfectly linear series returned **0.14–0.69** instead of
   **1.0**: raw `E[y²] − E[y]²` loses the variance to cancellation at large
   offsets (24.7% variance error on a `100 + 1e-6*i` prefix; total collapse at
   `1e10 + i`). Masking absolute `std ≈ 0` is not the fix — it also rejects
   valid small-variance windows.

6. **On-chain yield** (`cases/case7_onchain_yield.md`) — two public ERC4626
   vaults, same measurement. sUSDS: headline 3.80% vs realized 3.69% / 3.59%
   (30 / 90 days). Yearn OG USDC: headline **8.44%** vs realized **6.52%** /
   **6.04%**; 0.52 pp of the headline was token rewards that never entered the
   share price. The gap has three measurable sources: point-in-time vs period,
   rewards vs share price, gross vs net of fees.

**Install.**

```bash
pip install backtest-audit-kit
```

**Use it in code** (four checkers, pure standard library):

```python
from auditkit.checks import lookahead
findings = lookahead.detect_file("strategy.py")   # future-data lint
print(lookahead.format_findings(findings))
```

**Public reception.** Accepted into
[awesome-quant](https://github.com/wilsonfreitas/awesome-quant) (Trading &
Backtesting) via PR #824, merged 2026-10-19.

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

**案例摘要**（完整写在 `cases/`）：

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
4. **成本漏算**（`cases/case5_cost_omission.md`）—— 一个高换手 50x 账本**完全没算**手续费/资金费/滑点；止盈只需价格动 **+0.08%**，而一趟往返 **0.09%**（场馆真实 4.5bps taker）⇒ 目标在成本之下，每笔赢单净亏。按场馆真实费率，漏掉的成本约 **5.4× 本金**、**17.8× 账面收益**。

5. **数值抵消**（`cases/case6_numeric_cancellation.md`）—— 完全线性的序列上，expanding R² 返回 **0.14–0.69** 而不是 **1.0**：原始 `E[y²] − E[y]²` 在大偏移下把方差抵消掉了（`100 + 1e-6*i` 前缀方差相对误差 **24.7%**；`1e10 + i` 直接塌掉）。加绝对 `std ≈ 0` 掩码不是修法——它会把有效的小方差窗口一起误杀。

6. **链上收益**（`cases/case7_onchain_yield.md`）—— 两个公开 ERC4626 金库，同一套测法。sUSDS：头条 3.80% vs 实现 3.69% / 3.59%（30 / 90 天）。Yearn OG USDC：头条 **8.44%** vs 实现 **6.52%** / **6.04%**；其中 0.52pp 是代币奖励，从不进份额价格。差距有三个可测来源：时点 vs 期间、奖励 vs 份额价格、毛 vs 净（费用）。

**公开收录。** 本仓库已进入 [awesome-quant](https://github.com/wilsonfreitas/awesome-quant)
的 Trading & Backtesting 段（PR #824，2026-10-19 合并）。

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

---

## Also in this account · 另见

- [`outpost/`](./outpost/) — 一个"只放能跑、能查、能被否证的东西"的据点：
  单文件表格整理工具（零依赖、离线自检 14 项）+ 一份**被自己推翻**的回测（做空山寨无 edge）
  + 一次"两条腿都断了"的数据源修复。不写客户名、不写"我能做什么"。

- [audits/2026-10-28-collective2-calmar.md](./audits/2026-10-28-collective2-calmar.md) - 公开审计 · public audit:
  四个 Collective2 策略页的 Calmar 一个都复算不出来（倍数 1.21-1.53x，不是固定口径差），利润因子 3/4 对得上、1 个差 14.8%。
  附可复跑脚本 c2_page_check.py；不点任何卖家名、不声称对方造假。
