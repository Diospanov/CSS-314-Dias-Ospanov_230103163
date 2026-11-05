# Task 14 — Isoefficiency of a Gustafson Workload

## The isoefficiency relation

Kumar and Grama measure how fast the problem size must grow with \(P\) if efficiency is to stay constant. Write \(W\) for the operation count of the problem actually solved (the one-processor work \(T_1\)), \(T_P\) for the parallel wall time, and

\[
T_o(W, P) = P\,T_P - W
\]

for the overhead: processor-seconds spent by the parallel machine beyond the useful work. Efficiency is

\[
E = \frac{W}{P\,T_P} = \frac{W}{W + T_o} = \frac{1}{1 + T_o/W}.
\]

Holding \(E\) at a chosen constant \(E_0 \in (0,1)\) forces the useful work to track the overhead:

\[
W = \frac{E_0}{1-E_0}\, T_o(W, P) = K\, T_o, \qquad K = \frac{E_0}{1-E_0}.
\]

The solution \(W(P)\) of this relation is the isoefficiency function. A linear \(W(P) = \Theta(P)\) is optimal in the leading term, because \(P\) processors need \(\Omega(P)\) work merely to have a constant amount each.

## Overhead of a Gustafson-compliant program

Take a program that meets the classical Gustafson hypotheses: serial compute \(\sigma\) seconds, parallel compute \(w\) seconds per processor, both independent of \(P\), perfect balance, and no communication term. Then

\[
T_P = \sigma + w, \qquad W = T_1 = \sigma + P w,
\]

and the serial time-fraction on the parallel run is the constant

\[
\alpha = \frac{\sigma}{\sigma + w}.
\]

The overhead is exactly the serial section sitting on the processors that do not execute it:

\begin{align*}
T_o
&= P(\sigma + w) - (\sigma + P w) \\
&= P\sigma + P w - \sigma - P w \\
&= \sigma(P - 1).
\end{align*}

So \(T_o = \Theta(P)\). Overhead linear in \(P\) is the signature of a serial section of constant length.

## The isoefficiency function is linear

Substitute \(T_o = \sigma(P-1)\) into the isoefficiency relation:

\[
W = K \sigma (P-1) = \Theta(P).
\]

This \(W\) is achievable inside the model. The Gustafson workload already supplies

\[
W(P) = \sigma + P w = \Theta(P)
\]

with \(w\) a constant. Its efficiency is the function derived in Task 04,

\[
E(P) = 1 - \alpha + \frac{\alpha}{P},
\]

which decreases toward the floor \(1-\alpha\) and never crosses it. Therefore:

1. For every target \(E_0 \le 1-\alpha\), the constant local work \(w\) already keeps \(E(P) \ge E_0\) for all sufficiently large \(P\), at total work \(\Theta(P)\). The isoefficiency function is \(W(P) = \Theta(P)\).
2. For a target \(E_0\) with \(1-\alpha < E_0 < 1\), a larger but still constant local work is enough. Solve \(E \ge E_0\):

\[
\frac{\sigma/P + w}{\sigma + w} \ge E_0
\implies
w \ge \sigma \cdot \frac{E_0 - 1/P}{1-E_0}.
\]

The right-hand side tends to the constant \(\sigma E_0/(1-E_0)\). Choose \(w\) at least that large. Then \(W = \sigma + P w\) is still \(\Theta(P)\), and \(E(P)\) tends to \(w/(\sigma+w) \ge E_0\). Raising the efficiency target raises the constant hidden in \(\Theta(P)\). It does not raise the degree of the isoefficiency function.

**Conclusion.** A program that is Gustafson-compliant, with constant serial time and constant local parallel work, has linear isoefficiency \(W(P) = \Theta(P)\). That is the optimal rate. Equivalently, the overhead function \(T_o = \sigma(P-1)\) is linear, and isoefficiency has the same order as the overhead.

## Critique: the linear result is only as strong as \(T_o = \Theta(P)\)

Linear isoefficiency is not a gift of the word “weak scaling.” It is the isoefficiency of one particular overhead, the idle time of a constant-length serial section. Real solvers add further terms (Task 12 and Task 13):

\[
T_o(P) = \sigma(P-1) + P\,C(P).
\]

If \(C(P) = \beta \log P\) is a reduction latency paid by every processor, then \(T_o = \Theta(P \log P)\) and the relation \(W = K T_o\) becomes

\[
W(P) = \Theta(P \log P).
\]

Local work per processor must then grow, slowly, like \(\log P\). A constant \(\alpha\) no longer holds, and classical Gustafson efficiency no longer has a floor at \(1-\alpha\). If the surface term \(C(P) = \gamma P^{1/2}\) dominates, isoefficiency rises to \(\Theta(P^{3/2})\) and weak scaling at constant local size loses efficiency steadily.

The same promotion of degree appears when the algorithm itself lengthens, as in unpreconditioned CG (Task 13): the iteration count is a growing factor in front of an otherwise linear workload, and \(W\) must grow faster than linear to hold efficiency. Isoefficiency is the sharper question. Gustafson’s formula is the answer in the special case where the only overhead is a serial section of constant duration. As soon as overhead per processor grows, the isoefficiency function leaves the linear regime and the constant-\(\alpha\) model stops being the scaling law of the program.
