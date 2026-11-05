# Task 13 — Two Algorithms Where Fixed-Time Scaling Breaks

Gustafson’s premise is that the parallel wall time can be held constant while the problem grows in step with \(P\). That premise needs two things at once: the operation count per processor must stay constant, and the number of sequential steps the algorithm takes must stay constant. The two algorithms below each violate one of those requirements as soon as the problem is enlarged in the natural way.

## 1. Direct all-pairs \(N\)-body

**Algorithm.** Store \(N\) particles. Every step, for every particle, accumulate the force from every other particle. The operation count is \(\Theta(N^2)\). A balanced parallel split gives each processor \(N/P\) particles as targets and all \(N\) particles as sources, so the arithmetic per processor is

\[
T_{\text{comp}}(P) = \Theta\left(\frac{N}{P} \cdot N\right) = \Theta\left(\frac{N^2}{P}\right).
\]

**The scaling that people reach for first.** “Weak scaling” is often implemented as a constant number of particles per processor, \(N = cP\). That choice does keep the *storage* per processor constant. It does not keep the *time* constant:

\[
T_{\text{comp}} = \Theta\left(\frac{(cP)^2}{P}\right) = \Theta(P).
\]

Wall time grows linearly with the machine. The reason is the all-to-all interaction. Each new particle is a source for every target, including the targets already owned by existing processors. Adding a processor adds targets, and it also lengthens the source loop on every processor that was already there. Work per processor is \(\Theta(N)\), and \(N\) itself grew with \(P\).

**What constant time would actually require.** Set \(N^2/P = \Theta(1)\), so \(N = \Theta(P^{1/2})\). Particle count then grows more slowly than processor count, memory per processor *falls*, and any leftover serial pass over the particles (I/O, a diagnostic reduction over \(N\) bodies) lasts \(\Theta(P^{1/2})\) and eventually consumes the time budget. Either way the textbook picture — constant \(\alpha\), constant time, \(N \propto P\) — is unavailable. The complexity, not the implementation quality, is what breaks it. A tree code changes the complexity; it is a different algorithm, analyzed in Task 18.

## 2. Conjugate gradient on a growing Poisson grid

**Algorithm.** Solve \(Ax = b\) for a standard second-order elliptic operator by conjugate gradient. Each iteration is a sparse matrix-vector product, a handful of vector axpy operations, and two or three global dot products. On a three-dimensional grid with \(n\) unknowns per processor the local matvec is \(\Theta(n)\) and each dot product ends in an all-reduce.

**Local work can be held constant and the iteration still slows down.** Under the usual weak-scaling layout, \(n\) is fixed and the global grid grows as \(P\). Two separate effects then push the time of the *solve*, which is the time the user waits for, upward.

*Effect A — the collective grows.* A tree reduction across \(P\) ranks costs

\[
T_{\text{reduce}} = \Theta(\log P)
\]

in latency, independent of how large \(n\) is. The time of one iteration is

\[
T_{\text{iter}} = \Theta(n) + \Theta(\log P).
\]

With \(n\) fixed, the second term is an ever-larger share of the iteration. This is the communication extension of Task 12 inside a real solver. Classical Gustafson would have folded the dots into a constant \(\alpha\). They are not constant.

*Effect B — the iteration count grows.* For the model Poisson problem the condition number of the discrete operator scales as \(\Theta(h^{-2})\), and the global mesh spacing \(h\) shrinks, or the domain grows, when the grid is refined or enlarged with \(P\). Unpreconditioned CG then takes

\[
I(P) = \Theta\!\left(\sqrt{\kappa(A)}\right) = \Theta(P^{r})
\]

iterations for some positive \(r\) that depends on how \(N\) scales (for a cube of fixed physical domain refined in every direction, \(N \propto P\) implies \(h \propto P^{-1/3}\) and \(\sqrt{\kappa} \propto P^{1/3}\)). Total time is \(I(P) \cdot T_{\text{iter}}\). Even a perfect, latency-free matvec of constant size per processor produces a solve that lengthens as \(P^{1/3}\).

**Where the constant-runtime premise fails.** Gustafson scaling can describe one matvec with fixed \(n\). It does not describe the solve. The algorithm’s critical path is a data-dependent number of iterations, and that number is an increasing function of the problem dimension the extra processors were used to buy. Holding the local unknown count constant does not hold the iteration count constant. A multigrid preconditioner can flatten \(I(P)\); until it does, reporting a Gustafson speedup for the solver from a single-iteration model overstates the scaling of the program that actually runs.

## Shared pattern

In both algorithms, enlarging the problem changes the control structure of the work, not only its volume. All-pairs lengthens an inner loop that every processor executes. CG lengthens the outer iteration and the reduction chain. Fixed time survives only when both the local operation count and the number of sequential rounds stay bounded as \(P\) grows. These two algorithms, scaled in the straightforward way, violate that bound.
