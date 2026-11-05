# Task 10 — Memory Ceiling for a 3D Grid

## What weak scaling does to memory

Under pure weak scaling the work grows in proportion to the processor count,

\[
W(P) = P \cdot W(1),
\]

and the assignment states that the aggregate memory footprint does the same,

\[
M(P) = c \cdot P.
\]

The constant \(c = M(P)/P\) is the memory per node. It does not grow with \(P\). The per-node cap says

\[
c \le 32\ \text{GB} = 32 \times 2^{30}\ \text{bytes} = 34{,}359{,}738{,}368\ \text{bytes}.
\]

At the cap the largest legal footprints are

| Nodes \(P\) | Aggregate ceiling \(M(P) = 32P\) GB | Aggregate bytes |
|---|---|---|
| 64 | 2,048 GB (2 TB) | \(64 \times 2^{30} \times 32 = 2^{6} \cdot 2^{5} \cdot 2^{30} = 2^{41}\) |
| 512 | 16,384 GB (16 TB) | \(512 \times 32 \times 2^{30} = 2^{9} \cdot 2^{5} \cdot 2^{30} = 2^{44}\) |

## From bytes to a 3D dimension

A 3D grid stores \(\Theta(N^3)\) unknowns. Write the footprint as

\[
M = \kappa N^3,
\]

where \(\kappa\) is the bytes per grid point, including every array that scales with the mesh (solution, right-hand side, a halo layer counted into \(\kappa\), and so on). Solving for the dimension,

\[
N(P) = \left(\frac{M(P)}{\kappa}\right)^{1/3} = \left(\frac{c\,P}{\kappa}\right)^{1/3} = N_1 \cdot P^{1/3},
\]

with \(N_1 = (c/\kappa)^{1/3}\) the largest cube that fits on one node. At the 32 GB cap and at processor counts that are perfect cubes,

\[
64^{1/3} = 4, \qquad 512^{1/3} = 8,
\]

so the maximum dimensions are exactly four and eight times the one-node cube:

\[
N_{\max}(64) = 4\,N_1, \qquad N_{\max}(512) = 8\,N_1, \qquad N_1 = \left(\frac{32 \times 2^{30}}{\kappa}\right)^{1/3}.
\]

The cube root, rather than a linear factor of 64 or 512, is the geometric content of \(M \propto N^3\) together with \(M \propto P\). Eight times more nodes multiply the volume by eight and the linear dimension by two. From 64 nodes to 512 nodes the volume grows by \(512/64 = 8\) and the dimension grows by \(8/4 = 2\):

\[
\frac{N_{\max}(512)}{N_{\max}(64)} = 2.
\]

Wall-clock time stays constant under the Gustafson hypothesis even though the global grid goes from \(4N_1\) to \(8N_1\), because each node’s local cube stays \(N_1\) on a side. Local memory stays 32 GB. Aggregate memory grows from 2 TB to 16 TB.

## Integer dimensions for an 8-byte unknown

The formula above is the general ceiling. A concrete \(\kappa\) is required before \(N\) becomes an integer. Take one IEEE-754 double per grid point, \(\kappa = 8\) bytes, as an illustrative minimum (a real solver with several fields would use a larger \(\kappa\) and a smaller \(N\)).

Cells per node:

\[
\frac{32 \times 2^{30}}{8} = 2^{32} = 4{,}294{,}967{,}296.
\]

\[
N_1 = \lfloor (2^{32})^{1/3} \rfloor.
\]

Now \((2^{32})^{1/3} = 1625.498677\ldots\), and

\[
1625^3 = 4{,}291{,}015{,}625 \le 2^{32}, \qquad 1626^3 = 4{,}298{,}942{,}376 > 2^{32}.
\]

So \(N_1 = 1625\). Scaling by the exact cube roots of the node counts, the aggregate cell caps are \(64 \cdot 2^{32} = 2^{38}\) and \(512 \cdot 2^{32} = 2^{41}\):

\[
(2^{38})^{1/3} = 6501.994708\ldots, \qquad (2^{41})^{1/3} = 13003.989417\ldots
\]

The greatest integers whose cubes fit are

\[
N_{\max}(64) = 6501, \qquad N_{\max}(512) = 13003.
\]

These sit one below the real multiples \(4 \times 1625.4987\ldots\) and \(8 \times 1625.4987\ldots\) because \(1625\) itself sits below \((2^{32})^{1/3}\). Using \(4 \times 1625 = 6500\) and \(8 \times 1625 = 13000\) is safe and only one or three cells short of the byte-exact floor. Either pair is a 32 GB-per-node grid of double-precision values; neither grid increases the memory per node when \(P\) goes from 64 to 512.

## What this forbids

A strong-scaling habit of growing \(N\) faster than \(P^{1/3}\) at fixed \(P\), or of copying the global grid onto every node, breaks the cap. Aggregate memory linear in \(P\) and a cubic grid together allow only \(N = \Theta(P^{1/3})\). That is the most grid this memory system can hold while leaving every node inside 32 GB, and it is also the growth rate that holds the local problem, and therefore the local compute time, constant.
