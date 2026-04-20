from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any


@dataclass(frozen=True)
class RunResult:
    run: int
    timestamp: str
    host: str
    url: str
    avg_latency_ms: float | None
    ping_samples_ms: list[float]
    download_speed_mbps: float | None
    download_bytes: int | None
    download_seconds: float | None
    error: str | None = None


def ensure_results_dir(path: str = "results") -> None:
    os.makedirs(path, exist_ok=True)


def prompt_for_string(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def prompt_for_int(prompt: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            value = default
        else:
            try:
                value = int(raw)
            except ValueError:
                print("Please enter a whole number.")
                continue

        if minimum is not None and value < minimum:
            print(f"Please enter a value >= {minimum}.")
            continue
        if maximum is not None and value > maximum:
            print(f"Please enter a value <= {maximum}.")
            continue
        return value


def _try_tabulate(rows: list[list[Any]], headers: list[str]) -> str | None:
    try:
        from tabulate import tabulate  # type: ignore
    except Exception:
        return None
    return tabulate(rows, headers=headers, tablefmt="github")


def format_results_table(results: list[RunResult]) -> str:
    """
    Print a clean table and also show simple variation stats across successful runs.
    """
    rows: list[list[Any]] = []
    for r in results:
        rows.append(
            [
                r.run,
                "OK" if not r.error else "FAIL",
                f"{r.avg_latency_ms:.2f}" if r.avg_latency_ms is not None else "-",
                f"{r.download_speed_mbps:.2f}" if r.download_speed_mbps is not None else "-",
                r.error or "",
            ]
        )

    headers = ["Run", "Status", "Avg Latency (ms)", "Download Speed (Mbps)", "Notes"]
    table = _try_tabulate(rows, headers) or _simple_table(rows, headers)

    # Variation summary across successful runs
    ok_lat = [r.avg_latency_ms for r in results if r.avg_latency_ms is not None and not r.error]
    ok_spd = [r.download_speed_mbps for r in results if r.download_speed_mbps is not None and not r.error]

    summary_lines: list[str] = []
    if len(ok_lat) >= 2:
        summary_lines.append(
            f"Latency variation: mean={mean(ok_lat):.2f} ms, stdev={pstdev(ok_lat):.2f} ms, range={min(ok_lat):.2f}-{max(ok_lat):.2f} ms"
        )
    if len(ok_spd) >= 2:
        summary_lines.append(
            f"Speed variation:   mean={mean(ok_spd):.2f} Mbps, stdev={pstdev(ok_spd):.2f} Mbps, range={min(ok_spd):.2f}-{max(ok_spd):.2f} Mbps"
        )

    if summary_lines:
        return table + "\n\n" + "\n".join(summary_lines)
    return table


def _simple_table(rows: list[list[Any]], headers: list[str]) -> str:
    cols = list(zip(*([headers] + [[str(x) for x in row] for row in rows])))
    widths = [max(len(cell) for cell in col) for col in cols]

    def fmt_row(row: list[Any]) -> str:
        cells = [str(x) for x in row]
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    sep = "-+-".join("-" * w for w in widths)
    out = [fmt_row(headers), sep]
    out.extend(fmt_row(row) for row in rows)
    return "\n".join(out)


def save_results_txt(rows: list[dict[str, Any]], path: str) -> None:
    ensure_results_dir(os.path.dirname(path) or "results")
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            for k, v in row.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")


def save_results_csv(rows: list[dict[str, Any]], path: str) -> None:
    ensure_results_dir(os.path.dirname(path) or "results")
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def maybe_plot_results(results: list[RunResult]) -> None:
    choice = input("\nPlot results (latency & speed) as a simple graph? (y/N): ").strip().lower()
    if choice not in {"y", "yes"}:
        return

    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        print("matplotlib is not installed. Install it with: pip install matplotlib")
        return

    runs = [r.run for r in results]
    lat = [r.avg_latency_ms if r.avg_latency_ms is not None and not r.error else None for r in results]
    spd = [r.download_speed_mbps if r.download_speed_mbps is not None and not r.error else None for r in results]

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    axes[0].plot(runs, [x if x is not None else float("nan") for x in lat], marker="o")
    axes[0].set_title("Average Latency per Run")
    axes[0].set_ylabel("ms")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(runs, [x if x is not None else float("nan") for x in spd], marker="o", color="tab:green")
    axes[1].set_title("Download Speed per Run")
    axes[1].set_ylabel("Mbps")
    axes[1].set_xlabel("Run")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

