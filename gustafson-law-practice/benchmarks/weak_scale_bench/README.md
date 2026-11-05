# Weak-scaling benchmark

Synthetic numerical kernel used to observe a Gustafson serial fraction on this machine. No compiler is involved.

## What it times

`kernel` is a sine recurrence of a fixed trip count. Every process receives the same trip count `n_parallel` (weak scaling: work per process stays constant, total work grows with the process count). The parent also runs two shorter serial copies of the same recurrence, one before the parallel map and one after it, so the timed window contains a genuine serial section plus the map and the reduction of the return values.

The process pool is started before the clock starts. Each process count is warmed up once. The recorded runs are the five calls after that warmup.

## Run

From `gustafson-law-practice/`:

```
python benchmarks/weak_scale_bench/bench.py
```

Useful overrides:

```
python benchmarks/weak_scale_bench/bench.py --processes 1,2,4,8,12,16 --runs 5 --n-parallel 1200000 --n-serial 50000
```

The raw rows land in `benchmarks/results.csv`. Fit them with:

```
python benchmarks/fit_gustafson.py
```

Interpreter used for the submitted run: CPython 3.11. Dependencies beyond the standard library: `matplotlib` (plotting only, used by the fit script and by `benchmarks/simulator.py`).
