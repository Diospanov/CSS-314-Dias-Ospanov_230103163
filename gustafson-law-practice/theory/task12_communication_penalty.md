# Task 12 — Gustafson’s Law with a Communication Term

## The assumption that has to be relaxed

The base formula treats the serial fraction \(\alpha\) as a constant. That is accurate when the time that fails to speed up is a local setup, a fixed I/O stage, or any other cost that does not grow as processors are added. In a distributed-memory run the cost that usually grows is communication: a collective whose latency follows the diameter of the network, or a halo exchange whose surface grows as the processor grid grows.

Two standard shapes cover the cases named in the task.

- Tree or hypercube collectives (broadcast, reduction): \(C(P) = \beta \log_2 P\).
- A two-dimensional processor mesh whose halo cost follows the linear size of the mesh: \(C(P) = \gamma \, P^{1/2}\).

\(\beta > 0\) and \(\gamma > 0\) are times measured in the same unit as the compute. Both are increasing, and both go to infinity, slowly or not, as \(P \to \infty\).

## Extended model

Keep the compute split of the classical model. On \(P\) processors, with communication ignored, serial compute occupies a fraction \(\alpha\) and parallel compute occupies \(1-\alpha\), and those two already sum to one time unit. Communication is extra wall time \(C(P)\) that a single processor does not pay, because a single processor does not exchange halos or run a collective.

\[
T_P = 1 + C(P), \qquad T_1 = \alpha + (1-\alpha)\,P.
\]

\(T_1\) contains only compute. The scaled speedup, still defined as one-processor compute time over parallel wall time, is

\[
S_C(P) = \frac{T_1}{T_P} = \frac{\alpha + (1-\alpha)\,P}{1 + C(P)}.
\]

Efficiency is

\[
E_C(P) = \frac{S_C(P)}{P} = \frac{\alpha/P + (1-\alpha)}{1 + C(P)}.
\]

When \(C(P) = 0\) both expressions reduce to \(S(P) = \alpha + (1-\alpha)P\) and \(E(P) = 1 - \alpha + \alpha/P\).

## Limit once communication grows

If \(C(P) \to \infty\), the denominator of \(E_C\) is unbounded while the numerator tends to \(1-\alpha\). Therefore

\[
\lim_{P \to \infty} E_C(P) = 0
\]

for both \(C(P) = \beta \log_2 P\) and \(C(P) = \gamma P^{1/2}\), any \(\beta, \gamma > 0\). The positive floor \(1-\alpha\) of classical Gustafson efficiency was an artifact of assuming that non-parallel time stays constant. A growing communication term removes the floor. The removal is only logarithmic for a tree collective, so efficiency falls very slowly, and it is algebraic for a \(\sqrt{P}\) surface term.

## Worked values

Take \(\alpha = 0.04\) and a collective \(C(P) = 0.01 \log_2 P\) (one hundredth of the compute window per doubling of the machine).

| \(P\) | \(C(P)\) | \(S\) classical | \(S_C\) | \(E_C\) |
|---|---|---|---|---|
| 16 | 0.040 | 15.40 | 14.808 | 0.9255 |
| 1024 | 0.100 | 983.08 | 893.709 | 0.8728 |
| 65536 | 0.160 | 62914.60 | 54236.72 | 0.8276 |

The same \(\alpha\) with a heavier surface term \(C(P) = 0.001\,P^{1/2}\):

| \(P\) | \(C(P)\) | \(S_C\) | \(E_C\) |
|---|---|---|---|
| 1024 | 0.032 | 952.597 | 0.9303 |
| 65536 | 0.256 | 50091.24 | 0.7643 |

Classical Gustafson efficiency would already be \(0.960\) at these sizes and would stay there. The communication term is the entire additional loss.

## Why a renormalized \(\alpha(P)\) is a different model

It is tempting to fold communication into the serial fraction,

\[
\alpha_{\text{obs}}(P) = \frac{\alpha + C(P)}{1 + C(P)},
\]

and then to drop \(\alpha_{\text{obs}}\) into \(P - \alpha_{\text{obs}}(P-1)\). That substitution answers a different question. It treats \(C(P)\) as work a single processor would also perform, because the identity \(S = s + pP\) puts every “serial” second into \(T_1\) as well as into \(T_P\). For communication a single processor does not perform, the consistent numerator stays \(\alpha + (1-\alpha)P\), and the consistent formula is \(S_C\) above.

A numerical separation at \(P = 1024\), \(\alpha = 0.04\), \(C = 0.10\):

\[
S_C = \frac{983.08}{1.10} = 893.71,
\]

\[
P - \alpha_{\text{obs}}(P-1) = 1024 - \frac{0.14}{1.10}\cdot 1023 = 893.80.
\]

These particular numbers land close, but they are not the same function. The form to carry forward is the ratio of times \(T_1/T_P\), with \(C(P)\) placed only in the denominator when the uniprocessor does not communicate, and in both numerator and denominator when the extra term is truly serial compute that every run pays.

## Design reading

Classical Gustafson remains the model for the compute split. Real distributed runs need an explicit \(C(P)\) whose shape matches the collective or the surface exchange. The modified law

\[
S_C(P) = \frac{\alpha + (1-\alpha)P}{1 + \beta \log_2 P}
\quad\text{or}\quad
S_C(P) = \frac{\alpha + (1-\alpha)P}{1 + \gamma P^{1/2}}
\]

is the extension. Use the logarithmic form for reduction-dominated codes and the square-root form for 2D nearest-neighbor halos on a growing processor mesh. Either form is enough to stop efficiency from leveling at \(1-\alpha\).
