# Task 04 — Asymptotic Parallel Efficiency

## Gustafson efficiency

Scaled speedup and efficiency are

\[
S(P) = P - \alpha(P-1), \qquad E(P) = \frac{S(P)}{P},
\]

with serial time-fraction \(\alpha\) held constant in \([0,1]\) and processor count \(P \ge 1\).

Expand the efficiency:

\begin{align*}
E(P)
&= \frac{P - \alpha(P-1)}{P} \\
&= 1 - \alpha \cdot \frac{P-1}{P} \\
&= 1 - \alpha\left(1 - \frac{1}{P}\right) \\
&= 1 - \alpha + \frac{\alpha}{P}.
\end{align*}

## Limit under Gustafson’s law

**Claim.** \(\displaystyle\lim_{P \to \infty} E(P) = 1 - \alpha\).

**Proof.** For every finite \(P \ge 1\),

\[
\bigl|E(P) - (1-\alpha)\bigr| = \left|\frac{\alpha}{P}\right| = \frac{\alpha}{P},
\]

where the last step uses \(\alpha \ge 0\). Let \(\varepsilon > 0\).

- If \(\alpha = 0\), then \(E(P) = 1\) for every \(P\), so the difference is \(0 < \varepsilon\) immediately and the limit is \(1 = 1-\alpha\).
- If \(\alpha > 0\), choose an integer \(P_0 > \alpha/\varepsilon\). For every \(P \ge P_0\),

\[
\frac{\alpha}{P} \le \frac{\alpha}{P_0} < \varepsilon.
\]

Thus \(E(P)\) approaches \(1-\alpha\). \(\square\)

The approach is from above: \(\alpha/P > 0\) for finite \(P\), so \(E(P) > 1-\alpha\), and \(E\) is strictly decreasing in \(P\) whenever \(\alpha > 0\). Efficiency therefore degrades, but the degradation is bounded. A machine with a 4% serial time-fraction keeps at least 96% efficiency at every scale, and it gets arbitrarily close to 96% rather than falling toward zero.

## Limit under Amdahl’s law

Amdahl speedup at the same numerical value \(s = \alpha\), now interpreted as the serial fraction of a *fixed* workload, is

\[
S_{\text{Amdahl}}(P) = \frac{1}{s + (1-s)/P}.
\]

Efficiency on \(P\) processors is speedup per processor:

\begin{align*}
E_{\text{Amdahl}}(P)
&= \frac{S_{\text{Amdahl}}(P)}{P} \\
&= \frac{1}{P\left(s + (1-s)/P\right)} \\
&= \frac{1}{sP + (1-s)}.
\end{align*}

**Claim.** If \(s > 0\), then \(\displaystyle\lim_{P \to \infty} E_{\text{Amdahl}}(P) = 0\). If \(s = 0\), the limit is \(1\).

**Proof.** The \(s = 0\) case is \(E_{\text{Amdahl}}(P) = 1\). For \(s > 0\) and \(P \ge 1\),

\[
0 < E_{\text{Amdahl}}(P) = \frac{1}{sP + (1-s)} < \frac{1}{sP},
\]

because \(1-s \ge 0\). Let \(\varepsilon > 0\) and choose an integer \(P_0 > 1/(s\varepsilon)\). For every \(P \ge P_0\),

\[
E_{\text{Amdahl}}(P) < \frac{1}{sP} \le \frac{1}{sP_0} < \varepsilon.
\]

The squeeze \(0 < E_{\text{Amdahl}}(P) < \varepsilon\) gives the limit \(0\). \(\square\)

## What the two limits say operationally

| Model | \(E(P)\) | \(\lim_{P\to\infty} E(P)\) | Regime |
|---|---|---|---|
| Gustafson | \(1 - \alpha + \alpha/P\) | \(1-\alpha\) | Fixed time, work grows with \(P\) |
| Amdahl | \(1/(sP + 1 - s)\) | \(0\) when \(s>0\) | Fixed work, \(P\) grows |

Under Gustafson, each added processor is given new parallel work, so the fraction of the machine that stays busy tends to the parallel time-fraction \(1-\alpha\). The idle fraction tends to \(\alpha\), the portion of the time window spent waiting on the serial section, and it does not grow with \(P\).

Under Amdahl, added processors receive a thinning slice of a frozen parallel region and then wait on a serial section that does not thin out. Busy time per processor vanishes like \(1/(sP)\).

Setting the symbols \(\alpha\) and \(s\) equal numerically does not make the limits comparable as predictions for one experiment. They are comparable only after Task 03’s frame is fixed: \(\alpha\) is a time split on the scaled run, while \(s\) is a work split on the original run. Inside each model, taken on its own terms, Gustafson efficiency has a positive floor and Amdahl efficiency has a zero floor.
