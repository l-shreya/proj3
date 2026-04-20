from __future__ import annotations

import warnings
from dataclasses import asdict
from datetime import datetime

from network import NetworkTestError, measure_download_speed, measure_latency
from utils import (
    RunResult,
    ensure_results_dir,
    format_results_table,
    maybe_plot_results,
    prompt_for_int,
    prompt_for_string,
    save_results_csv,
    save_results_txt,
)


def main() -> None:
    # Beginner-friendly: hide a common macOS LibreSSL/urllib3 warning that doesn't affect usage here.
    warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL.*")

    print("\nLightweight Network Bandwidth Measurement Tool\n")

    host = prompt_for_string("Target host for ping (e.g., google.com)", default="google.com")
    url = prompt_for_string(
        "File URL for download speed test (e.g., https://speed.hetzner.de/10MB.bin)",
        default="https://speed.hetzner.de/10MB.bin",
    )
    runs = prompt_for_int("How many test runs?", default=3, minimum=1, maximum=20)
    timeout_s = prompt_for_int("Timeout per test (seconds)", default=15, minimum=3, maximum=120)
    ping_count = prompt_for_int("Ping count per run", default=4, minimum=1, maximum=20)

    ensure_results_dir()

    results: list[RunResult] = []

    for i in range(1, runs + 1):
        print(f"\nRun {i}/{runs}")
        avg_latency_ms = None
        samples_ms: list[float] = []
        speed_mbps = None
        file_size_bytes = None
        seconds = None
        errors: list[str] = []

        try:
            avg_latency_ms, samples_ms = measure_latency(host=host, count=ping_count, timeout_s=timeout_s)
        except NetworkTestError as e:
            errors.append(f"Latency: {e}")

        try:
            speed_mbps, file_size_bytes, seconds = measure_download_speed(url=url, timeout_s=timeout_s)
        except NetworkTestError as e:
            errors.append(f"Download: {e}")

        results.append(
            RunResult(
                run=i,
                timestamp=datetime.now().isoformat(timespec="seconds"),
                host=host,
                url=url,
                avg_latency_ms=avg_latency_ms,
                ping_samples_ms=samples_ms,
                download_speed_mbps=speed_mbps,
                download_bytes=file_size_bytes,
                download_seconds=seconds,
                error="; ".join(errors) if errors else None,
            )
        )

        print("OK" if not errors else f"Finished with issues: {'; '.join(errors)}")

    print("\nResults\n")
    print(format_results_table(results))

    # Save outputs
    rows = [asdict(r) for r in results]
    save_results_txt(rows, path="results/output.txt")
    save_results_csv(rows, path="results/output.csv")
    print("\nSaved: results/output.txt and results/output.csv")

    # Optional visualization
    maybe_plot_results(results)


if __name__ == "__main__":
    main()