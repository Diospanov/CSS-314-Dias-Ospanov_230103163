# Task 18 — Direct \(N\)-Body and Barnes–Hut at Constant Iteration Time

The constraint in this task is constant wall time per iteration while the particle count \(N\) changes with the processor count \(P\). Storage per processor is not the constraint. The serial-to-parallel ratio below is Gustafson’s time-fraction on the parallel machine,

\[
\alpha(P) = \frac{T_{\text{serial}}(P)}{T_{\text{serial}}(P) + T_{\text{parallel}}(P)},
\]

with \(T_{\text{parallel}}\) the length of the balanced arithmetic region.

Two serial contributions show up in both methods: a pass over the bodies that is not inside the force loop (reading the snapshot, writing diagnostics) of size \(\Theta(N)\), and a final reduction. The pass is the one that moves \(\alpha\). A tree reduction of a few scalars is only \(\Theta(\log P)\) and is noted where it matters.

## Direct all-pairs

Every target feels every source. Arithmetic is \(\Theta(N^2)\), and a balanced decomposition puts it in

\[
T_{\text{parallel}} = a \frac{N^2}{P}, \qquad a > 0.
\]

Hold that region at a constant \(\tau\):

\[
a \frac{N^2}{P} = \tau \implies N(P) = N_0 \sqrt{P}, \qquad N_0 = \sqrt{\tau/a}.
\]

Particle count grows with the square root of the machine, not with the machine. Memory per processor then *declines* as \(N/P = \Theta(P^{-1/2})\).

The \(\Theta(N)\) serial pass takes

\[
T_{\text{serial}} = b N = b N_0 \sqrt{P}, \qquad b > 0,
\]

which is no longer a constant. Total iteration time \(\tau + b N_0 \sqrt{P}\) itself grows, so a strictly constant deadline cannot be kept forever; the largest \(P\) that still fits in a deadline \(T\) solves \(\tau + b N_0 \sqrt{P} \le T\). Inside the range where the iteration is still run, the observed fraction is

\[
\alpha_{\text{direct}}(P) = \frac{b N_0 \sqrt{P}}{b N_0 \sqrt{P} + \tau}.
\]

This increases with \(P\) and tends to 1. The parallel region was successfully held at \(\tau\); the serial region was not, because it tracks \(N\) and \(N\) had to grow. Relative to the parallel region the serial/parallel time ratio is

\[
\frac{T_{\text{serial}}}{T_{\text{parallel}}} = \frac{b N_0}{\tau} \sqrt{P} = \Theta(P^{1/2}).
\]

A constant-\(\alpha\) Gustafson model does not describe this regime. The work ratio \(W_{\text{serial}}/W_{\text{parallel}} = \Theta(N)/\Theta(N^2) = \Theta(P^{-1/2})\) moves in the opposite direction and is the wrong ratio to insert into Gustafson’s formula: \(\alpha\) is a ratio of times on the parallel run, and the serial pass was never divided by \(P\).

## Barnes–Hut

The tree walk replaces the source loop by a descent whose accepted interactions number \(\Theta(\log N)\) per target under the usual opening-angle assumptions, for a total operation count \(\Theta(N \log N)\). Balanced across \(P\) processors,

\[
T_{\text{parallel}} = a_b \frac{N \log N}{P}.
\]

Constant parallel time \(\tau\) requires

\[
N \log N = \frac{\tau}{a_b}\, P.
\]

The solution satisfies

\[
N(P) \sim \frac{P}{\log P}
\]

in the sense that \(N \log N \sim P\) implies \(N \sim P / \log P\). Many more particles fit in the same parallel-time budget than in the direct method (\(P/\log P\) against \(P^{1/2}\)).

Whether \(\alpha\) stays healthy depends on what was left serial.

**Tree build and force walk both parallel, serial remnant \(\Theta(\log P)\).** Then

\[
\alpha_{\text{BH, log}}(P) = \frac{\beta \log_2 P}{\beta \log_2 P + \tau}.
\]

The fraction grows, but only with the logarithm. At \(\beta/\tau = 0.001\), \(\alpha\) is about \(0.01\) near \(P = 1024\) (\(\log_2 1024 = 10\)) and about \(0.016\) near \(P = 65536\). The serial/parallel time ratio is \(\Theta(\log P)\), far milder than the direct method’s \(\Theta(P^{1/2})\). This is the regime in which a Barnes–Hut code can look approximately Gustafson-like over several doublings of the machine: \(N\) must still grow a little slower than linearly, and \(\alpha\) must still be allowed to creep, but the creep is the collective term of Task 12 rather than a square-root blow-up.

**A leftover \(\Theta(N)\) serial pass (serial tree build, or serial I/O of every particle).** Then \(T_{\text{serial}} = b N = \Theta(P/\log P)\), which already exceeds any fixed \(\tau\) at moderate \(P\). Constant iteration time is lost, and

\[
\alpha_{\text{BH, serial\ pass}}(P) \to 1
\]

faster than in the direct method, because \(N\) is larger. The algorithm only wins if that pass is parallelized. The complexity improvement \(\Theta(N^2) \to \Theta(N \log N)\) does not by itself protect \(\alpha\); it increases the particle count that a constant parallel time can support, and any serial loop over those particles becomes the new bottleneck.

## Side-by-side

| | Direct all-pairs | Barnes–Hut |
|---|---|---|
| Parallel complexity | \(\Theta(N^2/P)\) | \(\Theta(N \log N / P)\) |
| \(N\) for constant parallel time | \(\Theta(P^{1/2})\) | \(\Theta(P/\log P)\) |
| \(\alpha\) if the only extra term is \(\Theta(\log P)\) | slowly rising, not the leading threat | slowly rising, \(\Theta(\log P)\) in the numerator |
| \(\alpha\) if a \(\Theta(N)\) pass stays serial | \(\dfrac{c\sqrt{P}}{c\sqrt{P}+\tau} \to 1\) | \(\dfrac{c P/\log P}{c P/\log P+\tau} \to 1\), and sooner |
| Constant-\(\alpha\) Gustafson model | breaks as soon as \(N\) grows | usable only after every \(\Theta(N)\) pass is parallel, and then only approximately, with a logarithmic leak |

The shift in the serial/parallel ratio is therefore opposite in origin for the two regimes. Direct summation, even with a perfect force loop, imports a growing serial fraction through the \(\Theta(N)\) work that scales like \(\sqrt{P}\) once time is held fixed. Barnes–Hut pushes the particle count up near \(P/\log P\) and stays close to a constant \(\alpha\) only when the tree build scales with the force walk; the ratio that remains moves from a constant toward 1 like \(\log P\), which is the isoefficiency correction \(W = \Theta(P \log P)\) of Task 14 rather than a change of the force-loop exponent.
