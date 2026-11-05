# Task 19 — Serial Fraction of a Large Monte Carlo Engine

## Why the workload is the model weak-scaling case

A Monte Carlo estimate of an integral or an expected value is a mean of \(M\) independent samples. Sample \(i\) depends on a random number stream and on read-only parameters. It does not depend on sample \(j\). Splitting \(M = P \cdot k\) samples across \(P\) workers, with \(k\) fixed, gives each worker the same arithmetic it had at \(P = 1\). There is no halo, no ordering between samples, and no growth of an iteration count. Parallel time per batch stays constant while the ensemble grows linearly with \(P\). Among the workloads in this sheet, this is the one Gustafson’s hypotheses were written for.

The scaled speedup would be \(S(P) = P\) if nothing surrounded the sampling loop. Production engines miss that ideal by a thin set of operations that are easy to underestimate because each of them is negligible on a workstation and visible on a full machine. Those operations are the serial fraction.

## Where a nonzero \(\alpha\) actually comes from

**Parameter setup and broadcast.** The cross section, the geometry, or the payoff parameters are read on one rank and sent to the others. The read is independent of \(M\). The broadcast is a collective of modest payload, \(\Theta(\log P)\) in latency plus the message size. Both sit outside the sample loop.

**Random-stream initialization.** Independent samples are only independent if the workers’ streams do not overlap. A library that takes one seed and then spawns \(P\) substreams by a jump-ahead of length \(k\) has to compute \(P\) jumps. Done on one rank, that is \(\Theta(P)\) setup work and it destroys constant time as soon as \(P\) is large. Done by each worker from its rank id, with a counter-based generator (a bijection from an integer counter to a uniform, as in Philox or Random123) or with a jump the worker computes locally, the cost is \(\Theta(1)\) per worker and folds into the parallel time. The serial fraction contributed by the generator is an initialization choice, not a property of Monte Carlo. A single global seed advanced by one rank and handed out through a serial loop is an avoidable \(\alpha\).

**The reduction.** Each worker holds a partial sum, a partial sum of squares, or a histogram. The estimate is the sum of those partials. A binary tree (or the equivalent all-reduce) has \(\lceil \log_2 P \rceil\) stages. If one stage costs \(\beta\) time units in the same normalization as the sample kernel, the reduction contributes

\[
C_{\text{red}}(P) = \beta \lceil \log_2 P \rceil
\]

to the wall time. This term is not a fixed \(\alpha\). It is the logarithmic communication penalty of Task 12, and it is the term that sets how far a real Monte Carlo engine drifts from \(S(P) = s + pP\).

**Output serialization.** Writing one file from every rank contends on the filesystem. The pattern that keeps \(\alpha\) small is: each rank writes a private partial, or a single rank writes a compact reduced record. The pattern that inflates \(\alpha\) is a serial gather of every sample path back to rank 0 when the only required result was the mean. Checkpointing full trajectories is \(\Theta(M) = \Theta(P)\) data; if it passes through one writer it is \(\Theta(P)\) time and constant-time weak scaling ends there.

## A model that isolates the reduction

Normalize the per-worker sample time to a constant \(\tau\) (this is \(k\) paths) and let \(\sigma\) be the fixed setup and final serial I/O, with no \(\Theta(P)\) term left in \(\sigma\). Wall time and one-processor time of the scaled ensemble are

\[
T_P = \sigma + \beta \log_2 P + \tau, \qquad T_1 = \sigma + P\tau.
\]

The one-processor timing does not include the parallel reduction; one processor simply accumulates into a register as it samples. Scaled speedup is

\[
S(P) = \frac{\sigma + P\tau}{\sigma + \beta\log_2 P + \tau}.
\]

The classical Gustafson number with the same compute split, pretending the reduction is free, is \(S_{\text{ideal}}(P) = \sigma/(\sigma+\tau) + \tau P/(\sigma+\tau)\) only after renormalizing — easier to compare the un-normalized forms

\[
S_{\text{no reduction}}(P) = \frac{\sigma + P\tau}{\sigma + \tau}, \qquad S(P) = \frac{\sigma + P\tau}{\sigma + \tau + \beta\log_2 P}.
\]

Their ratio is the penalty of the tree:

\[
\frac{S(P)}{S_{\text{no reduction}}(P)} = \frac{\sigma+\tau}{\sigma+\tau+\beta\log_2 P}.
\]

## Numerical size of the tree

Take \(\tau = 0.95\), \(\sigma = 0.05\), so a reduction-free run has \(\alpha = 0.05/1.00 = 0.05\) and \(S_{\text{no reduction}} = 0.05 + 0.95P\). Two reduction costs: a cheap scalar reduction \(\beta = 0.001\), and a heavy histogram reduction \(\beta = 0.01\), in the same time unit.

| \(P\) | \(\log_2 P\) | \(S\) at \(\beta = 0.001\) | \(S\) at \(\beta = 0.01\) | \(S\) with \(\beta = 0\) |
|---|---|---|---|---|
| 16 | 4 | \((0.05+15.2)/(1.004) = 15.189\) | \((15.25)/1.04 = 14.663\) | 15.25 |
| 256 | 8 | \((0.05+243.2)/1.008 = 241.319\) | \(243.25/1.08 = 225.231\) | 243.25 |
| 1024 | 10 | \(972.85/1.010 = 963.218\) | \(972.85/1.10 = 884.409\) | 972.85 |
| 65536 | 16 | \(62259.25/1.016 = 61278.79\) | \(62259.25/1.16 = 53671.77\) | 62259.25 |

A scalar reduction at \(\beta = 0.001\) removes about one percent of the scaled speedup at 1,024 workers (\(963\) against \(973\)) and about \(1.6\%\) at 65,536 workers. The same engine reducing a large histogram, \(\beta = 0.01\), is already \(9\%\) below the classical curve at 1,024 workers (\(884\) against \(973\)) and \(14\%\) below it at 65,536. The sample loop did not get worse. The tree got taller, and a fatter message made each rung expensive.

The observed serial fraction, if someone insists on quoting a single \(\alpha(P)\) for the run, is

\[
\alpha(P) = \frac{\sigma + \beta\log_2 P}{\sigma + \beta\log_2 P + \tau},
\]

which rises from \(0.053\) at \(P = 16\) to \(0.065\) at \(P = 65536\) when \(\beta = 0.001\), and from \(0.086\) to \(0.181\) over the same range when \(\beta = 0.01\). Substituting that moving \(\alpha(P)\) back into \(P - \alpha(P-1)\) is the inconsistency flagged in Task 12; the ratio \(T_1/T_P\) above is the speedup to report.

## What to do with the three sources

Keep stream setup on the worker and prefer a counter-based generator so seed management is \(\Theta(1)\) local work. Keep the reduction, accept \(\beta\log_2 P\), and shrink \(\beta\) by reducing a handful of accumulators rather than a full path. Keep output on the reduced record. Do those three and the engine’s scaled speedup stays within a logarithmic factor of \(0.05 + 0.95P\). Leave any one of them as a serial function of \(P\) or of \(M\) and the constant-time premise fails in the way Task 13 describes, even though the samples themselves were embarrassingly parallel.
