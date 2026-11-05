# Task 01 — Strong Scaling and Weak Scaling

## 1. What each law holds fixed

Gene Amdahl (1967) and John Gustafson (1988) answer different questions. Both split a run into a serial part and a parallel part. They disagree about which quantity stays constant when the processor count \(P\) grows.

**Amdahl** holds the *problem* fixed. The amount of serial work and the amount of parallel work are properties of one chosen input. Extra processors can only divide the parallel work. The serial work is untouched, so it becomes a larger share of the remaining time.

**Gustafson** holds the *wall-clock time* fixed. Processors added to the machine are given additional useful work, typically a larger mesh, a larger ensemble, or a finer physical model. The run is still expected to finish in about the same time. Speedup is then the ratio of the work completed in that fixed time to the work one processor could finish in the same time.

## 2. How the problem dimension behaves as \(P \to \infty\)

Let the problem dimension be a size parameter \(N\) (grid points, particles, matrix order, Monte Carlo samples) and let the operation count be \(W(N)\).

Under Amdahl’s assumptions \(N\) is a constant \(N_0\). Then \(W\) is constant as well. As \(P \to \infty\) the parallel piece of the runtime shrinks toward zero and the runtime approaches the serial piece. If \(s \in (0,1]\) is the serial fraction of the original work,

\[
\lim_{P \to \infty} S_{\text{Amdahl}}(P) = \lim_{P \to \infty} \frac{1}{s + (1-s)/P} = \frac{1}{s}.
\]

The dimension never grows, so the ceiling \(1/s\) is a property of that one problem size.

Under Gustafson’s assumptions the scientifically relevant dimension is the largest problem that still finishes in the allotted time. For an algorithm whose parallel work grows linearly with the data assigned to each processor, total work scales as

\[
W(P) = \Theta(P) \qquad \text{as } P \to \infty,
\]

so \(N \to \infty\). The precise map from \(P\) to \(N\) depends on complexity: \(N \propto P\) when \(W \propto N\), and \(N \propto P^{1/3}\) when \(W \propto N^3\) (see Task 16). In every case the dimension is an increasing function of \(P\), and scaled speedup

\[
S(P) = P - \alpha(P-1)
\]

grows without a finite ceiling when the serial time-fraction \(\alpha\) is constant and strictly less than 1.

## 3. Why the names “fixed-size” and “fixed-time” fit

Amdahl’s law is **fixed-size** scaling because the experiment changes only \(P\). The input, the memory footprint, and \(W(N_0)\) stay at their one-processor values. This is strong scaling: the same job, more workers, less work per worker.

Gustafson’s law is **fixed-time** scaling because the experiment changes \(P\) and \(N\) together so that the parallel runtime stays constant. Each processor keeps roughly a full unit of work. This is weak scaling: a larger job, more workers, the same work per worker, and the same deadline.

The physical divergence follows from that choice. Amdahl describes a machine applied to a frozen workload, which is the right model for a latency-sensitive job whose input cannot grow (an overnight batch of fixed transactions, a single diagnostic on a fixed image). Gustafson describes how large scientific codes are actually used: a bigger computer is built to run a bigger problem in the same operational window (a shift, a weather cycle, a design turnaround). The serial work still exists, but it is measured against a parallel workload that grew with the machine, so it does not impose a constant speedup ceiling.
