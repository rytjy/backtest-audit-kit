# backtest-audit-kit

**"I verify whether your strategy is real — or whether the backtest lied to you."**

A tiny, dependency-free toolkit that audits a backtest the way an accountant
audits a ledger and a QA engineer audits a test suite. It does not sell you
returns; it finds the four ways a backtest most often lies.

> **回测审计 / 策略代码复核服务** — 一页说明与联系方式 → **[PORTFOLIO.md](PORTFOLIO.md)**
> **Backtest audits · strategy-code review** — one-page overview → **[PORTFOLIO.md](PORTFOLIO.md)**

## 一条命令（3 分钟）

```bash
python3 -m auditkit.cli your.csv --trials 50     # 不用装，纯标准库
pip install -e . && auditkit your.csv            # 或者装上，用 auditkit 命令
```

给它一份交易/净值 CSV（`date` + `equity`，或 `date` + `pnl` / `return`），它只回三件事：

| 检查 | 问的问题 | 什么时候红 |
|---|---|---|
| look-ahead | 时间戳和成交价物理上可能吗 | 时间戳倒退、entry==exit 零持有、入场价落在该 bar 的 high/low 之外 = FAIL |
| multiple testing | 这个 Sharpe 能和「试了 N 次里最好的那次」分开吗 | 校正后 p ≥ 0.05 = FAIL（`--trials` 必须填你实际搜过的参数组数；在多个时间框架上各调过参数，再加 `--timeframes N`，N_eff = trials × timeframes；不填则标 UNVERIFIED，不冒充通过） |
| out-of-sample decay | 后半段还剩多少边 | 后半 SR ≤ 0 = FAIL，衰减 ≥ 50% = WARN |

多尺度搜索会单独标一行：同一策略在 5 个时间框架上各调 100 组 = **N_eff 500**，门槛按 500 算；若按 100 会判 PASS、按 500 判 FAIL，会额外出一条 WARN 说明膨胀。

退出码：`0` 全过 · `1` 有 FAIL · `2` 有缺输入判不了的项。加 `--ohlc bars.csv`（date, high, low）才能判价格级前视；`--json` 给机器读；`--split 0.6` 改样本内比例。

### One command (3 minutes)

`python3 -m auditkit.cli your.csv --trials 50` prints three verdicts — look-ahead,
multiple-testing (deflated Sharpe), out-of-sample decay — from a plain CSV
(`date` + `equity`, or `pnl` / `return`). Exit code 0 = pass, 1 = FAIL, 2 = needs input.
Without `--trials` the multiple-testing line says UNVERIFIED instead of inventing a pass.
Tuned the same grid on several time frames? Add `--timeframes N` — effective trials become
`trials × N`, and the tool prints the inflated N and, when it flips the verdict, a WARN line.
`--ohlc bars.csv` unlocks the price-level look-ahead check.

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
| `checks/bust_revival.py` | After a ruin check, does the account get reset to 1% and keep trading? (see `cases/case10_bust_revival.md`) |

**Who it is for.** Quant developers, prop-desk researchers, and anyone who has
ever shipped a strategy that looked great in a notebook and died in
production. If you are reviewing someone else's backtest — or your own — this
gives you a checklist, reproduction scripts, and before/after numbers instead
of opinions.

**What I deliver.** ① A ranked findings list plus a runnable reproduction
script for each problem. ② A minimal fix patch. ③ A before/after reconciliation
of the headline numbers (win rate, net PnL, multiple, MDD, t-stat).

**Three sample cases** — this page summarizes three of the thirteen write-ups in `cases/`:

New: [Case 13 — half the tickers, twice the PBO](audits/2026-11-06-case13-half-data-pbo.md). A retraction: I published PBO 73.33% against a README claim of 20%, but the run had loaded 63 of 75 tickers — the missing 12 shifted every cross-sectional rank. Full universe gives 46.67% / 26.67%, matching the maintainer. Same commit, same scripts; only the loaded count changed.

New: [Case 12 — the same 333 trades, three verdicts](audits/2026-11-04-case12-multiscale.md). One trade list, one data file; it passes `--trials 20 --timeframes 1` (p=0.024) and fails the same line with `--timeframes 5` (N_eff=100, p=0.12). The third block counts the search we actually ran, 576 configurations, and fails on a single time frame. Three outputs, one screen, nothing hidden.

1. **Look-ahead** — the exit scan ran on the entry bar, so every signal knew
   its outcome. Fixed: 91 trades / 90.1% / **+$214.37** → 26 trades / 65.4% /
   **-$0.12**; a tick-level re-run gives 27 trades / 66.7% / **+$0.37**. The
   leak was worth **≈ $214** of imaginary PnL — the whole profit.
2. **Withdrawal accounting** — the bust path dropped `wd_cum` (10 return
   sites). It only fires when a run busts: at lev 1.2 the published config never
   busts, so 7.82x → **7.82x**; at lev 5 it busts once and 0.00x → **5.97x**.
   The ~27x gap between 215.27x (no withdrawal) and 7.82x (double-keep-half) is
   **withdrawal policy, not the bug** — an earlier version of this page paired
   those two and mis-attributed it.
3. **Drawdown metric** — the circuit-breaker reset the running peak, so the
   "reported MDD" was only the local drawdown. Same run, same config:
   investor-view raw drawdown **98.7%** vs reported **53.1%** — a **45.6 pp**
   gap. Conclusion: MDD must be written twice (breaker-local *and* raw).
   (*Bonus case 4:* 5-minute bar clustering inflated `n` ~11x and turned
   t = 15.60 into t = 1.75 after a 24h cooldown.)

**Two public cases, both answered and followed by a change** — threads outside this repo; one-page PDF: [audits/2026-11-01-two-public-cases.pdf](audits/2026-11-01-two-public-cases.pdf).

| Thread | The number I questioned | What happened |
|---|---|---|
| [mr-scrooge-v6 #9](https://github.com/BrockStar3540/mr-scrooge-v6/issues/9) | -$1,308.74 over 1,041 trades (t ~ -3.0) | accepted; ratchet re-tightened, config bug fixed (B-142 to B-145) |
| [pineforge-engine #664](https://github.com/pineforge-4pass/pineforge-engine/issues/664) | 341 of 7,989 probes graded at a 100x wider PnL tolerance | accepted; regrade of all 7,989 due 2026-11-04 |

Full write-up: [audits/2026-11-01-two-public-cases.md](audits/2026-11-01-two-public-cases.md). Not paid work, and not a track record: 23 public threads opened, 7 answered (30%), 0 paid.

**What a deliverable looks like** - [audits/2026-11-01-sample-verification-report.pdf](audits/2026-11-01-sample-verification-report.pdf). One page, on a public live record recomputed from its own daily file: six numbers side by side, two convention gaps explained, one command to re-run. That result was *no error found* - which is also a result.

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
| `checks/bust_revival.py` | 爆仓检查之后，账户是否被重置成 1% 继续交易？（见 `cases/case10_bust_revival.md`） |

**给谁用。** 量化开发者、自营研究岗、以及任何"回测很美、实盘就死"过的
人。带看别人的回测（或自己的）时，它给你的是**问题清单 + 复现脚本 + 修复前后
的数字**，而不是一句"我觉得不太行"。

**交付物承诺。** ① 按严重度排序的问题清单，每个问题配一个可运行的复现脚本。
② 最小修复补丁。③ 修复前后的对账数字（胜率 / 净利 / 倍数 / 回撤 / t 值）。

**三个案例摘要**（本页只摘三份；`cases/` 里另有完整 13 份）：

新增：[案例 13 —— 半套票，双倍 PBO](audits/2026-11-06-case13-half-data-pbo.md)。一次**撤回**：我曾公布 PBO 73.33%（README 写 20%），但那次只加载了 75 只里的 63 只 —— 缺的 12 只改变了所有截面排名。满 75/75 复算是 46.67% / 26.67%，与维护者一致。同一 commit、同一脚本，只有加载数不同。

新增：[案例 12 —— 同一份 333 笔交易，三种判决](audits/2026-11-04-case12-multiscale.md)。一份交易表、一份数据：`--trials 20 --timeframes 1` 判 PASS（p=0.024），同一行加 `--timeframes 5` 判 FAIL（N_eff=100，p=0.12）；第三块按我们实际扫过的 576 组算，单时间框架就 FAIL。三段输出同页，不藏的。

1. **前视 bug** —— 出场扫描写在开仓 bar 的循环内，每个信号都提前知道结果。
   修复后：91 笔 / 90.1% / **+$214.37** → 26 笔 / 65.4% / **-$0.12**；tick 级
   复跑得 27 笔 / 66.7% / **+$0.37**。这个泄漏值 **约 $214 的虚假收益**，
   即全部利润。
2. **提现会计 bug** —— 爆仓返程丢了 `wd_cum`（引擎里有 10 处这样的 return）。
   它**只在爆仓时触发**：lev 1.2 的公开配置全程 0 爆仓 ⇒ **7.82x → 7.82x**，
   一分不变；lev 5 爆仓一次 ⇒ **0.00x → 5.97x**。215.27x 与 7.82x 之间那 27 倍
   是**提现规则本身的代价**（不提现 vs 翻 2 留 1），不是 bug —— 早先这一页把
   两个配置配成了一对，归因是错的，已改。
3. **回撤口径 bug** —— 熔断触发时把 peak 重置为 cap，"报告 MDD"只是每段熔断
   后的局部回撤。**同一次 run、同一配置**：投资者口径 **98.7%** vs 报告
   **53.1%**，**差 45.6 个百分点**。结论：MDD 必须双写（熔断口径 + 原始口径）。
   （**附赠案例 4**：一段暴跌连打十几根 5min bar 让样本量虚增约 11 倍，t 值从
   15.60 在 24h 冷却去重后掉到 1.75。）

**两个公开案例（都在本仓库之外）** —— 对方认账并改了代码；一页 PDF：[audits/2026-11-01-two-public-cases.pdf](audits/2026-11-01-two-public-cases.pdf)。

| 帖子 | 我质疑的数字 | 结果 |
|---|---|---|
| [mr-scrooge-v6 #9](https://github.com/BrockStar3540/mr-scrooge-v6/issues/9) | 1,041 笔合计 -$1,308.74（t ≈ -3.0） | 认账；收紧 ratchet，修掉配置加载 bug（B-142 至 B-145） |
| [pineforge-engine #664](https://github.com/pineforge-4pass/pineforge-engine/issues/664) | 7,989 个 probe 里 341 个按宽 100 倍的 PnL 容差评分 | 认账；承诺 2026-11-04 前重跑全部 7,989 |

完整文字：[audits/2026-11-01-two-public-cases.md](audits/2026-11-01-two-public-cases.md)。不是付费工作，也不是战绩：公开 23 条，7 条有回复（30%），付费 0。

**第三份，性质不同：读源码。** [APEX V2 [JOAT]](https://www.tradingview.com/script/b4EWZCPJ-APEX-V2-JOAT/)（开源 Pine，作者 JOAT）——不跑、不看净值，只把描述里的每个数字对回代码，查出六处对不上：面板上的 `8.0σ` 其实是 12 个标准差（分母带 `* 1.5`）；confluence 分母 9 但输入上限 7；九个票里有俩测的是同一个 VWAP 偏离；`Enable Trailing Stop` 默认开着却永远触发不了（`limit` 和 `trail_price` 同价）；`Risk Per Trade %` 算完没用（仓位走 `default_qty_value=100`）；`strategy()` 无手续费无滑点。每条都带行号，附 `sed` 复现命令：[`audits/2026-11-01-apex-v2-code-audit.md`](audits/2026-11-01-apex-v2-code-audit.md)。**没有对方回复** —— TradingView 脚本页没有评论区（页面 706KB 里 `comment` 只出现两次，全是数据字段；相关 API 全 404），所以这份是"结论"而不是"回合"。

**交付物长什么样** —— [audits/2026-11-01-sample-verification-report.pdf](audits/2026-11-01-sample-verification-report.pdf)。一页纸，靶子是一份公开的实盘记录，用他本人发布的逐日文件复算：六个数字逐行对照，两处口径差异讲清楚，附一条可重跑的命令。那次结论是「未发现错误」——这也是结果。

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
