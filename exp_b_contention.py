"""Experiment B: every increment takes the same lock.

The iteration count is split across workers, so the arithmetic could
scale. The shared counter cannot. Runtime grows with P, and Karp-Flatt
e(p) rises with it.

Pass an iteration count as the first argument to run a shorter pilot.
"""

import statistics
import sys
import time
from multiprocessing import Lock, Process, Value

from pin import p_core_ids, pin_current_thread

# The handout uses 2_000_000. On this host 500_000 already makes T(4) much
# larger than T(1) and makes e(4) larger than e(2), which is the check.
DEFAULT_INCREMENTS = 500_000
WORKERS = (1, 2, 4)
REPEATS = 1


def contended_worker(shared_counter, lock, iterations, cpu_id):
    pin_current_thread(cpu_id)
    for _ in range(iterations):
        with lock:
            shared_counter.value += 1


def run_contended(p, total_increments=DEFAULT_INCREMENTS):
    increments_per_worker = total_increments // p
    if increments_per_worker * p != total_increments:
        raise ValueError(f"{total_increments} does not divide evenly across {p} workers")
    counter = Value("i", 0)
    lock = Lock()
    cpu_ids = p_core_ids(p)
    procs = [
        Process(
            target=contended_worker,
            args=(counter, lock, increments_per_worker, cpu_ids[worker]),
        )
        for worker in range(p)
    ]
    t0 = time.perf_counter()
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()
    elapsed = time.perf_counter() - t0
    failed = [proc.exitcode for proc in procs if proc.exitcode != 0]
    if failed:
        raise RuntimeError(f"P={p} exited with {failed}")
    if counter.value != total_increments:
        raise RuntimeError(f"counter {counter.value} != {total_increments}")
    return elapsed


def karp_flatt(t1, tp, processes):
    return ((processes * tp / t1) - 1.0) / (processes - 1.0)


def main(argv):
    total_increments = int(argv[1]) if len(argv) > 1 else DEFAULT_INCREMENTS
    repeats = 1 if len(argv) > 1 else REPEATS
    print(f"total_increments={total_increments} repeats={repeats}", flush=True)
    print(f"pinned cores (P-cores first): {p_core_ids(max(WORKERS))}", flush=True)
    runtimes = {}
    for workers in WORKERS:
        samples = []
        for _ in range(repeats):
            samples.append(run_contended(workers, total_increments))
            print(f"P={workers} sample {samples[-1]:.3f}s", flush=True)
        runtimes[workers] = statistics.median(samples)

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


if __name__ == "__main__":
    main(sys.argv)
