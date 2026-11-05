# Task 06 — Scaled Speedup at \(\alpha = 0.04\)

The serial time-fraction on the parallel machine is \(\alpha = 0.04\). Scaled speedup and efficiency are the closed forms from Task 02 and Task 04:

\[
S(P) = P - \alpha(P-1) = 0.04 + 0.96\,P,
\]

\[
E(P) = 1 - \alpha\frac{P-1}{P} = 0.96 + \frac{0.04}{P}.
\]

Both expressions are exact for every \(P\) in the table (each \(P\) is a power of two, so \((P-1)/P\) is a finite binary fraction and the decimals below terminate).

| \(P\) | \(\alpha(P-1)\) | \(S(P)\) | \(E(P)\) | \(E(P)\) in percent |
|---|---|---|---|---|
| 16 | 0.60 | 15.40 | 0.962500000000 | 96.2500000000% |
| 64 | 2.52 | 61.48 | 0.960625000000 | 96.0625000000% |
| 256 | 10.20 | 245.80 | 0.960156250000 | 96.0156250000% |
| 1024 | 40.92 | 983.08 | 0.960039062500 | 96.0039062500% |
| 4096 | 163.80 | 3932.20 | 0.960009765625 | 96.0009765625% |
| 16384 | 655.32 | 15728.68 | 0.960002441406 | 96.0002441406% |

## How efficiency degrades

\(E(P)\) is strictly decreasing and bounded below by \(1-\alpha = 0.96\). Across a thousand-fold growth in processor count, from 16 cores to 16,384 cores, efficiency falls from \(0.9625\) to \(0.960002441406\). The absolute drop is \(0.002497558594\), about a quarter of one percentage point.

Almost all of the loss from the ideal value \(E(1) = 1\) has already happened by the time the machine reaches a few tens of processors: \(E(16)\) is \(0.0025\) above the floor, and \(E(16384)\) is only \(0.00000244\) above it. Further growth in \(P\) does not open a new efficiency problem. It repeats the same \(4\%\) idle-time fraction on a larger machine. Speedup keeps a constant \(96\%\) of linearity: \(S(P)/P \to 0.96\), and \(S(16384) = 15728.68\) against an ideal \(16384\).

The practical reading of the table is that a \(4\%\) serial time-fraction is a small, stable tax under weak scaling. It is not an accumulating penalty. The tax would look entirely different under a fixed-size model with the same numerical fraction: Amdahl efficiency \(1/(0.04P + 0.96)\) at \(P = 16384\) is \(1/656.32 \approx 0.00152\), three orders of magnitude below the Gustafson column. That comparison uses Task 03’s warning: the two formulas may share the symbol \(0.04\) only after the experiment decides whether \(0.04\) is a fraction of a frozen workload or a fraction of a fixed time window. This table is the second of those experiments.
