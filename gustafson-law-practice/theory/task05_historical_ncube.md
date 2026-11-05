# Task 05 — The nCUBE Result and Amdahl’s Ceiling

## The experiment Gustafson, Montry, and Benner reported

In 1988 John L. Gustafson, Gary R. Montry, and Robert E. Benner, working at Sandia National Laboratories, published parallel methods for a 1,024-processor nCUBE 10 hypercube and, in a companion note, the scaled-speedup argument now called Gustafson’s law.

- J. L. Gustafson, G. R. Montry, and R. E. Benner, “Development of Parallel Methods for a 1024-Processor Hypercube,” *SIAM Journal on Scientific and Statistical Computing* 9(4), 1988.
- J. L. Gustafson, “Reevaluating Amdahl’s Law,” *Communications of the ACM* 31(5), 1988, pp. 532–533.

The machine was a 1,024-node nCUBE 10. Each node was a modest microprocessor with its own local memory. Nodes communicated by messages on a 10-dimensional hypercube. The codes were production-style scientific applications (explicit wave-mechanics and fluid calculations, and structural finite-element work), not a single synthetic kernel.

The operational choice was fixed-time scaling. Rather than take a problem sized for one node and spread it thinly across 1,024 nodes, they enlarged the physical problem so the full machine stayed busy for a run of practical length. On those enlarged problems the portion of wall time that remained serial was a fraction of one percent. The figure cited throughout later discussion, and the figure used in this assignment, is a serial fraction of \(0.4\%\). Measured speedups of the scaled problems against one processor exceeded \(1{,}000\times\) on 1,024 processors.

## Why that looked impossible under Amdahl’s law

Interpret \(0.4\%\) as an Amdahl serial fraction of a fixed problem:

\[
s = 0.004, \qquad \lim_{P \to \infty} S_{\text{Amdahl}}(P) = \frac{1}{s} = 250.
\]

At exactly \(P = 1024\),

\[
S_{\text{Amdahl}}(1024) = \frac{1}{0.004 + 0.996/1024} = \frac{1}{0.004 + 0.00097265625} = \frac{1}{0.00497265625} \approx 201.10.
\]

A measured speedup above \(1{,}000\) is several times this value and four times the asymptotic ceiling. No rearrangement of a fixed-size Amdahl model with \(s = 0.004\) produces a speedup of \(1{,}000\). The ceiling really is \(250\). The observation really was above \(1{,}000\). One of the identifications in the comparison had to be wrong.

## How problem expansion removes the ceiling

The \(0.4\%\) was the serial share of time on the *1,024-processor scaled run*, which is Gustafson’s \(\alpha\), not Amdahl’s \(s\) for a one-node problem. Task 02 then gives

\begin{align*}
S(1024)
&= 1024 - 0.004 \cdot (1024 - 1) \\
&= 1024 - 0.004 \cdot 1023 \\
&= 1024 - 4.092 \\
&= 1019.908.
\end{align*}

A result “above \(1{,}000\times\)” sits on this prediction. Efficiency is

\[
E(1024) = \frac{1019.908}{1024} = 0.996005859375,
\]

about \(99.6\%\), consistent with a machine that is serial for only \(0.4\%\) of a fixed time window.

The workload behind that speedup is not the workload behind the ceiling of \(250\). One processor needs \(1019.908\) time units to repeat what 1,024 processors did in one time unit. The serial piece is \(0.004\) of the parallel time unit, which is only

\[
\frac{0.004}{1019.908} \approx 0.000392\%
\]

of the scaled work. Amdahl’s formula, fed with *that* serial share of the scaled work, would have predicted a ceiling near \(1/0.00000392 \approx 255{,}000\), not \(250\). The 1,024-processor run never approached such a ceiling.

Problem expansion is what creates the gap. Each node of the nCUBE received a full local subdomain, a full local particle set, or a full local element block, sized so the node’s arithmetic remained large compared with startup, I/O, and the hypercube exchanges of that generation. Growing the subdomains with the machine grew the parallel work in the numerator of \(T_1 = s + pP\) while the measured serial time in the denominator stayed near \(0.4\%\) of the run. The ratio crossed \(1{,}000\). The fixed-size ceiling never applied to that ratio, because the size was not fixed.

## What the episode does and does not retire

Amdahl’s law remains the correct account of strong scaling a frozen input: with \(s = 0.004\) you still cannot make *that* input faster than \(250\times\), and at 1,024 processors you should expect about \(201\times\) if the parallel region scales perfectly. The nCUBE runs did not violate that statement. They answered a different question — how much more science the same wall-clock budget can contain — and Gustafson’s formula is the one that matches the answer.
