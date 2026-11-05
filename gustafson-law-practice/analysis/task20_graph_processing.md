# Task 20 — Why Weak Scaling Is Hard for BFS and PageRank

Gustafson’s formula is a statement about a stable split of a fixed wall-clock window into a serial piece and a parallel piece, with the parallel piece carrying \(\Theta(P)\) useful work. Dense linear algebra earns that split. A sparse matrix or a well-partitioned stencil touches its neighbors through a surface that grows more slowly than its volume, the memory stream is regular enough to saturate a cache, and the iteration count of a direct kernel does not depend on the values. Breadth-first search and PageRank on power-law graphs have none of those structural gifts. Weak scaling them is difficult because enlarging the graph and adding processors both change the split that \(\alpha\) is supposed to name.

## The graph the extra processors actually receive

A power-law (scale-free) degree sequence puts a small number of hubs next to a large number of leaves. The average degree can stay constant as the vertex count \(N\) grows, which looks like a constant amount of edge data per vertex and therefore like a legal weak-scaling family \(N \propto P\). The *work* does not follow the average. In BFS the work of a level is the number of edges out of the current frontier. One hub pulled into the frontier creates a level whose edge list is a finite fraction of the whole graph, and that level is hard to split evenly: many of those edges land on vertices already owned by other ranks, or they all have to be filtered through a small set of high-degree adjacency arrays. In PageRank the same hubs dominate the sparse matrix-vector product. A partition that balances vertices leaves one rank holding a hub and doing many times the arithmetic of a rank that holds leaves. A partition that balances edges cuts the hub’s adjacency and pays the cut in messages.

Either way, “\(N/P\) vertices per rank” is not “equal time per rank.” Gustafson’s step from a parallel interval of length \(p\) to one-processor work \(pP\) assumes the \(P\) ranks were all busy during that interval. On a power-law graph a large share of them are waiting on the rank that owns the current hub. The idle time grows when the graph grows, because a larger draw from a power-law distribution produces a more extreme maximum degree. \(\alpha\) measured on a small crawl is not \(\alpha\) on a crawl \(P\) times bigger.

## BFS has a critical path the extra vertices make longer or at least not shorter

Level-synchronous BFS advances one frontier at a time, with a global barrier or an equivalent all-to-all of the next frontier between levels. The number of those rounds is the graph distance from the source to the farthest reached vertex. Adding processors does not reduce the number of rounds below the diameter of the graph, and growing a graph to feed those processors does not drive the diameter to zero. For many random graph families the diameter grows, slowly, with \(N\). Each round also moves an unpredictable volume of frontier identifiers, so the time of a round is data-dependent.

The wall time of a search is therefore

\[
T_{\text{BFS}} = \sum_{\ell=1}^{L(N)} \bigl(T_{\text{local}}(\ell) + T_{\text{imbalance}}(\ell) + T_{\text{sync}}(P)\bigr),
\]

where \(L(N)\) is the number of levels. Weak scaling asks this sum to stay constant while \(N \propto P\). \(T_{\text{sync}}\) is at least a reduction or a barrier and grows like the collective in Task 12. \(T_{\text{imbalance}}\) is the wait for the slowest rank, which power-law hubs set. \(L(N)\) is a property of the input, not a knob the programmer sets to \(O(1)\). Dense GEMM has no analogue of \(L(N)\): its loop nest is a function of the dimensions the scaling law already chose. BFS has a serial chain of frontiers whose length the scaling law does not control. That chain is why a measured speedup refuses to sit on \(S(P) = P - \alpha(P-1)\) with a single \(\alpha\) taken from a smaller graph.

## PageRank adds a global reduction to every iteration

PageRank (and any label-propagation cousin) applies a sparse matvec and then normalizes or damps with a global sum, once per iteration. The matvec is the irregular memory stream: edge traversals jump through the neighbor array, cache lines die after one use, and arithmetic intensity is a few flops per edge. The normalization is an all-reduce. On a stencil, intensity and surface-to-volume both improve or at least hold as the local box grows (Task 17). On a graph, growing the local vertex set grows the edge cut of a power-law partition in a way that does not follow \(n^2\) against \(n^3\). There is no geometric surface. Community structure and hubs decide the cut, and a larger sample of a power-law graph often cuts *worse* relative to local work, not better.

The iteration count of PageRank to a fixed residual is another hidden serial multiplier. It depends on the spectral gap of the damped transition matrix. Nothing in \(N \propto P\) guarantees that gap stays constant from one crawl to a crawl \(P\) times larger. A Gustafson prediction fit on 16 ranks at one graph size does not travel to 1,024 ranks on a different graph of proportional size, because the input family has changed the number of useful iterations and the balance of each iteration.

## Contrast with dense linear algebra

A dense GEMM or a regular stencil weak-scales, when it does, for reasons that are all absent here.

- The work per byte is high (GEMM) or the halo is a geometric surface of a compact subdomain (stencil). Graph kernels are memory-latency bound and their “surface” is an edge cut.
- The owner of each output element is known before the run, and every rank’s loop has the same trip count. BFS frontiers and power-law rows do not.
- The number of outer iterations is chosen by the user (a fixed number of stencil steps) or is stable under the scaling (a direct factorization’s panel count, itself a different and known function of \(N\)). BFS levels and PageRank convergence are data-dependent.
- Communication volume is a formula in \(N\) and \(P\). Communication volume in a graph code is an output of the partitioner and the frontier, and both move when the problem is enlarged.

Gustafson’s law can still be *evaluated* on a graph code: measure \(T_P\), measure how long one processor takes on that same large graph, and divide. The quotient is a number. What fails is the predictive use of the law, the claim that a single \(\alpha\) and the rule \(N \propto P\) will hold the quotient near \((1-\alpha)P\) at the next machine size. The hypotheses behind that claim — constant local time, constant balance, a serial fraction that does not itself depend on \(P\) and \(N\) — are the hypotheses power-law BFS and PageRank violate. Regular dense kernels satisfy them closely enough that the formula is a design tool. Irregular graph kernels make \(\alpha\) an outcome of the particular graph, so the formula becomes a report of one run rather than a scaling law.
