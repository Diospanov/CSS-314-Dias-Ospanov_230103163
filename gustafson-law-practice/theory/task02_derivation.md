# Task 02 — Derivation of Scaled Speedup

## Setup and notation

Run the scaled problem on \(P\) processors and divide its wall-clock time into two measured pieces:

- \(s\): time spent in work that is not sped up by the extra processors (startup, a serial kernel, a single-threaded reduction that has already been timed as serial).
- \(p\): time spent in the parallel region, as observed on the \(P\)-processor run. During this interval all \(P\) processors are doing useful parallel work.

Normalize the parallel run so that its compute time is one time unit:

\[
s + p = 1, \qquad s \ge 0,\quad p \ge 0.
\]

\(s\) and \(p\) are therefore time fractions on the parallel machine. Write \(\alpha\) for the serial fraction in that same frame:

\[
\alpha = \frac{s}{s+p} = s, \qquad 1-\alpha = p.
\]

The normalization \(s+p=1\) is a choice of time unit. It does not assume the serial and parallel *work* are equal.

## Step 1 — One processor’s time on the parallel region

During the parallel interval of length \(p\), each of the \(P\) processors performs useful work. On one processor that same work is done sequentially, so it occupies

\[
T_{\text{parallel work on 1 processor}} = p \cdot P.
\]

Justification: the \(P\) processors together contribute \(p \cdot P\) processor-seconds, and a single processor can supply only one processor-second per second of wall time. This step assumes the parallel region has perfect speedup on its own work: no extra communication, no duplicate computation, and a balanced split. Those effects, if present, belong in an extended model (Task 12), not in the base identity.

## Step 2 — Equivalent serial time of the scaled workload

The serial section does not multiply by \(P\). One processor spends time \(s\) on it, the same amount the parallel run spent. Adding the two contributions gives the time one processor would need to execute the *entire scaled* workload:

\[
T_1 = s + p \cdot P.
\]

Justification: the scaled workload is exactly the serial work plus the parallel work that the \(P\) processors just finished. No other work is introduced by moving to one processor under the assumptions of Step 1.

## Step 3 — Scaled speedup is the ratio of those times

Scaled speedup is how much longer the scaled workload takes on one processor than on \(P\) processors. The parallel wall time is \(s+p=1\), so

\[
S(P) = \frac{T_1}{T_P} = \frac{s + p \cdot P}{s + p} = s + p \cdot P.
\]

Justification: dividing by \(s+p\) is dividing by 1. This is the first form required by the task,

\[
S(P) = s + p \cdot P.
\]

## Step 4 — Substitute the serial fraction \(\alpha\)

Because the run is normalized, \(s=\alpha\) and \(p=1-\alpha\). Substitute:

\begin{align*}
S(P)
&= \alpha + (1-\alpha)\,P \\
&= \alpha + P - \alpha P \\
&= P + \alpha(1-P) \\
&= P - \alpha(P-1).
\end{align*}

Line by line:

1. Replace \(s\) and \(p\) using \(\alpha=s\) and \(1-\alpha=p\).
2. Distribute \((1-\alpha)P\).
3. Group the terms that contain \(\alpha\): \(\alpha - \alpha P = \alpha(1-P)\).
4. Use \(1-P = -(P-1)\) to reach \(P - \alpha(P-1)\).

## Step 5 — The two forms are identical

The algebraic identity just shown is

\[
s + p\cdot P = P - \alpha(P-1)
\]

whenever \(\alpha=s\), \(p=1-\alpha\), and \(s+p=1\). Either form may be used for later tasks. The factored form makes the efficiency limit in Task 04 immediate:

\[
E(P) = \frac{S(P)}{P} = 1 - \alpha\frac{P-1}{P}.
\]

## What the derivation does not claim

\(T_1 = s + pP\) is the serial time of the *scaled* problem, the problem that was large enough to fill \(P\) processors. It is not the serial time of the smaller problem that originally fit on one processor. That distinction is the whole of Task 03. The derivation also treats \(s\) as independent of \(P\). When communication grows with \(P\), the denominator is no longer 1 and Step 3 gains the term derived in Task 12.
