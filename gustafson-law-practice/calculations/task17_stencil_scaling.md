# Task 17 — Surface-to-Volume Ratio of a 7-Point Stencil

## Costs on one rank

The domain is a cube of \(N \times N \times N\) points, advanced by a 7-point finite-difference stencil (the point itself and its six orthogonal neighbors). Interior updates do \(\Theta(1)\) work per point, so a time step costs

\[
W_{\text{comp}} = \Theta(N^3).
\]

Decompose the cube onto \(P = Q^3\) ranks with a cubic process grid. Each rank owns a subcube of side

\[
n = \frac{N}{Q} = \frac{N}{P^{1/3}}.
\]

Local arithmetic is \(\Theta(n^3)\). The data the rank must exchange are the six faces of the subcube, one layer deep for a 7-point stencil:

\[
W_{\text{comm}} = \Theta(n^2) \qquad \text{(specifically \(6n^2\) face points sent, and \(6n^2\) received).}
\]

The communication-to-computation ratio that governs the rank is

\[
r = \frac{W_{\text{comm}}}{W_{\text{comp}}} = \Theta\left(\frac{n^2}{n^3}\right) = \Theta\left(\frac{1}{n}\right) = \Theta\left(\frac{P^{1/3}}{N}\right).
\]

For the concrete 7-point face count with one unknown per point, \(r = 6/n\) when the leading constants of compute and of face points are both taken as the point counts.

## Gustafson scaling: volume proportional to \(P\)

Fixed parallel time for a stencil whose work is \(\Theta(N^3)\) means constant work per rank (Task 16’s exponent with the stencil’s complexity):

\[
n = n_0 \quad\text{constant}, \qquad N(P) = n_0 \, P^{1/3}, \qquad N^3 = n_0^3 \, P.
\]

Domain volume therefore scales in proportion to \(P\). Substitute the constant local side into the ratio:

\[
r(P) = \frac{6}{n_0}.
\]

The ratio does not depend on \(P\). Growing the domain in proportion to the processor count, and giving every new rank its own copy of the original subcube, leaves the surface of each subcube and the volume of each subcube unchanged. Every rank communicates the same six faces and updates the same \(n_0^3\) points it updated at \(P = 1\). The communication-to-computation ratio is invariant.

That invariance is why a stencil weak-scales. Classical Gustafson efficiency keeps the floor \(1-\alpha\) only when the non-compute term is stable. Here the halo term is stable because it is proportional to \(n_0^2\) and \(n_0\) was held fixed. Aggregate communication across the machine is \(\Theta(P n_0^2)\) and aggregate arithmetic is \(\Theta(P n_0^3)\), so the machine-wide ratio is the same \(6/n_0\).

## The global surface moves the other way

The outer surface of the whole cube, ignoring the internal faces the decomposition creates, satisfies

\[
R_{\text{global}} = \frac{6N^2}{N^3} = \frac{6}{N} = \frac{6}{n_0}\, P^{-1/3}.
\]

This quantity *improves* (it falls) as the domain grows with \(P\). It is the right ratio for a single shared-memory sweep of a growing cube. It is the wrong ratio for the parallel algorithm. The parallel algorithm pays every subcube face, including faces that lie in the interior of the global cube, and those interior faces scale as \(P\), not as the outer surface \(N^2\). Quoting the global improvement as if it were the parallel communication savings overstates the benefit of weak scaling. The parallel ratio stays flat; it does not inherit the \(P^{-1/3}\) improvement.

## Where the ratio degrades

Hold the global cube fixed and increase \(P\). That is strong scaling, \(N = N_0\), \(n = N_0 P^{-1/3}\):

\[
r_{\text{strong}}(P) = \frac{6}{n} = \frac{6}{N_0}\, P^{1/3}.
\]

The ratio degrades as the cube root of the processor count. Each doubling of linear resolution of the process grid multiplies the relative halo cost by two, because the subcube volume falls by eight while each face falls only by four. At large \(P\) the halo term dominates a fixed grid even though the same stencil, run weak-scaled at constant \(n_0\), still has \(r = 6/n_0\).

## Summary

| Experiment | Local side \(n\) | \(r\) as \(P\) grows |
|---|---|---|
| Gustafson, volume \(\propto P\) | constant \(n_0\) | constant \(6/n_0\) |
| Global surface of the growing cube | — | improves as \(P^{-1/3}\) |
| Strong scaling, \(N\) fixed | \(N_0 P^{-1/3}\) | degrades as \(P^{1/3}\) |

Under Gustafson’s hypothesis the communication-to-computation ratio of the 7-point decomposition neither improves nor degrades. Constancy is the favorable result: it is what keeps a single serial-fraction measurement meaningful as \(P\) increases. The ratio improves only in the undecomposed global accounting, and it degrades as soon as extra processors are used to shrink the subcubes instead of to enlarge the domain.
