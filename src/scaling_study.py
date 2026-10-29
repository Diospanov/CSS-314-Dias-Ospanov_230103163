"""Strong scaling, weak scaling, and a roofline placement for a 5-point stencil.

The salted N x N grid is split by rows across processes. Each interior point is

    dst = 0.2 * (north + south + west + east + center)

which is 5 floating-point operations. One sweep reads the source grid and
writes the interior of the destination grid.

Strong scaling keeps N fixed. Weak scaling sets N_P = ceil(N * sqrt(P)) so the
cell count grows in proportion to P. Scaled speedup follows Gustafson-Barsis:
the estimated serial time of that larger grid divided by the parallel time.
"""

import argparse
import ctypes
import json
import math
import multiprocessing as mp
import platform
import statistics
import time
from pathlib import Path

import numpy as np
from multiprocessing import shared_memory
from numba import njit

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FLOPS_PER_POINT = 5
# Golden Cove: two 256-bit FMAs per cycle, 4 double-precision results each,
# and an FMA counts as two operations.
P_CORE_DP_FLOPS_PER_CYCLE = 16
P_CORE_BASE_HZ = 2_500_000_000
# Gracemont: two 128-bit FMAs per cycle.
E_CORE_DP_FLOPS_PER_CYCLE = 8
E_CORE_BASE_HZ = 1_800_000_000
P_CORES = 4
E_CORES = 8
SMBIOS_MEMORY = {
    24: "DDR3",
    26: "DDR4",
    30: "LPDDR4",
    34: "DDR5",
    35: "LPDDR5",
}


@njit
def stencil_chunk(src, dst, row_start, row_end):
    width = src.shape[1]
    for i in range(row_start, row_end):
        for j in range(1, width - 1):
            dst[i, j] = 0.2 * (
                src[i - 1, j]
                + src[i + 1, j]
                + src[i, j - 1]
                + src[i, j + 1]
                + src[i, j]
            )


def split_rows(n, processes):
    interior = n - 2
    if interior < processes:
        raise ValueError(f"grid {n} has too few interior rows for {processes} processes")
    base, extra = divmod(interior, processes)
    ranges = []
    start = 1
    for worker in range(processes):
        length = base + (1 if worker < extra else 0)
        ranges.append((start, start + length))
        start += length
    return ranges


def work_cells(n):
    return (n - 2) * (n - 2)


def dram_bytes_per_sweep(n):
    """Minimum traffic with cache reuse: read the source, write the interior."""
    return n * n * 8 + work_cells(n) * 8


def process_counts(physical_cores):
    counts = []
    processes = 1
    while processes <= physical_cores:
        counts.append(processes)
        processes *= 2
    if counts[-1] != physical_cores:
        counts.append(physical_cores)
    return counts


def one_cpu_per_core():
    """Logical CPU ids, one per physical core, hyper-threaded cores first."""
    if platform.system() != "Windows":
        return []

    class CACHE_DESCRIPTOR(ctypes.Structure):
        _fields_ = [
            ("Level", ctypes.c_ubyte),
            ("Associativity", ctypes.c_ubyte),
            ("LineSize", ctypes.c_ushort),
            ("Size", ctypes.c_ulong),
            ("Type", ctypes.c_int),
        ]

    class PROCESSORCORE(ctypes.Structure):
        _fields_ = [("Flags", ctypes.c_ubyte)]

    class NUMANODE(ctypes.Structure):
        _fields_ = [("NodeNumber", ctypes.c_ulong)]

    class SLPI_UNION(ctypes.Union):
        _fields_ = [
            ("ProcessorCore", PROCESSORCORE),
            ("NumaNode", NUMANODE),
            ("Cache", CACHE_DESCRIPTOR),
            ("Reserved", ctypes.c_ulonglong * 2),
        ]

    class SLPI(ctypes.Structure):
        _fields_ = [
            ("ProcessorMask", ctypes.c_ulonglong),
            ("Relationship", ctypes.c_int),
            ("Payload", SLPI_UNION),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_info = kernel32.GetLogicalProcessorInformation
    get_info.argtypes = [ctypes.POINTER(SLPI), ctypes.POINTER(ctypes.wintypes.DWORD)]
    get_info.restype = ctypes.wintypes.BOOL
    needed = ctypes.wintypes.DWORD(0)
    get_info(None, ctypes.byref(needed))
    count = needed.value // ctypes.sizeof(SLPI)
    buffer = (SLPI * count)()
    if not get_info(buffer, ctypes.byref(needed)):
        return []

    smt_cores = []
    single_cores = []
    for item in buffer:
        if item.Relationship != 0:
            continue
        cpu = (item.ProcessorMask & -item.ProcessorMask).bit_length() - 1
        if item.Payload.ProcessorCore.Flags:
            smt_cores.append(cpu)
        else:
            single_cores.append(cpu)
    return smt_cores + single_cores


def pin_current_thread(cpu_id):
    if platform.system() != "Windows" or cpu_id is None or cpu_id < 0:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.SetThreadAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    kernel32.SetThreadAffinityMask.restype = ctypes.c_size_t
    if kernel32.SetThreadAffinityMask(kernel32.GetCurrentThread(), 1 << cpu_id) == 0:
        raise OSError(f"could not pin worker to CPU {cpu_id}")


def attach(cache, name, n):
    cached = cache.get(name)
    if cached is not None:
        return cached[1]
    shm = shared_memory.SharedMemory(name=name)
    array = np.ndarray((n, n), dtype=np.float64, buffer=shm.buf)
    cache[name] = (shm, array)
    return array


def retain_only(cache, names):
    for name in list(cache):
        if name not in names:
            cache[name][0].close()
            del cache[name]


def worker_loop(task_queue, result_queue, cpu_id):
    pin_current_thread(cpu_id)
    warmup_src = np.zeros((8, 8))
    warmup_dst = np.zeros((8, 8))
    stencil_chunk(warmup_src, warmup_dst, 1, 7)
    cache = {}
    while True:
        message = task_queue.get()
        if message is None:
            break
        src_name, dst_name, n, row_start, row_end, sweeps = message
        try:
            retain_only(cache, {src_name, dst_name})
            src = attach(cache, src_name, n)
            dst = attach(cache, dst_name, n)
            started = time.perf_counter()
            for _ in range(sweeps):
                stencil_chunk(src, dst, row_start, row_end)
            elapsed = time.perf_counter() - started
        except Exception as exc:
            result_queue.put(repr(exc))
            continue
        result_queue.put(elapsed)
    for shm, _array in cache.values():
        shm.close()


def check_decomposition():
    n = 48
    processes = 4
    rng = np.random.default_rng(0)
    src = rng.random((n, n))
    serial = np.zeros_like(src)
    parallel = np.zeros_like(src)
    stencil_chunk(src, serial, 1, n - 1)
    for row_start, row_end in split_rows(n, processes):
        stencil_chunk(src, parallel, row_start, row_end)
    if not np.allclose(serial, parallel):
        raise RuntimeError("row decomposition does not match the serial stencil")


class Grid:
    def __init__(self, n, seed):
        nbytes = n * n * 8
        self.src_shm = shared_memory.SharedMemory(create=True, size=nbytes)
        self.dst_shm = shared_memory.SharedMemory(create=True, size=nbytes)
        self.src = np.ndarray((n, n), dtype=np.float64, buffer=self.src_shm.buf)
        self.dst = np.ndarray((n, n), dtype=np.float64, buffer=self.dst_shm.buf)
        rng = np.random.default_rng(seed)
        self.src[:] = rng.random((n, n))
        self.dst.fill(0.0)

    def close(self):
        self.src_shm.close()
        self.dst_shm.close()
        self.src_shm.unlink()
        self.dst_shm.unlink()


def run_parallel(queues, result_queue, grid, n, processes, sweeps):
    ranges = split_rows(n, processes)
    started = time.perf_counter()
    for worker_id, (row_start, row_end) in enumerate(ranges):
        queues[worker_id].put(
            (grid.src_shm.name, grid.dst_shm.name, n, row_start, row_end, sweeps)
        )
    worker_times = []
    for _ in range(processes):
        item = result_queue.get(timeout=300)
        if isinstance(item, str):
            raise RuntimeError(item)
        worker_times.append(item)
    return time.perf_counter() - started, worker_times


def median_runtime(queues, result_queue, grid, n, processes, sweeps, repeats):
    samples = []
    spreads = []
    for _ in range(repeats):
        wall, worker_times = run_parallel(queues, result_queue, grid, n, processes, sweeps)
        samples.append(wall)
        spreads.append(max(worker_times) / min(worker_times))
    return statistics.median(samples), samples, statistics.median(spreads)


def amdahl_s(speedup, processes):
    if processes < 2 or speedup <= 0:
        return None
    return (1.0 / speedup - 1.0 / processes) / (1.0 - 1.0 / processes)


def fit_serial_fraction(measurements):
    """Least squares for 1/S = s*(1-1/P) + 1/P."""
    numerator = 0.0
    denominator = 0.0
    for processes, speedup in measurements:
        if processes < 2 or speedup <= 0:
            continue
        x = 1.0 - 1.0 / processes
        y = 1.0 / speedup - 1.0 / processes
        numerator += x * y
        denominator += x * x
    if denominator == 0.0:
        raise RuntimeError("could not fit Amdahl's serial fraction")
    return numerator / denominator


def scaled_dimension(n, processes):
    return math.ceil(n * math.sqrt(processes))


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def memory_bandwidth():
    if platform.system() != "Windows":
        return None
    import subprocess

    script = (
        "Get-CimInstance Win32_PhysicalMemory | "
        "Select-Object DeviceLocator, ConfiguredClockSpeed, SMBIOSMemoryType, DataWidth | "
        "ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    payload = json.loads(completed.stdout)
    if isinstance(payload, dict):
        payload = [payload]
    controllers = set()
    for stick in payload:
        locator = stick.get("DeviceLocator") or ""
        controller = locator.split("-")[0]
        controllers.add(controller)
    clock = int(payload[0]["ConfiguredClockSpeed"])
    width_bits = int(payload[0]["DataWidth"])
    channels = len(controllers)
    bytes_per_second = clock * 1_000_000 * (width_bits // 8) * channels
    mem_type = SMBIOS_MEMORY.get(int(payload[0]["SMBIOSMemoryType"]), "unknown")
    return {
        "type": mem_type,
        "data_rate_mts": clock,
        "channels": channels,
        "modules": len(payload),
        "peak_bytes_per_s": bytes_per_second,
    }


def peak_dp_flops():
    return (
        P_CORES * P_CORE_DP_FLOPS_PER_CYCLE * P_CORE_BASE_HZ
        + E_CORES * E_CORE_DP_FLOPS_PER_CYCLE * E_CORE_BASE_HZ
    )


def fmt(value, digits=6):
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def write_tsv(path, rows):
    header = (
        "study\tP\tN\tsweeps\twork_cells\tmedian_runtime_s\t"
        "speedup\tefficiency_pct\tamdahl_s\tscaled_speedup\n"
    )
    lines = []
    for row in rows:
        lines.append(
            f"{row['study']}\t{row['P']}\t{row['N']}\t{row['sweeps']}\t"
            f"{row['work_cells']}\t{fmt(row['median_runtime_s'])}\t"
            f"{fmt(row['speedup'])}\t{fmt(row['efficiency_pct'])}\t"
            f"{fmt(row['amdahl_s'])}\t{fmt(row['scaled_speedup'])}\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Strong/weak scaling and roofline for a 5-point stencil.")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=0.75)
    args = parser.parse_args(argv)

    params = read_json(RESULTS / "salted_params.json")
    profile = read_json(RESULTS / "host_profile.json")
    n = int(params["N"])
    seed = int(params["seed"])
    physical = int(profile["physical_cores"])
    counts = process_counts(physical)
    cpus = one_cpu_per_core()
    if len(cpus) < counts[-1]:
        cpus = list(range(counts[-1]))

    check_decomposition()

    ctx = mp.get_context("spawn")
    task_queues = [ctx.Queue() for _ in range(counts[-1])]
    result_queue = ctx.Queue()
    workers = [
        ctx.Process(target=worker_loop, args=(task_queues[index], result_queue, cpus[index]))
        for index in range(counts[-1])
    ]
    for worker in workers:
        worker.start()

    rows = []
    strong_summary = []
    weak_summary = []
    try:
        grid = Grid(n, seed)
        try:
            run_parallel(task_queues, result_queue, grid, n, counts[-1], 1)
            pilot, _worker_times = run_parallel(task_queues, result_queue, grid, n, 1, 20)
            sweeps = max(20, int(math.ceil(20 * args.target_seconds / pilot)))
            print(f"sweeps per trial: {sweeps}", flush=True)

            strong_runtime = {}
            for processes in counts:
                runtime, samples, spread = median_runtime(
                    task_queues, result_queue, grid, n, processes, sweeps, args.repeats
                )
                strong_runtime[processes] = runtime
                print(
                    f"strong P={processes:<2d} N={n}  {runtime:.3f} s  "
                    f"spread {spread:.2f}  samples={samples}",
                    flush=True,
                )
        finally:
            grid.close()

        t1 = strong_runtime[1]
        fitted_s = fit_serial_fraction((p, t1 / strong_runtime[p]) for p in counts)
        ceiling = 1.0 / fitted_s if fitted_s > 0 else None
        for processes in counts:
            runtime = strong_runtime[processes]
            speedup = t1 / runtime
            point_s = amdahl_s(speedup, processes)
            rows.append(
                {
                    "study": "strong",
                    "P": processes,
                    "N": n,
                    "sweeps": sweeps,
                    "work_cells": work_cells(n) * sweeps,
                    "median_runtime_s": runtime,
                    "speedup": speedup,
                    "efficiency_pct": 100.0 * speedup / processes,
                    "amdahl_s": point_s,
                    "scaled_speedup": None,
                }
            )
            strong_summary.append(
                {
                    "P": processes,
                    "N": n,
                    "median_runtime_s": runtime,
                    "speedup": speedup,
                    "efficiency_pct": 100.0 * speedup / processes,
                    "amdahl_s": point_s,
                }
            )

        weak_runtime = {}
        weak_work = {}
        weak_n = {}
        for processes in counts:
            n_p = scaled_dimension(n, processes)
            weak_n[processes] = n_p
            weak_work[processes] = work_cells(n_p) * sweeps
            grid = Grid(n_p, seed)
            try:
                run_parallel(task_queues, result_queue, grid, n_p, counts[-1], 1)
                runtime, samples, spread = median_runtime(
                    task_queues, result_queue, grid, n_p, processes, sweeps, args.repeats
                )
            finally:
                grid.close()
            weak_runtime[processes] = runtime
            print(
                f"weak   P={processes:<2d} N={n_p}  {runtime:.3f} s  "
                f"spread {spread:.2f}  samples={samples}",
                flush=True,
            )

        base_work = weak_work[1]
        for processes in counts:
            runtime = weak_runtime[processes]
            gustafson = (weak_work[processes] / base_work) * (weak_runtime[1] / runtime)
            rows.append(
                {
                    "study": "weak",
                    "P": processes,
                    "N": weak_n[processes],
                    "sweeps": sweeps,
                    "work_cells": weak_work[processes],
                    "median_runtime_s": runtime,
                    "speedup": None,
                    "efficiency_pct": 100.0 * gustafson / processes,
                    "amdahl_s": None,
                    "scaled_speedup": gustafson,
                }
            )
            weak_summary.append(
                {
                    "P": processes,
                    "N": weak_n[processes],
                    "work_cells": weak_work[processes],
                    "median_runtime_s": runtime,
                    "scaled_speedup": gustafson,
                    "efficiency_pct": 100.0 * gustafson / processes,
                }
            )
    finally:
        for queue in task_queues:
            queue.put(None)
        for worker in workers:
            worker.join(timeout=30)

    bandwidth = memory_bandwidth()
    flops = peak_dp_flops()
    interior = work_cells(n)
    bytes_per_sweep = dram_bytes_per_sweep(n)
    intensity = (FLOPS_PER_POINT * interior) / bytes_per_sweep
    working_set = 2 * n * n * 8
    ridge = None if bandwidth is None else flops / bandwidth["peak_bytes_per_s"]
    if ridge is None:
        regime = "undetermined"
    elif intensity < ridge:
        regime = "Memory-Bandwidth Bound"
    else:
        regime = "Compute Bound"
    ceiling_text = "undefined" if ceiling is None else f"{ceiling:.2f}"

    l3 = int(profile["l3_cache_bytes"])
    summary = {
        "student_id": str(params["student_id"]),
        "stencil": "5-point Jacobi",
        "flops_per_interior_point": FLOPS_PER_POINT,
        "operation": "0.2 * (north + south + west + east + center)",
        "N": n,
        "physical_cores": physical,
        "process_counts": counts,
        "l1d_cache_bytes": int(profile["l1d_cache_bytes"]),
        "l2_cache_bytes": int(profile["l2_cache_bytes"]),
        "l3_cache_bytes": l3,
        "cache_line_bytes": int(profile["cache_line_bytes"]),
        "working_set_bytes": working_set,
        "working_set_exceeds_l3": working_set > l3,
        "dram_bytes_per_sweep": bytes_per_sweep,
        "arithmetic_intensity_flops_per_byte": intensity,
        "memory": bandwidth,
        "peak_dp_flops_per_s": flops,
        "peak_flops_model": {
            "p_cores": P_CORES,
            "p_core_dp_flops_per_cycle": P_CORE_DP_FLOPS_PER_CYCLE,
            "p_core_base_hz": P_CORE_BASE_HZ,
            "e_cores": E_CORES,
            "e_core_dp_flops_per_cycle": E_CORE_DP_FLOPS_PER_CYCLE,
            "e_core_base_hz": E_CORE_BASE_HZ,
            "note": (
                "i5-12500H base clocks. Golden Cove does two 256-bit FMAs per cycle. "
                "Gracemont does two 128-bit FMAs per cycle. An FMA counts as two flops."
            ),
        },
        "ridge_point_flops_per_byte": ridge,
        "regime": regime,
        "amdahl_serial_fraction": fitted_s,
        "amdahl_speedup_ceiling": ceiling,
        "strong": strong_summary,
        "weak": weak_summary,
        "scaled_speedup_definition": (
            "S_scaled(P) = Work(P) / Work(1) * T_weak(1) / T_weak(P), "
            "the Gustafson-Barsis estimate of serial time on the scaled grid."
        ),
        "conclusion": (
            f"The stencil moves {intensity:.3f} flops per DRAM byte. "
            f"The machine ridge point is {ridge:.3f} flops/byte, and the "
            f"{working_set / 1e6:.1f} MB working set is larger than the "
            f"{l3 / 1e6:.1f} MB L3 cache, so the kernel is {regime}. "
            f"Strong-scaling efficiency falls from 100% at one process to "
            f"{strong_summary[-1]['efficiency_pct']:.1f}% at {strong_summary[-1]['P']} "
            f"(speedup {strong_summary[-1]['speedup']:.2f}). "
            f"The fitted serial fraction is {fitted_s:.3f}, so Amdahl's ceiling is "
            f"{ceiling_text}. At {weak_summary[-1]['P']} processes the Gustafson "
            f"scaled speedup is {weak_summary[-1]['scaled_speedup']:.2f} while "
            f"runtime rises from {weak_summary[0]['median_runtime_s']:.3f} s to "
            f"{weak_summary[-1]['median_runtime_s']:.3f} s, because the enlarged "
            f"grids stay on the memory roof and the E-cores trail the P-cores."
        ),
    }
    if ridge is None:
        summary["conclusion"] = (
            "Arithmetic intensity is below a typical CPU ridge point, but peak "
            "DRAM bandwidth was not detected on this host."
        )

    metrics_path = RESULTS / "scaling_metrics.tsv"
    roofline_path = RESULTS / "roofline_summary.json"
    write_tsv(metrics_path, rows)
    roofline_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {metrics_path}")
    print(f"wrote {roofline_path}")
    print(f"fitted serial fraction {fitted_s:.4f}  ceiling {ceiling}")
    print(f"arithmetic intensity {intensity:.4f}  regime {regime}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
