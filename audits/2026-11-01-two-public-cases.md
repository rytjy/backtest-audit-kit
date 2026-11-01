# Two cases where the finding was accepted and the code changed

Independent public reviews of published backtest numbers. No engagement, no fee, no account access:
every claim was made against artifacts the target had already published, and every reply is in the thread.

## Case 1 - pineforge-engine #664

- **Opened:** 2026-10-31 03:57Z. **First reply:** 2026-10-31 12:32Z (8h35m).
- **Claim:** the parity scoreboard reports 7,989 graded probes under one headline, but
  trailing-stop strategies are graded on a looser profile - exit within 0.05% and P&L within 100% -
  against 0.01% and 1% for everything else. Their README documents the looser profile; the
  denominator does not separate it out.
- **Reply (luisleo526):** accepted, with the split. 341 of the 7,989 probes use trail_* parameters
  (58 distinct strategies); the other 7,648 were already graded strict.
  At exit 0.02% / P&L 1%: 0 of 341 fail under their own 90th-percentile rule, 8 of 341 by
  worst single trade.
- **Change committed in the thread:** drop the looser profile, list the trailing-stop bucket
  separately with the grading rule printed beside it, re-run all 7,989 and publish which change
  grade - by 2026-11-04.
- **Status:** commitment, not yet verified.

## Case 2 - mr-scrooge-v6 #9

- **Opened:** 2026-10-08 13:01Z. **First reply:** 2026-10-21 20:22Z. **Closed out:** 2026-10-28 14:48Z.
- **Claim:** the promote/demote evidence bar does not scale with the number of candidates tried
  (~1,000 setups on trial), so clearing it partly measures the search rather than the edge.
- **Their process:** they pre-registered a prediction, then ran it.
- **Independent re-runs:** 1,041 trades from their published trades.csv - sum -$1,308.74,
  mean -$1.257, t ~ -3.0; 18 fixed stop/target combinations on real M1 data - all negative;
  sizing decomposition by seat (parent 633 / popper 409).
- **Reply (BrockStar3540):** accepted. The -$131.44 gap was overnight financing; OANDA half-spread
  summed to $979.82, about three quarters of the realized loss; the payoff grid matched their own
  replay.
- **Changed the same night (2026-10-28 07:06Z):** ratchet re-tightened; a config-loader bug that
  dropped early-lock settings on every popper found and fixed (Book of Bugs B-142 to B-145,
  CHANGELOG 6.31.0); reaper window 24h to 4h.
- **Also granted in writing:** permission to cite the exchange.

## What this is, and what it is not

- **Is:** two public threads where one specific number was challenged, answered, and followed by a
  code change in the target's own repository.
- **Is not:** paid work. Neither case was billed. One party states it does not buy audits; the other
  has not been asked.
- **Is not a base rate:** 23 public threads opened, 7 answered (30%), 0 paid.

## Reproduce

- Case 1: https://github.com/pineforge-4pass/pineforge-engine/issues/664
- Case 2: https://github.com/BrockStar3540/mr-scrooge-v6/issues/9
- Audit scripts and outputs for case 2: https://github.com/rytjy/backtest-audit-kit/tree/main/audits
