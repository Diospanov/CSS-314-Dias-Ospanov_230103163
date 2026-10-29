"""Experiment A: a fixed serial tail in front of parallel work.

Workers compute a fixed set of chunks. The master sleeps 0.40 s before
dispatch. Karp-Flatt e(p) stays near that serial fraction when the
parallel part scales.

The pool is opened before the timer. On Windows, creating the pool
spawns interpreters, and counting that startup as serial work moves e(p)
off the flat Amdahl signature this experiment is meant to show.
"""

import statistics
import time
import math
from multiprocessing import Pool

from pin import init_worker, make_ticket, p_core_ids, park_parent

SLEEP_S = 0.40
TOTAL_CHUNKS = 16
# Median of the five-trial run used in RESULTS.md. One trial is the default
# here so a re-run finishes in class; that five-trial median is the recorded one.
CHUNK_SIZE = 900_000
WORKERS = (1, 2, 4)
REPEATS = 1


def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))


def time_once(workers, total_chunks=TOTAL_CHUNKS, chunk_size=CHUNK_SIZE):
    ticket = make_ticket()
    cpu_ids = p_core_ids(workers)
    with Pool(processes=workers, initializer=init_worker, initargs=(ticket, cpu_ids)) as pool:
        pool.map(heavy_math, [1000] * workers)
        t0 = time.perf_counter()
        time.sleep(SLEEP_S)
        pool.map(heavy_math, [chunk_size] * total_chunks, chunksize=total_chunks // workers)
        return time.perf_counter() - t0


def karp_flatt(t1, tp, processes):
    return ((processes * tp / t1) - 1.0) / (processes - 1.0)


def main():
    parent_cpu = park_parent()
    print(f"pinned cores (P-cores first): {p_core_ids(max(WORKERS))}", flush=True)
    print(f"parent parked on CPU {parent_cpu}", flush=True)
    samples = {workers: [] for workers in WORKERS}
    for _ in range(REPEATS):
        for workers in WORKERS:
            elapsed = time_once(workers)
            samples[workers].append(elapsed)
            print(f"P={workers} sample {elapsed:.4f}s", flush=True)
    runtimes = {}
    for workers in WORKERS:
        runtimes[workers] = statistics.median(samples[workers])
        print(
            f"P={workers} samples={[round(s, 4) for s in samples[workers]]} "
            f"median={runtimes[workers]:.4f}s",
            flush=True,
        )

    t1 = runtimes[1]
    print(f"P=1 | Runtime={t1:.3f}s | Speedup=1.00x | Karp-Flatt e=n/a", flush=True)
    for workers in WORKERS[1:]:
        tp = runtimes[workers]
        speedup = t1 / tp
        metric = karp_flatt(t1, tp, workers)
        print(
            f"P={workers} | Runtime={tp:.3f}s | Speedup={speedup:.2f}x | Karp-Flatt e={metric:.3f}",
            flush=True,
        )
    ratio = karp_flatt(t1, runtimes[4], 4) / karp_flatt(t1, runtimes[2], 2)
    print(f"e(4)/e(2)={ratio:.3f}", flush=True)


if __name__ == "__main__":
    main()
