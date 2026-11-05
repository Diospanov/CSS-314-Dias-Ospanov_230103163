# Task 03 — Where the Serial Fraction Is Measured

## The apparent contradiction

Take a code whose serial work is a fraction of a percent of a large parallel run. Amdahl’s ceiling \(1/s\) then sits in the low hundreds. A 1,024-processor run with a measured serial share near \(0.4\%\) would be declared incapable of more than

\[
\frac{1}{0.004} = 250
\]

times speedup. Experiments on that class of machine nevertheless finished scaled problems more than \(1{,}000\) times faster than a single processor (Task 05). The arithmetic is not wrong. The fraction being inserted into Amdahl’s formula was measured in a different frame from the fraction Amdahl defined.

## Two frames for the same words “serial fraction”

**Amdahl’s frame is the uniprocessor, and the problem is frozen.**

Run a problem of size \(W\) on one processor. Let \(\sigma\) be the serial work and \(\pi\) the parallel work, in processor-seconds, with

\[
W = \sigma + \pi, \qquad s_{\text{Amdahl}} = \frac{\sigma}{\sigma+\pi}.
\]

Spread the same \(W\) over \(P\) processors. Parallel work becomes \(\pi/P\) seconds of wall time and serial work remains \(\sigma\), so

\[
S_{\text{Amdahl}}(P) = \frac{\sigma+\pi}{\sigma+\pi/P} = \frac{1}{s_{\text{Amdahl}} + (1-s_{\text{Amdahl}})/P}.
\]

Here \(s_{\text{Amdahl}}\) cannot shrink when \(P\) grows, because neither \(\sigma\) nor \(\pi\) is allowed to change. As \(P\) increases, \(\sigma\) occupies almost all of the wall time. That is a statement about a fixed numerator \(W\).

**Gustafson’s frame is the parallel machine, after the problem has been enlarged.**

On \(P\) processors the wall time is held near a constant \(T\), and the parallel portion of that wall time is filled with new work. Let the observed split of \(T\) be

\[
T = \sigma_T + \pi_T, \qquad \alpha = \frac{\sigma_T}{\sigma_T+\pi_T}.
\]

\(\alpha\) is a fraction of *time on the scaled run*, not a fraction of the original small problem. The workload whose speedup we quote is the scaled one. Its one-processor time is \(\sigma_T + P\pi_T\), and

\[
S(P) = \frac{\sigma_T + P\pi_T}{\sigma_T+\pi_T} = P - \alpha(P-1).
\]

## How the parallel-machine measurement removes the ceiling

Suppose the serial work stays an absolute \(\sigma\) while the analyst grows only the parallel work, assigning each new processor its own \(\pi\) seconds of parallel computation. On the parallel machine

\[
\alpha(P) = \frac{\sigma}{\sigma+\pi}.
\]

If \(\sigma\) and \(\pi\) are both held constant in seconds, \(\alpha\) itself is constant, and \(S(P)\approx (1-\alpha)P\) still grows without bound.

Now form the quantity an Amdahl-style ratio would see if it were applied to this *same scaled* workload. The scaled work is \(\sigma + P\pi\), so the serial share of that work is

\[
s_{\text{scaled}}(P) = \frac{\sigma}{\sigma + P\pi} = \frac{\alpha}{\alpha + (1-\alpha)P}.
\]

As \(P \to \infty\),

\[
s_{\text{scaled}}(P) \to 0.
\]

The serial overhead did not vanish from the wall-clock trace. \(\sigma\) is still there and still lasts \(\alpha T\) seconds on every run. What vanished is the serial share of the *enlarged* workload. Amdahl’s ceiling \(1/s_{\text{scaled}}\) therefore recedes to infinity as the problem grows. There is no contradiction with a large scaled speedup, because the \(s\) that would have produced a low ceiling was the serial share of the small frozen problem, and that is not the problem the 1,024 processors ran.

## A numerical picture of the two frames

Use \(\alpha = 0.004\) observed on \(P = 1024\) processors, with \(T\) normalized to 1. Then \(\sigma_T = 0.004\) and \(\pi_T = 0.996\).

- Gustafson, using the parallel-machine fraction: \(S = 1024 - 0.004 \cdot 1023 = 1019.908\).
- The serial share of that scaled workload, in the uniprocessor accounting, is \(s_{\text{scaled}} = 0.004 / 1019.908 \approx 3.92 \times 10^{-6}\).
- Amdahl’s ceiling computed from \(s_{\text{scaled}}\) is about \(2.55 \times 10^{5}\), far above 1,024. The run is nowhere near that ceiling.
- Amdahl’s ceiling computed by mistakenly inserting the parallel-machine \(\alpha = 0.004\) is 250, which sits *below* the scaled speedup. That insertion treats a time-fraction of the large run as if it were the work-fraction of a small run.

The second bullet is the resolution. Measuring the fraction on the parallel machine tells you \(\alpha\), the quantity Gustafson’s formula needs. It does not tell you \(s_{\text{Amdahl}}\) for a smaller problem, and it does not tell you that \(4\) parts in \(1{,}000\) of the *scaled* work are serial. Those \(4\) parts in \(1{,}000\) are \(4\) parts in \(1{,}000\) of the *time*. Of the work, they are \(4\) parts in about \(1{,}020{,}000\).

## Consequence for performance arguments

A short serial section throttles strong scaling of a frozen input, because every added processor has less parallel work left to steal and the same serial seconds to wait through. The same section does not throttle weak scaling, provided each added processor brings new parallel work and the serial seconds stay a modest fraction of the fixed time window. “Serial fraction” is only a meaningful brake once the denominator — fixed original work, or work that grew with \(P\) — is stated. Gustafson’s contribution is to make that denominator explicit by measuring \(\alpha\) where the large run actually happens.
