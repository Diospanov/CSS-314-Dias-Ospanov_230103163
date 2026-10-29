"""Experiment C: privatize the counter, then reduce once.

Each worker adds into a local variable. The parent sums the returned
values after the loop. No lock is held inside the iteration.

The pool is opened and warmed before the timer, same reason as
Experiment A: process startup is not part of the parallel section.
"""

import statistics
import time
from multiprocessing import Pool

from pin import init_worker, make_ticket, p_core_ids

TOTAL_INCREMENTS = 20_000_000
WORKERS = (1, 2, 4)
REPEATS = 1


def private_worker(iterations):
    local_sum = 0
    for _ in range(iterations):
        local_sum += 1
    return local_sum


def run_privatized(p, total_increments=TOTAL_INCREMENTS, repeats=REPEATS):
    increments_per_worker = total_increments // p
    if increments_per_worker * p != total_increments:
        raise ValueError(f"{total_increments} does not divide evenly across {p} workers")
    tasks = [increments_per_worker] * p
    ticket = make_ticket()
    cpu_ids = p_core_ids(p)
    with Pool(processes=p, initializer=init_worker, initargs=(ticket, cpu_ids)) as pool:
        pool.map(private_worker, [1000] * p)
        samples = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            results = pool.map(private_worker, tasks)
            total = sum(results)
            samples.append(time.perf_counter() - t0)
            if total != total_increments:
                raise RuntimeError(f"reduced {total} != {total_increments}")
    return statistics.median(samples), samples


def karp_flatt(t1, tp, processes):
    return ((processes * tp / t1) - 1.0) / (processes - 1.0)


def main():
    print(f"pinned cores (P-cores first): {p_core_ids(max(WORKERS))}", flush=True)
    runtimes = {}
    for workers in WORKERS:
        median, samples = run_privatized(workers)
        runtimes[workers] = median
        print(f"P={workers} samples={[round(s, 4) for s in samples]} median={median:.4f}s", flush=True)

    t1 = runtimes[1]
    print(f"P=1 | Runtime={t1:.3f}s | Speedup=1.00x | Karp-Flatt e=n/a", flush=True)
    for workers in WORKERS[1:]:
        tp = runtimes[workers]
        speedup = t1 / tp
        metric = karp_flatt(t1, tp, workers)
        efficiency = 100.0 * speedup / workers
        print(
            f"P={workers} | Runtime={tp:.3f}s | Speedup={speedup:.2f}x | "
            f"Karp-Flatt e={metric:.3f} | efficiency={efficiency:.1f}%",
            flush=True,
        )


if __name__ == "__main__":
    main()
