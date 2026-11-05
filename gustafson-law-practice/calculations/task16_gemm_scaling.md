# Task 16 — Dense Matrix Multiplication, Fixed Parallel Time

## Complexity

Compute \(C = AB\) with \(A,B,C\) each \(N \times N\). The arithmetic is

\[
W(N) = \Theta(N^3)
\]

(classically \(2N^3\) floating-point operations for the \(ijk\) form). The three matrices occupy

\[
M(N) = \Theta(N^2)
\]

words. On \(P\) processors with a perfect split of the arithmetic and no communication term,

\[
T_P(N) = \Theta\left(\frac{N^3}{P}\right).
\]

## Dimension required by Gustafson’s hypothesis

Fixed parallel time means \(T_P(N) = T_P(N_0)\) when the one-processor problem of order \(N_0\) is compared with the \(P\)-processor problem of order \(N\). Canceling the hidden constant,

\[
\frac{N^3}{P} = N_0^3 \implies N^3 = N_0^3 \, P \implies N(P) = N_0 \, P^{1/3}.
\]

Equivalently, the work itself must satisfy \(W(P) = P\,W(1)\), and because \(W \propto N^3\) the order scales as the cube root of that work ratio. This is the unique exponent that holds the floating-point work per processor constant:

\[
\frac{W(N(P))}{P} = \Theta(N_0^3) = \Theta\bigl(W(N_0)\bigr).
\]

## What memory does at that exponent

Total memory at the fixed-time dimension is

\[
M\bigl(N(P)\bigr) = \Theta\bigl(N(P)^2\bigr) = \Theta\bigl(N_0^2 \, P^{2/3}\bigr),
\]

so aggregate memory grows, but slower than the processor count. Memory *per processor* falls:

\[
\frac{M}{P} = \Theta\bigl(P^{2/3 - 1}\bigr) = \Theta\bigl(P^{-1/3}\bigr).
\]

A GEMM whose *runtime* is held constant therefore does not fill a constant fraction of each node’s memory. The scaling that does fill memory is the Sun–Ni choice \(N \propto P^{1/2}\) (because \(N^2 \propto P\)), and that choice makes \(T_P = \Theta(N^3/P) = \Theta(P^{1/2})\) grow. Fixed time and full-memory are different GEMM experiments. This task is the fixed-time one.

## Scaling targets

\(N/N_0 = P^{1/3}\). Rows with integer cube roots are exact. The others are reported to six decimals.

| \(P\) | \(N/N_0 = P^{1/3}\) | Work ratio \(N^3/N_0^3 = P\) | Memory ratio \(N^2/N_0^2 = P^{2/3}\) | Memory per processor, relative to \(P=1\) |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 |
| 8 | 2 | 8 | 4 | 0.500000 |
| 27 | 3 | 27 | 9 | 0.333333 |
| 64 | 4 | 64 | 16 | 0.250000 |
| 512 | 8 | 512 | 64 | 0.125000 |
| 1024 | 10.079368 | 1024 | 101.593667 | 0.099213 |
| 4096 | 16 | 4096 | 256 | 0.062500 |
| 16384 | 25.398417 | 16384 | 645.079578 | 0.039373 |

Reading the \(P = 4096\) row: the matrix order is \(16\) times the one-processor order, the arithmetic is \(4{,}096\) times larger, the three matrices together occupy \(256\) times more memory, and each processor holds \(1/16\) as many words as the original one-processor problem while performing the same number of flops as that original problem. That last clause is the Gustafson condition. Scaled speedup of the arithmetic, with a serial fraction \(\alpha\) measured on the parallel run, is then the ordinary \(S(P) = P - \alpha(P-1)\), because the derivation in Task 02 never needed the work to be linear in \(N\) — it needed the parallel *time* to be the constant \(p\), which the relation \(N \propto P^{1/3}\) enforces.
