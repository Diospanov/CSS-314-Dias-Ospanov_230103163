# Task 11 — Gustafson and Sun–Ni Memory-Bounded Speedup

## The quantity Sun and Ni allowed to vary

Xian-He Sun and Lionel M. Ni generalized the two classical limits by letting the workload grow by a factor \(g(P)\) set by available memory, rather than by the two-point choice “do not grow” or “grow exactly with \(P\)”.

Let a one-processor problem have serial work fraction \(s\) and parallel work fraction \(1-s\). Give the machine \(P\) processors and enough extra memory that the parallel work may be multiplied by \(g(P)\), where \(g\) is determined by the application and by the memory system:

\[
S_{\text{SN}}(P) = \frac{s + (1-s)\,g(P)}{s + (1-s)\,g(P)/P}.
\]

The numerator is the one-processor time of the enlarged problem. The denominator is the \(P\)-processor time, assuming the enlarged parallel work speeds up by \(P\) and the serial work does not. This is the memory-bounded speedup model (Sun and Ni, early 1990s; the technical argument was in circulation from about 1990 and published in the *Journal of Parallel and Distributed Computing* in 1993).

Two substitutions recover the earlier laws exactly.

- Fixed size, no extra memory used to enlarge the problem: \(g(P) = 1\). Then \(S_{\text{SN}} = 1 / (s + (1-s)/P)\), which is Amdahl.
- Fixed time, parallel work enlarged in proportion to the processor count: \(g(P) = P\). Then the denominator is \(s + (1-s) = 1\) and \(S_{\text{SN}} = s + (1-s)P\), which is Gustafson.

Sun–Ni is the family of models indexed by \(g\). Amdahl and Gustafson are the endpoints people already knew.

## How \(g(P)\) is fixed by memory

Let total memory scale as \(M(P) = M(1) \cdot G(P)\). \(G(P) = P\) when every processor brings its own full memory node and the aggregate capacity is linear. \(G(P)\) grows more slowly when processors share a fixed memory pool.

Work need not track memory one-for-one. If the data of the problem scale as \(N^{d}\) and the operation count scales as \(N^{e}\), filling a memory that grew by \(G\) multiplies the work by

\[
g(P) = G(P)^{e/d}.
\]

Examples, taking \(G(P) = P\) (one memory node per processor):

| Workload | Memory | Work | \(g(P)\) |
|---|---|---|---|
| Explicit stencil, one unknown per cell | \(\Theta(N^3)\) on a 3D grid | \(\Theta(N^3)\) | \(P\) |
| Dense matrix multiply | \(\Theta(N^2)\) | \(\Theta(N^3)\) | \(P^{3/2}\) |
| Direct all-pairs \(N\)-body, particles stored once | \(\Theta(N)\) | \(\Theta(N^2)\) | \(P^{2}\) |
| Fixed input, strong scaling | unchanged | unchanged | \(1\) |

Gustafson’s law is the special case \(g(P) = P\). It is the correct memory-bounded model for the first row. It is an assumption, not a consequence, for the other rows.

## Where Gustafson overestimates

Gustafson overestimates achievable scaled speedup when the real workload cannot grow as fast as \(P\), that is when \(g(P) < P\).

The common cases are a fixed problem (\(g = 1\)), a shared-memory machine whose capacity grows slower than the core count, and a per-node memory cap that is already full at modest \(P\). Compare the two formulas at the same \(s\). For \(1 \le g(P) < P\) and \(0 < s < 1\),

\[
S_{\text{SN}}(P) = \frac{s + (1-s)g}{s + (1-s)g/P} < s + (1-s)P = S_{\text{Gustafson}}(P).
\]

The right-hand side pretends each processor is given a full extra copy of the original parallel work. The left-hand side only has \(g(P)\) copies available. The missing work is exactly the overestimate: Gustafson’s numerator is too large, and Gustafson’s denominator is too optimistic because it assumes the extra work fits in the original time window.

A short check with \(s = 0.05\), \(P = 1024\), \(g = 1\):

\[
S_{\text{Gustafson}} = 0.05 + 0.95 \cdot 1024 = 972.85, \qquad S_{\text{SN}} = S_{\text{Amdahl}} \approx 19.64.
\]

Quoting 973 as the speedup of a problem that was not allowed to grow overstates the delivered speedup by a factor of about fifty.

## Where Gustafson underestimates

Gustafson underestimates the speedup of the *largest memory-resident problem* when work grows faster than memory, so \(g(P) > P\). Dense matrix multiplication with a full node of memory per processor has \(g(P) = P^{3/2}\). Then

\[
S_{\text{SN}}(P) = \frac{s + (1-s)\,P^{3/2}}{s + (1-s)\,P^{1/2}}.
\]

For large \(P\) the ratio behaves as \(P\), the same leading order as Gustafson, but the constant factors differ. At \(s = 0.05\):

| \(P\) | \(g = P^{3/2}\) | \(S_{\text{SN}}\) | \(S_{\text{Gustafson}} = s+(1-s)P\) |
|---|---|---|---|
| 64 | 512 | \((0.05 + 486.4)/(0.05 + 7.6) = 63.59\) | 60.85 |
| 1024 | 32,768 | \((0.05 + 31129.6)/(0.05 + 30.4) = 1022.32\) | 972.85 |

The memory-bounded problem is larger than the fixed-time problem: filling the extra memory creates more than \(P\) times the original arithmetic, and one processor would take longer than \(P\) time units to repeat it. Gustafson’s linear workload never includes that extra arithmetic, so its speedup is the smaller number.

This underestimate has a side condition that matters in design. Sun–Ni speedup here is *not* a fixed-time claim. The denominator grows like \(P^{1/2}\), so the wall-clock time of the maximum GEMM is increasing. Gustafson remains the right formula when the constraint is a deadline. Sun–Ni is the right formula when the constraint is “use every byte, however long the larger problem takes.” Throughput in the strict sense of work per wall-clock second is \(\Theta(P)\) in both of those GEMM scalings; what Gustafson underestimates is the speedup ratio against the one-processor time of the bigger, memory-filling problem.

## Design reading

Use Gustafson when each rank can be given a constant amount of local work and the deadline is fixed. Switch to the Sun–Ni form, with the \(g\) that the complexity and the memory system actually provide, when the limit is capacity. If \(g(P) < P\), a Gustafson forecast is a high estimate of scaled speedup. If \(g(P) > P\), a Gustafson forecast is a low estimate of the speedup of the largest problem the memory can hold, and it is silent on the fact that this largest problem no longer finishes in the original time window.
