# Task 08 — Amdahl and Gustafson at \(s = \alpha = 0.08\), \(P = 128\)

The same numerical fraction \(0.08\) is fed to both laws. In Amdahl’s formula it is the serial share of a fixed workload. In Gustafson’s formula it is the serial share of time on the 128-processor run. The arithmetic below is exact; the two predictions are far apart because those two readings are different experiments (Task 03).

## Amdahl, fixed workload

\[
S_{\text{Amdahl}}(128)
= \frac{1}{0.08 + 0.92/128}.
\]

The denominator is a single fraction:

\[
0.08 + \frac{0.92}{128} = \frac{0.08 \cdot 128 + 0.92}{128} = \frac{10.24 + 0.92}{128} = \frac{11.16}{128}.
\]

Therefore

\[
S_{\text{Amdahl}}(128) = \frac{128}{11.16} = \frac{12800}{1116} = \frac{3200}{279} = 11.469534050179\ldots
\]

Efficiency is \(S/P = 3200/(279 \cdot 128) = 25/279 \approx 0.0896\). Only about \(9\%\) of the 128 processors are doing useful work under the fixed-size reading. The asymptotic ceiling for this \(s\) is \(1/0.08 = 12.5\), so at 128 processors the run is already within \(9\%\) of the best speedup a fixed problem of this serial fraction can ever have.

## Gustafson, fixed time

\[
S_{\text{Gustafson}}(128)
= 128 - 0.08 \cdot 127
= 128 - 10.16
= 117.84.
\]

Equivalently, \(S = 0.08 + 0.92 \cdot 128 = 0.08 + 117.76 = 117.84\).

Efficiency is

\[
E = \frac{117.84}{128} = 0.920625 = 1 - 0.08 + \frac{0.08}{128},
\]

just above the floor \(0.92\).

## Discrepancy

\[
S_{\text{Gustafson}} - S_{\text{Amdahl}} = 117.84 - \frac{3200}{279} = 106.370465949821\ldots
\]

\[
\frac{S_{\text{Gustafson}}}{S_{\text{Amdahl}}} = 117.84 \cdot \frac{279}{3200} = 10.274175.
\]

The Gustafson prediction exceeds the Amdahl prediction by a factor of \(10.274175\). As a percentage of the Amdahl value,

\[
\frac{S_{\text{Gustafson}} - S_{\text{Amdahl}}}{S_{\text{Amdahl}}} \times 100\% = 927.4175\%.
\]

## Why the gap grows with \(P\)

Hold \(s = \alpha = 0.08\) fixed and vary \(P\).

\[
S_{\text{Amdahl}}(P) = \frac{1}{0.08 + 0.92/P} \to \frac{1}{0.08} = 12.5,
\]

\[
S_{\text{Gustafson}}(P) = 0.08 + 0.92\,P \to \infty,
\]

so the ratio \(S_{\text{Gustafson}}/S_{\text{Amdahl}}\) tends to infinity. At \(P = 128\) the fixed-size curve has nearly finished rising (11.47 against a ceiling of 12.5), while the fixed-time curve is still collecting \(0.92\) speedup points per added processor and has barely felt the \(8\%\) serial tax (\(E = 92.06\%\)).

They diverge because the fraction \(0.08\) is applied to different denominators. Amdahl keeps the parallel work in the numerator fixed, so at 128 processors that work occupies only \(0.92/128 = 0.0071875\) of the original time unit and the serial \(0.08\) dominates the denominator \(0.0871875\). Gustafson keeps the parallel *time* fixed at \(0.92\) of the window, multiplies the work in that window by 128, and only then compares with one processor. The serial section is \(8\%\) of the time on both pictures only if one ignores that “the time” refers to a different run. On the scaled run it is \(8\%\) of one window. On the fixed run it is \(8\%\) of the original work and about \(92\%\) of the 128-processor wall time.
