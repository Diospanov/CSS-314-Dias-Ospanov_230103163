# Task 09 — Three-Phase Simulation

## Time breakdown on the parallel run

The three phases are given as shares of the parallel execution time, and the shares sum to 1:

| Phase | Role | Share of \(T_P\) | Scales with \(P\)? |
|---|---|---|---|
| A | Disk I/O and parameter broadcast | \(0.02\) | No. One reader, then a start-up broadcast. |
| B | Boundary synchronization | \(0.06\) | No, inside this model. It is time spent coupling ranks rather than advancing the flux. |
| C | Domain flux computation | \(0.92\) | Yes. This is the parallel region. |

Phases A and B are both parts of the wall time that the flux workers cannot remove by adding processors. Their sum is the serial time-fraction Gustafson’s formula takes as input:

\[
\alpha = 0.02 + 0.06 = 0.08, \qquad p = 1-\alpha = 0.92.
\]

(The \(6\%\) synchronization is real communication. Task 12 would let that term grow with \(P\). Here it is given as an observed share at the processor count under discussion, so it is folded into a constant \(\alpha\) for that observation.)

## Scaled speedup

\[
S(P) = P - 0.08(P-1) = 0.08 + 0.92\,P.
\]

**At \(P = 512\):**

\[
S(512) = 512 - 0.08 \cdot 511 = 512 - 40.88 = 471.12,
\]

\[
E(512) = \frac{471.12}{512} = 0.92015625.
\]

**At \(P = 2048\):**

\[
S(2048) = 2048 - 0.08 \cdot 2047 = 2048 - 163.76 = 1884.24,
\]

\[
E(2048) = \frac{1884.24}{2048} = 0.9200390625.
\]

## What each phase contributes

The parallel phase alone would allow \(S = 0 + 1 \cdot P = P\). Charging the observed overhead changes the slope from 1 to 0.92 and adds a \(0.08\) intercept. Splitting the overhead back into its sources:

\[
S(P) = \underbrace{0.02}_{\text{I/O, broadcast}} + \underbrace{0.06}_{\text{boundary sync}} + \underbrace{0.92\,P}_{\text{flux}}.
\]

At 512 processors the flux term is \(471.04\) and the two overheads contribute \(0.08\) of scaled speedup between them. At 2,048 processors the flux term is \(1884.16\). The overheads dominate the *loss relative to linear speedup* — \(40.88\) points at \(P = 512\), \(163.76\) points at \(P = 2048\) — while remaining \(8\%\) of the wall time. Efficiency moves from \(0.92015625\) to \(0.9200390625\), toward the floor \(0.92 = 1-\alpha\).

Of the \(8\%\) tax, boundary synchronization is three quarters (\(6/8\)) and I/O plus broadcast is one quarter (\(2/8\)). A redesign that overlapped the boundary exchange with the flux would be attacking the larger piece of \(\alpha\). A redesign that only cut the disk stage would be attacking a serial share of \(0.02\), which at these processor counts changes \(S\) by \(0.02(P-1)\): about \(10.2\) speedup points at \(P = 512\) and about \(40.9\) points at \(P = 2048\).
