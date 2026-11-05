# Gustafson’s Law and Weak Scaling

Practice set on scaled speedup: Amdahl’s fixed-size model, Gustafson’s fixed-time model, the calculations that follow from them, and a weak-scaling measurement on this machine. Every artifact listed below lives in this directory.

## How to reproduce the plots

No compile step. The scripts need CPython 3.11 and `matplotlib`.

```
python benchmarks/simulator.py
python benchmarks/weak_scale_bench/bench.py
python benchmarks/fit_gustafson.py
```

`simulator.py` writes `benchmarks/amdahl_gustafson.csv` and `plots/simulator_overlay.png` (plus a PDF). The benchmark writes `benchmarks/results.csv`. The fit reads that CSV and writes `plots/scaling_comparison.png` (plus a PDF). Details of the harness are in `benchmarks/weak_scale_bench/README.md`.

## Rules worth keeping

Scaled speedup, with the parallel run normalized so serial time \(\alpha\) and parallel time \(1-\alpha\) sum to 1, is

\[
S(P) = \alpha + (1-\alpha)P = P - \alpha(P-1).
\]

Efficiency tends to \(1-\alpha\), not to 0:

\[
E(P) = 1 - \alpha + \frac{\alpha}{P}, \qquad \lim_{P \to \infty} E(P) = 1-\alpha.
\]

Amdahl’s law with a fixed workload whose serial *work* fraction is \(s\) is a different experiment:

\[
S_{\text{Amdahl}}(P) = \frac{1}{s + (1-s)/P} \to \frac{1}{s}, \qquad E_{\text{Amdahl}}(P) \to 0.
\]

The number that goes into Gustafson’s formula is the serial share of **time on the scaled run**. The number that goes into Amdahl’s formula is the serial share of **work in the original problem**. Inserting the first number into the second formula is what made a \(0.4\%\) serial fraction look like a ceiling of \(250\times\) on the 1,024-node nCUBE, while the scaled runs exceeded \(1{,}000\times\). At \(\alpha = 0.004\) and \(P = 1024\), Gustafson’s formula gives \(S = 1019.9\).

Consequences used throughout the calculations:

- A constant \(\alpha\) is a constant tax. At \(\alpha = 0.04\), efficiency is already \(0.9625\) at 16 processors and \(0.96000244\) at 16,384. It does not keep falling.
- The largest \(\alpha\) that still delivers scaled speedup \(S\) on \(P\) processors is \(\alpha_{\max} = (P - S)/(P - 1)\). For \(P = 8192\) and \(S \ge 7500\), that is \(692/8191 \approx 0.0845\).
- Holding the parallel time constant fixes the dimension through the complexity. Dense GEMM needs \(N \propto P^{1/3}\). A 3D grid whose memory is \(\Theta(N^3)\) and whose per-node memory is capped needs the same exponent: at 32 GB per node, \(N\) grows by \(4\) at 64 nodes and by \(8\) at 512 nodes, relative to the one-node cube.
- A 7-point stencil decomposed into fixed local cubes has a communication-to-computation ratio that stays constant as the global volume grows with \(P\). The ratio degrades only when extra processors shrink the cubes.
- Sun and Ni’s \(g(P)\) recovers both laws: \(g = 1\) is Amdahl, \(g = P\) is Gustafson. Gustafson overestimates scaled speedup when memory cannot grow the work that fast, and underestimates the speedup of a memory-filling problem whose work grows faster than \(P\) (GEMM at \(g = P^{3/2}\)).
- A communication term \(C(P) = \beta \log_2 P\) or \(\gamma P^{1/2}\) replaces the denominator \(1\) by \(1+C(P)\) and removes the efficiency floor.
- Isoefficiency of a pure Gustafson workload is linear, \(W = \Theta(P)\), because the only overhead is a serial section of constant length. Any per-processor cost that grows with \(P\) pushes the isoefficiency function above linear.
- At fixed wall time, energy scales roughly with \(P\) and energy per unit work tends to a constant set by idle power, active power, and \(\alpha\).

## When to design for weak scaling

Design the program so that adding a processor adds a constant amount of local work and does not add rounds of synchronization.

Do that when the scientific question grows with the machine and the deadline does not: a larger mesh, a larger ensemble, a longer Monte Carlo. Give every rank the same local box or the same number of samples. Keep setup, output, and reductions off the critical path, or accept an explicit \(\log P\) term and budget for it. Check that the algorithm’s iteration count and inner-loop complexity stay put when the global size grows. All-pairs \(N\)-body and unpreconditioned conjugate gradient on a growing Poisson grid fail that check (Task 13). Breadth-first search and PageRank on power-law graphs fail it because balance, diameter, and the edge cut move with the graph (Task 20).

Stay with Amdahl’s question when the input is frozen and the goal is a shorter answer: a fixed transaction batch, a fixed image, a latency target. Extra processors then only divide the parallel part, and \(1/s\) is a real ceiling.

A practical test before trusting a single \(\alpha\): double \(P\), double the parallel work, and see whether the wall time stays flat. If it rises, fit a \(C(P)\) rather than a bigger constant serial fraction. If the rise starts where the machine changes core type or NUMA domain, the model is no longer the whole story.

## What this laptop did

On the i5-12500H (12 cores, 16 logical processors, 9 MB L2, 18 MB L3), the harness of Task 22 at process counts \(1,2,4,8,12,16\), five runs each, produced

\[
\alpha_{\text{observed}} = 0.4148 \quad (R^2 = 0.941).
\]

Mean wall time was \(0.169\,\text{s}\) at one process and \(0.301\,\text{s}\) at sixteen. Scaled speedup at sixteen processes was \(8.98\), against about \(9.78\) on the fitted Gustafson line and about \(2.22\) on Amdahl’s curve at the same \(\alpha\). The trip counts alone would have implied \(\alpha \approx 0.077\). The gap is process-coordination overhead and the step off the four performance cores onto efficiency cores and hyper-threads, between 4 and 8 processes. The full table, the error bars, and that hardware reading are in `analysis/task24_hardware_audit.md`.

## Index

| Path | Task |
|---|---|
| `theory/task01_scaling_models.md` | Fixed-size versus fixed-time; dimension as \(P \to \infty\) |
| `theory/task02_derivation.md` | Derivation of \(S = s + pP = P - \alpha(P-1)\) |
| `theory/task03_serial_invariance.md` | Why \(\alpha\) is measured on the parallel machine |
| `theory/task04_asymptotic_limits.md` | Limits of efficiency under both laws |
| `theory/task05_historical_ncube.md` | 1,024-processor nCUBE and the ceiling of \(250\) |
| `calculations/task06_parametric_table.md` | \(S\) and \(E\) at \(\alpha = 0.04\) for six processor counts |
| `calculations/task07_tolerable_serial.md` | \(\alpha_{\max} = 692/8191\) on 8,192 cores |
| `calculations/task08_cross_divergence.md` | Amdahl \(11.47\) versus Gustafson \(117.84\) at \(P = 128\) |
| `calculations/task09_multicomponent.md` | Three-phase run, \(\alpha = 0.08\), \(P = 512\) and \(2048\) |
| `calculations/task10_memory_growth.md` | 32 GB/node cap, \(N\) at 64 and 512 nodes |
| `theory/task11_sun_ni_comparison.md` | Memory-bounded speedup, \(g(P)\) |
| `theory/task12_communication_penalty.md` | Denominator \(1 + C(P)\) |
| `theory/task13_failure_cases.md` | All-pairs \(N\)-body and Poisson CG |
| `theory/task14_isoefficiency.md` | Linear isoefficiency, and when it breaks |
| `theory/task15_energy_scaling.md` | Idle and active energy at fixed wall time |
| `calculations/task16_gemm_scaling.md` | \(N \propto P^{1/3}\) for dense GEMM |
| `calculations/task17_stencil_scaling.md` | Surface-to-volume of a 7-point stencil |
| `analysis/task18_nbody_scaling.md` | Direct summation versus Barnes–Hut |
| `analysis/task19_monte_carlo.md` | PRNG setup, reductions, output |
| `analysis/task20_graph_processing.md` | BFS and PageRank on power-law graphs |
| `benchmarks/simulator.py` | Sweep of both laws, CSV and overlay plot |
| `benchmarks/amdahl_gustafson.csv` | Simulator output |
| `plots/simulator_overlay.png` | Speedup and efficiency overlay |
| `benchmarks/weak_scale_bench/bench.py` | Multiprocessing weak-scaling harness |
| `benchmarks/weak_scale_bench/README.md` | Run instructions for the harness |
| `benchmarks/results.csv` | Five raw times at each process count |
| `benchmarks/fit_gustafson.py` | Least-squares \(\alpha\) and the comparison figure |
| `plots/scaling_comparison.png` | Ideal, Gustafson, measured, Amdahl |
| `analysis/task24_hardware_audit.md` | CPU, caches, and why the points scatter |
