"""False sharing collapse, cache-line padding, and privatization.

Eight adjacent int64 counters occupy one 64-byte cache line. Unpadded
workers each increment their own counter, so the line ping-pongs between
cores. Padding places each counter on its own line. Privatization keeps
the increment in a register and writes the shared array once.

The shared array is created with lock=False. A lock would serialize the
updates in software and hide the coherence cost this experiment measures.
"""

import argparse
import multiprocessing as mp
import statistics
import time
from pathlib import Path

import ctypes

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PROCESS_COUNTS = (1, 2, 4, 8)
DEFAULT_ITERATIONS = 5_000_000
DEFAULT_REPEATS = 3
CACHE_LINE_INT64S = 8
COUNTER_SLOTS = 8


def worker_unpadded(counter_array, worker_id, iterations, barrier, elapsed):
    barrier.wait()
    started = time.perf_counter()
    for _ in range(iterations):
        counter_array[worker_id] += 1
    elapsed[worker_id] = time.perf_counter() - started


def worker_padded(counter_array, worker_id, iterations, barrier, elapsed):
    index = worker_id * CACHE_LINE_INT64S
    barrier.wait()
    started = time.perf_counter()
    for _ in range(iterations):
        counter_array[index] += 1
    elapsed[worker_id] = time.perf_counter() - started


def worker_privatized(counter_array, worker_id, iterations, barrier, elapsed):
    barrier.wait()
    started = time.perf_counter()
    local = 0
    for _ in range(iterations):
        local += 1
    counter_array[worker_id] = local
    elapsed[worker_id] = time.perf_counter() - started


WORKERS = {
    "unpadded": worker_unpadded,
    "padded": worker_padded,
    "privatized": worker_privatized,
}


def array_length(variant):
    if variant == "padded":
        return COUNTER_SLOTS * CACHE_LINE_INT64S
    return COUNTER_SLOTS


def run_once(variant, processes, iterations):
    counter_array = mp.Array(ctypes.c_int64, array_length(variant), lock=False)
    elapsed = mp.Array(ctypes.c_double, processes, lock=False)
    barrier = mp.Barrier(processes)
    worker = WORKERS[variant]
    procs = [
        mp.Process(
            target=worker,
            args=(counter_array, worker_id, iterations, barrier, elapsed),
        )
        for worker_id in range(processes)
    ]
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()
    failed = [proc.exitcode for proc in procs if proc.exitcode != 0]
    if failed:
        raise RuntimeError(f"{variant} P={processes} exited with {failed}")

    for worker_id in range(processes):
        index = worker_id * CACHE_LINE_INT64S if variant == "padded" else worker_id
        if variant == "privatized" and counter_array[index] != iterations:
            raise RuntimeError(
                f"privatized worker {worker_id} stored {counter_array[index]}"
            )
        if variant != "privatized" and counter_array[index] != iterations:
            raise RuntimeError(
                f"{variant} worker {worker_id} counter {counter_array[index]} != {iterations}"
            )
    return max(elapsed[worker_id] for worker_id in range(processes))


def karp_flatt(t1, tp, processes):
    """e(P) = (1/S(P) - 1/P) / (1 - 1/P), with S(P) = T(1) / T(P)."""
    if processes < 2:
        return None
    return (processes * tp / t1 - 1.0) / (processes - 1.0)


def write_tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "variant\tP\trun\truntime_s\tmedian_runtime_s\tspeedup\t"
        "karp_flatt\te_unpadded\te_padded\n"
    )
    body = []
    for row in rows:
        e = "" if row["karp_flatt"] is None else f"{row['karp_flatt']:.6f}"
        e_unpadded = "" if row["e_unpadded"] is None else f"{row['e_unpadded']:.6f}"
        e_padded = "" if row["e_padded"] is None else f"{row['e_padded']:.6f}"
        body.append(
            f"{row['variant']}\t{row['P']}\t{row['run']}\t"
            f"{row['runtime_s']:.6f}\t{row['median_runtime_s']:.6f}\t"
            f"{row['speedup']:.6f}\t{e}\t{e_unpadded}\t{e_padded}\n"
        )
    path.write_text(header + "".join(body), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure false sharing and the Karp-Flatt metric.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    args = parser.parse_args(argv)

    samples = {variant: {p: [] for p in PROCESS_COUNTS} for variant in WORKERS}
    for variant in WORKERS:
        for processes in PROCESS_COUNTS:
            for _ in range(args.repeats):
                runtime = run_once(variant, processes, args.iterations)
                samples[variant][processes].append(runtime)
                print(f"{variant:12s} P={processes}  {runtime:.3f} s", flush=True)

    rows = []
    e_by_variant = {variant: {} for variant in WORKERS}
    for variant in WORKERS:
        t1 = statistics.median(samples[variant][1])
        for processes in PROCESS_COUNTS:
            runtimes = samples[variant][processes]
            median_runtime = statistics.median(runtimes)
            speedup = t1 / median_runtime
            e = karp_flatt(t1, median_runtime, processes)
            e_by_variant[variant][processes] = e
            for run_index, runtime in enumerate(runtimes, start=1):
                rows.append(
                    {
                        "variant": variant,
                        "P": processes,
                        "run": run_index,
                        "runtime_s": runtime,
                        "median_runtime_s": median_runtime,
                        "speedup": speedup,
                        "karp_flatt": e,
                    }
                )
            e_text = "n/a" if e is None else f"{e:.3f}"
            print(
                f"{variant:12s} P={processes}  median {median_runtime:.3f} s  "
                f"S {speedup:.3f}  e {e_text}",
                flush=True,
            )

    for row in rows:
        row["e_unpadded"] = e_by_variant["unpadded"][row["P"]]
        row["e_padded"] = e_by_variant["padded"][row["P"]]

    out = RESULTS / "false_sharing_karp_flatt.tsv"
    write_tsv(out, rows)
    print(f"wrote {out}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
