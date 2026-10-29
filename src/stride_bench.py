"""Stride latency cliff over a buffer larger than L3.

Each step reads one float64. A 64-byte cache line holds 8 of them, so
stride-1 reuses a fetched line and stride-8 starts a new line every read.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salt import get_student_params

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
STRIDES = (1, 2, 4, 8, 16, 32, 64, 128)
WARMUP_RUNS = 5
RECORDED_RUNS = 5


@njit
def reduce_stride(data, stride):
    total = 0.0
    n = data.shape[0]
    i = 0
    while i < n:
        total += data[i]
        i += stride
    return total


def load_params(student_id):
    if student_id:
        return get_student_params(student_id)
    path = RESULTS / "salted_params.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def elements_touched(length, stride):
    return (length + stride - 1) // stride


def benchmark_stride(data, stride):
    touched = elements_touched(data.shape[0], stride)
    for _ in range(WARMUP_RUNS):
        total = reduce_stride(data, stride)
    samples = []
    for _ in range(RECORDED_RUNS):
        started = time.perf_counter_ns()
        total = reduce_stride(data, stride)
        samples.append(time.perf_counter_ns() - started)
    if total != touched:
        raise RuntimeError(f"stride {stride} reduction {total} != {touched}")
    median_ns = statistics.median(samples)
    return {
        "stride": stride,
        "elements_touched": touched,
        "median_time_ns": median_ns,
        "latency_per_element_ns": median_ns / touched,
    }


def write_tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "stride\telements_touched\tmedian_time_ns\tlatency_per_element_ns\n"
    )
    lines = [
        f"{row['stride']}\t{row['elements_touched']}\t"
        f"{row['median_time_ns']:.0f}\t{row['latency_per_element_ns']:.6f}\n"
        for row in rows
    ]
    path.write_text(header + "".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure per-element read latency versus stride.")
    parser.add_argument("--student-id", default=None, help="Override the salted student ID.")
    args = parser.parse_args(argv)

    params = load_params(args.student_id)
    length = int(params["buffer_elements"])
    data = np.ones(length, dtype=np.float64)
    reduce_stride(data[:64], 1)

    rows = [benchmark_stride(data, stride) for stride in STRIDES]
    out = RESULTS / "stride_results.tsv"
    write_tsv(out, rows)
    print(f"wrote {out}")
    for row in rows:
        print(
            f"stride {row['stride']:3d}  "
            f"latency {row['latency_per_element_ns']:.3f} ns/elem"
        )


if __name__ == "__main__":
    main()
