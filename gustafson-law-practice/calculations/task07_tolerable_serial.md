# Task 07 — Maximum Serial Fraction on 8,192 Cores

## Requirement

The machine has \(P = 8192\) cores. The scaled speedup must satisfy

\[
S(P) \ge 7500.
\]

Find the largest serial time-fraction \(\alpha\) that still meets the requirement.

## Algebra

Start from \(S(P) = P - \alpha(P-1)\) and impose the floor:

\begin{align*}
8192 - \alpha(8192 - 1) &\ge 7500 \\
8192 - \alpha \cdot 8191 &\ge 7500 \\
-\alpha \cdot 8191 &\ge 7500 - 8192 \\
-\alpha \cdot 8191 &\ge -692.
\end{align*}

Dividing by \(-8191\) reverses the inequality:

\[
\alpha \le \frac{692}{8191}.
\]

So the maximum tolerable serial fraction is exactly

\[
\alpha_{\max} = \frac{692}{8191}.
\]

The fraction is in lowest terms: \(692 = 2^2 \cdot 173\) and \(8191 = 2^{13}-1\) is prime, so \(8191\) shares no factor with \(692\).

## Decimal value and the equality check

\[
\alpha_{\max} = \frac{692}{8191} = 0.08448296911244\ldots
\]

At this value the speedup lands on the requirement with no slack:

\[
S(8192) = 8192 - \frac{692}{8191}\cdot 8191 = 8192 - 692 = 7500.
\]

Any larger \(\alpha\) misses the floor. In percentages, the parallel run may spend at most \(8.4483\%\) of its wall time in the serial section. The matching parallel time-fraction is

\[
1 - \alpha_{\max} = \frac{8191 - 692}{8191} = \frac{7499}{8191} \approx 0.915517030888.
\]

Efficiency at the boundary is \(E = 7500/8192 \approx 0.915527\). The slight difference between \(1-\alpha_{\max}\) and \(E\) is the \(\alpha/P\) term from Task 04: efficiency sits a little above the floor \(1-\alpha\).

## Reading the tolerance

An 8,192-core machine aimed at a scaled speedup of 7,500 can afford a serial section about twice as long, as a fraction of time, as the \(4\%\) example of Task 06. It cannot afford a serial section of \(10\%\): that would give

\[
S = 8192 - 0.10 \cdot 8191 = 8192 - 819.1 = 7372.9 < 7500.
\]

The entire budget from a perfectly parallel machine down to the requirement is \(8192 - 7500 = 692\) speedup points, and those 692 points are exactly \(\alpha \cdot 8191\).
