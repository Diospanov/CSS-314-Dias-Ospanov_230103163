# Task 24 — Hardware Audit and the Measured Gap

The curves in `plots/scaling_comparison.png` (and the vector copy `plots/scaling_comparison.pdf`) come from one run of `benchmarks/weak_scale_bench/bench.py`, fitted by `benchmarks/fit_gustafson.py`. Raw times are `benchmarks/results.csv`. Five timed runs were kept at each process count after one discarded warmup. The pool was created before the clock started.

## What was timed

Each process runs the same sine recurrence for `n_parallel = 1_200_000` iterations. The parent runs the same recurrence for `n_serial = 50_000` iterations before the map and again after it. The checksum of every run was `1148287.651325`, so the loop result was live and the arithmetic did not change between repeats.

If those trip counts cost the same per iteration and nothing else is in the window, the serial time-fraction would be

\[
\alpha_{\text{trip}} = \frac{2 \times 50000}{2 \times 50000 + 1200000} = \frac{1}{13} \approx 0.0769.
\]

The fit below is much larger. The extra is overhead, not a different kernel.

## Hardware the run actually used

Queried from this machine’s processor object:

| Item | Value |
|---|---|
| Processor | 12th Gen Intel Core i5-12500H |
| Cores reported | 12 |
| Logical processors | 16 |
| Max clock reported by the firmware object | 2500 MHz |
| L2 cache, total | 9216 KB (9 MB) |
| L3 cache | 18432 KB (18 MB) |

The published specification of this processor identifies the core mix behind those counts: four performance cores with hyper-threading and eight efficiency cores without it (Alder Lake-H). The 9 MB of L2 matches that layout (1.25 MB private on each performance core, 2 MB shared by each group of four efficiency cores). The shared last-level cache is the 18 MB above. Base power is 45 W and the performance-core turbo specification is 4.50 GHz; the 2500 MHz figure is the base, which is what the firmware object returns. The memory controller is dual-channel and is specified for DDR4-3200, DDR5-4800, LPDDR4x-4267, and LPDDR5-5200. The installed DIMM size and the speed actually trained on this laptop were not read. The package is one socket, so this run is not a cross-socket NUMA experiment.

The working set of the kernel is a handful of scalars. It does not fill the 18 MB L3 and it does not stream through DRAM. Cache capacity and memory channels are not the terms that move the curves. What can move them is which cores Windows hands the processes, the power shared by those cores, and the cost of shipping a task to each process.

## Recorded times

\(T\) is the mean wall time of the five runs. The standard deviation is the sample standard deviation. SEM is that deviation divided by \(\sqrt{5}\). Scaled speedup for each run is \(S = P \cdot \overline{T}(1) / T_{\text{run}}\), using the mean one-process time \(0.168941\,\text{s}\) as the size of one unit of work. The table reports the mean of those five speedups, and the SEM of that mean.

| \(P\) | Mean \(T\) (s) | Std. dev. (s) | SEM of \(T\) (s) | Mean \(S\) | SEM of \(S\) |
|---|---|---|---|---|---|
| 1 | 0.168941 | 0.012877 | 0.005759 | 1.0043 | 0.0314 |
| 2 | 0.151844 | 0.004552 | 0.002036 | 2.2268 | 0.0297 |
| 4 | 0.173160 | 0.011613 | 0.005193 | 3.9163 | 0.1148 |
| 8 | 0.238906 | 0.026653 | 0.011920 | 5.7084 | 0.2573 |
| 12 | 0.261411 | 0.006472 | 0.002894 | 7.7589 | 0.0842 |
| 16 | 0.301434 | 0.013733 | 0.006141 | 8.9819 | 0.1794 |

\(S(1)\) is \(1.0043\) rather than \(1\) because it is an average of reciprocals of the five one-process times. The mean of \(1/T\) sits slightly above \(1/\overline{T}\).

## The fitted serial fraction

Gustafson’s model on these six points is \(S(P) = P - \alpha(P-1)\). The least-squares \(\alpha\), minimizing the squared residual of that expression, is

\[
\alpha_{\text{observed}} = 0.4148, \qquad R^2 = 0.941.
\]

The same \(\alpha\) is drawn as an Amdahl curve on the figure. At 16 processes that Amdahl curve is

\[
S_{\text{Amdahl}}(16) = \frac{1}{0.4148 + 0.5852/16} \approx 2.22,
\]

against a measured scaled speedup of \(8.98\) and a Gustafson value on the fitted line of about \(9.78\). The points follow the rising weak-scaling curve. They do not follow the strong-scaling ceiling. Efficiency at 16 processes is \(8.98/16 \approx 0.56\), in the neighborhood of the Gustafson floor \(1 - \alpha \approx 0.585\) and nowhere near Amdahl’s \(2.22/16 \approx 0.14\).

## Why the points leave the ideal line

Four observations in the table are the deviation, and each has a cause that the constant-\(\alpha\) formula does not contain.

**Wall time is not constant.** From 2 processes to 16 it rises from \(0.152\,\text{s}\) to \(0.301\,\text{s}\). Classical Gustafson assumes a fixed window. A window that lengthens as \(P\) grows is the communication penalty of Task 12: here the “message” is the process map and the return of each checksum, and its cost grows as more processes are joined. A single \(\alpha\) is the best constant compromise (\(R^2 = 0.94\)), and the residuals still show the growth. \(P = 2\) and \(P = 4\) sit above the fitted line; \(P = 16\) sits below it.

**Two processes beat one.** Mean time falls from \(0.169\,\text{s}\) to \(0.152\,\text{s}\), and the speedup \(2.23\) clears 2 by several standard errors of the mean (\(0.030\)). A pure serial-fraction model cannot produce \(S(P) > P\). The one-process samples are also the noisiest at the low end (one run at \(0.191\,\text{s}\)). The likely practical causes are scheduling and frequency: a single worker does not occupy the chip the way two performance cores do, and this kernel is so short that a small shift in boost dominates the planted serial work. It is a real feature of these thirty samples, not a plotting artifact.

**The large step is between 4 and 8 processes.** Mean time goes from \(0.173\,\text{s}\) to \(0.239\,\text{s}\), the biggest jump in the table, and \(P = 8\) has the widest error bar (speedup SEM \(0.26\), driven by a \(0.027\,\text{s}\) standard deviation). Four processes fit on the four performance cores. Eight processes do not. Hyper-threads and efficiency cores then enter the pool. They are not the same speed as the performance cores, so a weak-scaling assumption of identical workers fails exactly where the core types change. The further rise from 12 to 16 processes continues that mix.

**The fitted \(0.415\) is not the trip-count \(0.077\).** About four fifths of the observed serial fraction is overhead around the kernel: building the task list, waking workers, and reducing Python floats, on top of two short serial recurrences. The kernel’s working set never leaves the core, so this is not a memory-channel effect and not an L3-capacity effect. It is coordination plus heterogeneous cores. A longer kernel would shrink \(\alpha\) toward the trip-count value; this kernel was kept near two tenths of a second so the five-by-six run stayed small, and the overhead is correspondingly honest and large.

Power and temperature sit underneath the core-type effect. Sixteen logical processors share a 45 W envelope, so clocks fall as the pool grows. Frequencies were not sampled during the run. The monotone rise in time from 4 to 16 processes is what a power limit and a shift onto efficiency cores both predict; the data do not separate those two contributions.

NUMA across sockets does not explain the gap. There is one package. The dual memory channels are irrelevant to a kernel that does not stream.

## Reading the figure

`plots/scaling_comparison.png` draws four series: ideal \(S = P\), the Gustafson line at \(\alpha = 0.4148\), the measured means with SEM bars, and Amdahl’s law at that same \(\alpha\). Use the figure together with the table. The line is a summary of six noisy points on a hybrid laptop, not a claim that this Python harness has a constant \(41\%\) serial region inside the arithmetic. The arithmetic’s own serial share is \(7.7\%\). The rest is the machine and the runtime, which is the quantity Task 23 asked the regression to absorb.
