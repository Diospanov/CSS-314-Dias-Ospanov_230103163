"""Amdahl and Gustafson sweep for P in [1, 65536] and alpha in [0.001, 0.20].

Writes a CSV of both laws and an overlay plot of speedup and efficiency.
Run from anywhere:

    python benchmarks/simulator.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALPHAS = (0.001, 0.01, 0.02, 0.04, 0.05, 0.08, 0.10, 0.15, 0.20)


def processor_counts(p_max: int) -> list[int]:
    counts = []
    p = 1
    while p <= p_max:
        counts.append(p)
        p *= 2
    return counts


def amdahl_speedup(p: int, serial: float) -> float:
    return 1.0 / (serial + (1.0 - serial) / p)


def gustafson_speedup(p: int, alpha: float) -> float:
    return p - alpha * (p - 1)


def write_csv(path: Path, counts: list[int], alphas: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "p",
                "alpha",
                "speedup_gustafson",
                "efficiency_gustafson",
                "speedup_amdahl",
                "efficiency_amdahl",
            ]
        )
        for alpha in alphas:
            for p in counts:
                s_g = gustafson_speedup(p, alpha)
                s_a = amdahl_speedup(p, alpha)
                writer.writerow(
                    [
                        p,
                        f"{alpha:.6f}",
                        f"{s_g:.10f}",
                        f"{s_g / p:.10f}",
                        f"{s_a:.10f}",
                        f"{s_a / p:.10f}",
                    ]
                )


def plot_overlay(path: Path, counts: list[int], alphas: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # A few curves keep the overlay readable; the CSV still holds every alpha.
    shown = [a for a in (0.01, 0.05, 0.10, 0.20) if any(abs(a - x) < 1e-12 for x in alphas)]
    if not shown:
        shown = list(alphas[:4])

    colors = {
        0.01: "#0072B2",
        0.05: "#E69F00",
        0.10: "#009E73",
        0.20: "#D55E00",
    }
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))

    ax = axes[0]
    ax.plot(counts, counts, color="#000000", linewidth=1.2, label="Ideal linear")
    for alpha in shown:
        color = colors.get(alpha, None)
        s_g = [gustafson_speedup(p, alpha) for p in counts]
        s_a = [amdahl_speedup(p, alpha) for p in counts]
        label = f"α = {alpha:g}"
        ax.plot(counts, s_g, color=color, linewidth=1.8, label=f"Gustafson, {label}")
        ax.plot(
            counts,
            s_a,
            color=color,
            linewidth=1.4,
            linestyle="--",
            label=f"Amdahl, {label}",
        )
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Processors P")
    ax.set_ylabel("Speedup S(P)")
    ax.set_title("Strong scaling (dashed) and weak scaling (solid)")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.5)
    ax.legend(fontsize=7, ncol=2, frameon=False)

    ax = axes[1]
    ax.axhline(1.0, color="#000000", linewidth=1.0, label="Ideal efficiency")
    for alpha in shown:
        color = colors.get(alpha, None)
        e_g = [gustafson_speedup(p, alpha) / p for p in counts]
        e_a = [amdahl_speedup(p, alpha) / p for p in counts]
        label = f"α = {alpha:g}"
        ax.plot(counts, e_g, color=color, linewidth=1.8, label=f"Gustafson, {label}")
        ax.plot(
            counts,
            e_a,
            color=color,
            linewidth=1.4,
            linestyle="--",
            label=f"Amdahl, {label}",
        )
    ax.set_xscale("log", base=2)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel("Processors P")
    ax.set_ylabel("Efficiency E(P) = S(P) / P")
    ax.set_title("Efficiency floor under Gustafson, collapse under Amdahl")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.5)
    ax.legend(
        fontsize=7,
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
    )

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    if path.suffix.lower() == ".png":
        fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def parse_alphas(text: str) -> list[float]:
    alphas = [float(piece) for piece in text.split(",") if piece.strip()]
    for alpha in alphas:
        if not 0.001 - 1e-15 <= alpha <= 0.20 + 1e-15:
            raise SystemExit(f"alpha {alpha} is outside the required interval [0.001, 0.20]")
    return alphas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p-max", type=int, default=65536)
    parser.add_argument("--alphas", default=",".join(str(a) for a in DEFAULT_ALPHAS))
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "benchmarks" / "amdahl_gustafson.csv",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=ROOT / "plots" / "simulator_overlay.png",
    )
    args = parser.parse_args()
    if args.p_max < 1 or args.p_max > 65536:
        raise SystemExit("p-max must lie in [1, 65536]")

    counts = processor_counts(args.p_max)
    alphas = parse_alphas(args.alphas)
    write_csv(args.csv, counts, alphas)
    plot_overlay(args.plot, counts, alphas)
    print(f"wrote {args.csv}")
    print(f"wrote {args.plot}")
    print(f"wrote {args.plot.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
