# Task 15 — Energy of a Fixed-Time Scaled Workload

## Power model

Processor count is \(P\). To keep that symbol free, write power with subscripts and treat each as a constant of the node:

- \(\mathcal{P}_{\text{idle}}\): power a node draws while powered and not issuing the parallel or serial arithmetic.
- \(\mathcal{P}_{\text{active}}\): extra power a node draws while it is the one executing useful work.

Every node is powered for the whole run, so idle power is always present. Active power is added only on nodes that are computing.

The workload follows Gustafson’s split. Wall-clock time \(T\) is the same for the one-node run of the unit problem and for the \(P\)-node run of the scaled problem. Of that window, a fraction \(\alpha\) is serial (one node computing, the other \(P-1\) nodes only idling) and a fraction \(1-\alpha\) is parallel (all \(P\) nodes computing). The scaled speedup is the usual

\[
S(P) = \alpha + (1-\alpha)P.
\]

\(S(P)\) is also the factor by which the scaled run’s useful work exceeds the unit problem, because \(T_1 = S(P)\,T\) is the one-processor time of the scaled work and \(T\) is the one-processor time of the unit problem.

## Energy at identical wall-clock time

**One node, unit problem, time \(T\).** That node computes for the whole window:

\[
E(1) = \bigl(\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\bigr)\, T.
\]

**\(P\) nodes, scaled problem, same time \(T\).** Idle energy is \(\mathcal{P}_{\text{idle}}\) on every node for time \(T\). Dynamic energy equals \(\mathcal{P}_{\text{active}}\) times the processor-seconds of useful work. Those processor-seconds are one node for \(\alpha T\) plus \(P\) nodes for \((1-\alpha)T\):

\[
\alpha T + (1-\alpha) P T = S(P)\, T.
\]

Hence

\[
E(P) = P\,\mathcal{P}_{\text{idle}}\,T + \mathcal{P}_{\text{active}}\,S(P)\,T
= T\Bigl(P\,\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\bigl[\alpha + (1-\alpha)P\bigr]\Bigr).
\]

The ratio of energies at fixed wall time is

\[
\frac{E(P)}{E(1)} = \frac{P\,\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\,S(P)}{\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}}.
\]

When dynamic power dominates, this is about \(S(P)\), which is about \((1-\alpha)P\). The large machine consumes roughly \(P\) times the energy and returns roughly \(S(P)\) times the work in the same deadline. Energy per unit work,

\[
e(P) = \frac{E(P)}{S(P)} = T\left(\mathcal{P}_{\text{active}} + \mathcal{P}_{\text{idle}}\frac{P}{S(P)}\right),
\qquad
e(1) = T\bigl(\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\bigr),
\]

stays bounded as \(P\) grows, because \(P/S(P) \to 1/(1-\alpha)\). Fixed-time scaling therefore has a finite energy cost per unit of science. The cost does not improve with \(P\) once \(P\) is large; it levels off at

\[
\lim_{P \to \infty} e(P) = T\left(\mathcal{P}_{\text{active}} + \frac{\mathcal{P}_{\text{idle}}}{1-\alpha}\right).
\]

A nonzero serial fraction raises the idle term. During the serial interval the other nodes burn \(\mathcal{P}_{\text{idle}}\) and add no work, so the asymptotic energy per work is strictly worse than the \(\alpha = 0\) value \(T(\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}})\).

## Same scaled work, one node versus \(P\) nodes

The comparison above gives both runs the same deadline and different amounts of work. The other natural comparison gives both runs the scaled work and lets the one-node run take the time it needs, \(S(P)\,T\):

\[
E_{\text{serial, scaled}} = \bigl(\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\bigr)\, S(P)\, T.
\]

Subtracting, the dynamic parts match exactly: both equal \(\mathcal{P}_{\text{active}}\,S(P)\,T\), because both perform the same useful processor-seconds. The entire difference is idle energy.

\[
\frac{E(P)}{E_{\text{serial, scaled}}}
= \frac{P\,\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\,S(P)}{S(P)\bigl(\mathcal{P}_{\text{idle}} + \mathcal{P}_{\text{active}}\bigr)}.
\]

Idle energy on the parallel machine is \(P\,\mathcal{P}_{\text{idle}}\,T\). Idle energy on the long one-node run is \(\mathcal{P}_{\text{idle}}\,S(P)\,T\). Their ratio is

\[
\frac{P}{S(P)} = \frac{P}{\alpha + (1-\alpha)P} \to \frac{1}{1-\alpha}.
\]

For \(\alpha = 0\), \(S(P) = P\) and the two idle energies are equal: \(P\) nodes for time \(T\), or one node for time \(PT\). For \(\alpha > 0\), \(S(P) < P\), so the parallel machine pays more idle energy than the long single-node run. The extra is the \(P-1\) nodes powered through the serial fraction, together with the fact that the single node does not have to run for a full \(P\,T\).

If \(\mathcal{P}_{\text{idle}} \to 0\), the ratio of total energies tends to 1. With no idle draw, weak scaling does not change the energy of a given body of work; it only shortens the clock from \(S(P)\,T\) to \(T\).

## Numerical illustration

Assumptions, chosen so the arithmetic is easy to check: \(\alpha = 0.04\), \(P = 1024\), \(T = 1\) hour, \(\mathcal{P}_{\text{idle}} = 20\,\text{W}\), \(\mathcal{P}_{\text{active}} = 80\,\text{W}\).

\[
S(1024) = 0.04 + 0.96 \cdot 1024 = 983.08.
\]

\[
E(1) = (20 + 80) \cdot 1 = 100\ \text{Wh}.
\]

\[
E(1024) = 1024 \cdot 20 + 80 \cdot 983.08 = 20480 + 78646.4 = 99126.4\ \text{Wh}.
\]

Energy per unit work falls from \(100\) Wh on the unit problem to \(99126.4 / 983.08 = 100.83\) Wh on the scaled run. The same scaled work on one node would cost \(100 \times 983.08 = 98308\) Wh and would take \(983.08\) hours. The 1,024-node run costs \(0.83\%\) more energy and finishes in one hour. Almost all of that \(0.83\%\) is idle power during the serial \(4\%\) of the window: \(P/S = 1024/983.08 = 1.0416\), and the idle-energy ratio between the parallel run and the long serial run is that same \(1.0416\).

## Design reading

Under Gustafson scaling, energy to the deadline grows essentially with \(P\), and energy per unit work tends to a constant fixed by \(\mathcal{P}_{\text{active}}\), \(\mathcal{P}_{\text{idle}}\), and \(\alpha\). Reducing \(\alpha\) saves energy per work even when it barely changes the already-large speedup, because it shortens the interval in which \(P-1\) nodes are powered and idle. Reducing idle power saves energy in proportion to \(P\,T\) regardless of how parallel the arithmetic is.
