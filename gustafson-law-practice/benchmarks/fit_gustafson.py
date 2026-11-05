"""Least-squares Gustafson fit of benchmarks/results.csv and the comparison plot.

Empirical scaled speedup at process count P is

    S(P) = P * mean(T_1) / mean(T_P)

which is the one-processor time of P copies of the unit work divided by the
measured parallel time. Gustafson's model says

    S(P) = P - alpha (P - 1).

The least-squares alpha is the minimizer of the squared residual of that line
through the measured (P, S) points. The same alpha is then drawn as an Amdahl
curve so the two laws can be compared on one figure.
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def load_times(path: Path) -> dict[int, list[float]]:
    grouped: dict[int, list[float]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[int(row["p"])].append(float(row["wall_seconds"]))
    if 1 not in grouped:
        raise SystemExit("results.csv has no p=1 rows; scaled speedup needs that baseline")
    return grouped


def fit_alpha(counts: list[int], speedups: list[float]) -> float:
    """Minimize sum_i (S_i - (P_i - alpha (P_i - 1)))^2."""
    numerator = 0.0
    denominator = 0.0
    for process_count, speedup in zip(counts, speedups):
        gap = process_count - 1
        numerator += (process_count - speedup) * gap
        denominator += gap * gap
    if denominator == 0.0:
        raise SystemExit("need a process count greater than 1 to fit alpha")
    return numerator / denominator


def coefficient_of_determination(counts: list[int], speedups: list[float], alpha: float) -> float:
    mean_speedup = statistics.fmean(speedups)
    residual = 0.0
    total = 0.0
    for process_count, speedup in zip(counts, speedups):
        predicted = process_count - alpha * (process_count - 1)
        residual += (speedup - predicted) ** 2
        total += (speedup - mean_speedup) ** 2
    if total == 0.0:
        return 1.0
    return 1.0 - residual / total


def amdahl(process_count: int, alpha: float) -> float:
    return 1.0 / (alpha + (1.0 - alpha) / process_count)


def gustafson(process_count: int, alpha: float) -> float:
    return process_count - alpha * (process_count - 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ROOT / "benchmarks" / "results.csv")
    parser.add_argument("--plot", type=Path, default=ROOT / "plots" / "scaling_comparison.png")
    args = parser.parse_args()

    grouped = load_times(args.csv)
    counts = sorted(grouped)
    t1 = statistics.fmean(grouped[1])
    summary = []
    for process_count in counts:
        samples = grouped[process_count]
        mean_time = statistics.fmean(samples)
        stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
        sem = stdev / math.sqrt(len(samples))
        # Per-run speedups use the mean one-process time as the work baseline.
        run_speedups = [process_count * t1 / sample for sample in samples]
        mean_speedup = statistics.fmean(run_speedups)
        speedup_stdev = statistics.stdev(run_speedups) if len(run_speedups) > 1 else 0.0
        speedup_sem = speedup_stdev / math.sqrt(len(run_speedups))
        summary.append(
            {
                "p": process_count,
                "mean": mean_time,
                "stdev": stdev,
                "sem": sem,
                "speedup": mean_speedup,
                "speedup_sem": speedup_sem,
                "n": len(samples),
            }
        )

    fit_counts = [row["p"] for row in summary]
    fit_speedups = [row["speedup"] for row in summary]
    alpha = fit_alpha(fit_counts, fit_speedups)
    r_squared = coefficient_of_determination(fit_counts, fit_speedups, alpha)

    print(f"alpha_observed {alpha:.8f}")
    print(f"r_squared {r_squared:.6f}")
    print(f"t1_mean {t1:.6f}")
    print("p mean_s stdev_s sem_s speedup speedup_sem")
    for row in summary:
        print(
            f"{row['p']} {row['mean']:.6f} {row['stdev']:.6f} {row['sem']:.6f} "
            f"{row['speedup']:.4f} {row['speedup_sem']:.4f}"
        )

    curve_p = list(range(1, max(fit_counts) + 1))
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    ax.plot(curve_p, curve_p, color="#000000", linewidth=1.3, label="Ideal linear speedup")
    ax.plot(
        curve_p,
        [gustafson(p, alpha) for p in curve_p],
        color="#0072B2",
        linewidth=1.8,
        label=f"Gustafson fit, α = {alpha:.4f}",
    )
    ax.plot(
        curve_p,
        [amdahl(p, alpha) for p in curve_p],
        color="#D55E00",
        linewidth=1.6,
        linestyle="--",
        label=f"Amdahl, same α = {alpha:.4f}",
    )
    ax.errorbar(
        fit_counts,
        fit_speedups,
        yerr=[row["speedup_sem"] for row in summary],
        fmt="o",
        color="#009E73",
        markersize=6,
        capsize=3,
        linewidth=1.2,
        label="Measured scaled speedup ± SEM",
    )
    ax.set_xlabel("Process count P")
    ax.set_ylabel("Scaled speedup S(P) = P · T(1) / T(P)")
    ax.set_title("Weak-scaling kernel: measured speedup against both laws")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.plot, dpi=200)
    fig.savefig(args.plot.with_suffix(".pdf"))
    plt.close(fig)
    print(f"wrote {args.plot}")
    print(f"wrote {args.plot.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
