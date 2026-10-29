"""Naive i-j-k versus interchanged i-k-j on an N x N block.

B[k, j] steps by N elements when k is the inner index. The interchanged
kernel hoists A[i, k] and streams B[k, :] and C[i, :] with stride 1.
The timed region is the leading M x M block, M = N / 2.
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
TIMED_RUNS = 3


@njit
def naive_ijk(A, B, C, M):
    for i in range(M):
        for j in range(M):
            acc = 0.0
            for k in range(M):
                acc += A[i, k] * B[k, j]
            C[i, j] = acc


@njit
def interchanged_ikj(A, B, C, M):
    for i in range(M):
        for j in range(M):
            C[i, j] = 0.0
        for k in range(M):
            aik = A[i, k]
            for j in range(M):
                C[i, j] += aik * B[k, j]


def load_params(student_id):
    if student_id:
        return get_student_params(student_id)
    path = RESULTS / "salted_params.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def time_kernel(fn, A, B, C, M):
    samples = []
    for _ in range(TIMED_RUNS):
        started = time.perf_counter()
        fn(A, B, C, M)
        samples.append(time.perf_counter() - started)
    return samples


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare i-j-k and i-k-j dense kernels.")
    parser.add_argument("--student-id", default=None, help="Override the salted student ID.")
    args = parser.parse_args(argv)

    params = load_params(args.student_id)
    n = int(params["N"])
    m = n // 2
    rng = np.random.default_rng(int(params["seed"]))
    A = rng.random((n, n))
    B = rng.random((n, n))
    naive_c = np.zeros((n, n))
    interchanged_c = np.zeros((n, n))

    check_m = 32
    naive_ijk(A, B, naive_c, check_m)
    interchanged_ikj(A, B, interchanged_c, check_m)
    max_abs_error = float(np.max(np.abs(naive_c[:check_m, :check_m] - interchanged_c[:check_m, :check_m])))
    if max_abs_error > 1e-9:
        raise RuntimeError(f"kernels disagree by {max_abs_error}")

    naive_ijk(A, B, naive_c, 8)
    interchanged_ikj(A, B, interchanged_c, 8)

    naive_times = time_kernel(naive_ijk, A, B, naive_c, m)
    interchanged_times = time_kernel(interchanged_ikj, A, B, interchanged_c, m)
    naive_median = statistics.median(naive_times)
    interchanged_median = statistics.median(interchanged_times)
    speedup = naive_median / interchanged_median

    payload = {
        "student_id": str(params["student_id"]),
        "N": n,
        "M": m,
        "seed": int(params["seed"]),
        "runs": TIMED_RUNS,
        "naive_ijk_times_s": naive_times,
        "naive_ijk_median_s": naive_median,
        "naive_time_s": naive_median,
        "interchanged_ikj_times_s": interchanged_times,
        "interchanged_ikj_median_s": interchanged_median,
        "interchanged_time_s": interchanged_median,
        "speedup": speedup,
        "check_m": check_m,
        "max_abs_error": max_abs_error,
    }
    out = RESULTS / "loop_interchange.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"naive i-j-k median {naive_median:.6f} s")
    print(f"interchanged i-k-j median {interchanged_median:.6f} s")
    print(f"speedup {speedup:.3f}")


if __name__ == "__main__":
    main()
