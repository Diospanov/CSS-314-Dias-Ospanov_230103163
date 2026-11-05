"""Weak-scaling harness for a fixed amount of work per process.

Each process evaluates the same sine recurrence `n_parallel` times. The parent
runs a shorter copy of that recurrence before and after the parallel section so
the timed region has a real serial fraction. The pool is created outside the
timed region; one warmup call per pool size is discarded.

    python benchmarks/weak_scale_bench/bench.py

There is no compile step. The interpreter is CPython 3.11.
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def kernel(n: int, seed: float) -> float:
    """Deterministic floating-point work of length n. The return value is used."""
    acc = 0.0
    x = seed
    step = 1.0e-6
    for i in range(n):
        x = math.sin(x + i * step)
        acc += x
    return acc


def parallel_job(n: int) -> float:
    return kernel(n, 0.5)


def timed_run(pool: Pool, process_count: int, n_parallel: int, n_serial: int) -> tuple[float, float]:
    start = time.perf_counter()
    serial_prefix = kernel(n_serial, 0.25)
    parts = pool.map(parallel_job, [n_parallel] * process_count)
    serial_suffix = kernel(n_serial, 0.75)
    checksum = serial_prefix + serial_suffix + sum(parts)
    elapsed = time.perf_counter() - start
    return elapsed, checksum


def default_process_counts(logical: int) -> list[int]:
    candidates = [1, 2, 4, 8, 12, 16, logical]
    counts: list[int] = []
    for count in candidates:
        if 1 <= count <= logical and count not in counts:
            counts.append(count)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-parallel", type=int, default=1_200_000)
    parser.add_argument("--n-serial", type=int, default=50_000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument(
        "--processes",
        default="",
        help="Comma-separated process counts. Default: 1,2,4,... up to this machine.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "benchmarks" / "results.csv",
    )
    args = parser.parse_args()

    logical = __import__("os").cpu_count() or 1
    if args.processes.strip():
        counts = [int(piece) for piece in args.processes.split(",") if piece.strip()]
    else:
        counts = default_process_counts(logical)
    if len(counts) < 5:
        raise SystemExit(f"need at least 5 process counts, got {counts}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["p", "run", "wall_seconds", "n_parallel", "n_serial", "checksum"])
        for process_count in counts:
            with Pool(processes=process_count) as pool:
                timed_run(pool, process_count, args.n_parallel, args.n_serial)
                for run_index in range(1, args.runs + 1):
                    elapsed, checksum = timed_run(
                        pool, process_count, args.n_parallel, args.n_serial
                    )
                    writer.writerow(
                        [
                            process_count,
                            run_index,
                            f"{elapsed:.6f}",
                            args.n_parallel,
                            args.n_serial,
                            f"{checksum:.6f}",
                        ]
                    )
                    handle.flush()
                    print(
                        f"p={process_count} run={run_index} seconds={elapsed:.4f}",
                        flush=True,
                    )

    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
