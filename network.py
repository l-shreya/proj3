from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests


class NetworkTestError(Exception):
    """Raised when a network test fails in a user-friendly way."""


@dataclass(frozen=True)
class DownloadResult:
    speed_mbps: float
    file_size_bytes: int
    seconds: float


_PING_TIME_RE = re.compile(r"time[=<]([\d.]+)\s*ms")


def _validate_host(host: str) -> None:
    host = host.strip()
    if not host:
        raise NetworkTestError("Host cannot be empty.")


def _validate_url(url: str) -> None:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise NetworkTestError("Invalid URL. Please provide a full http(s) URL (example: https://example.com/file.bin).")


def measure_latency(host: str, count: int = 4, timeout_s: int = 15) -> tuple[float, list[float]]:
    """
    Measure average latency using the system `ping` command.

    Returns (average_latency_ms, samples_ms).
    """
    _validate_host(host)

    try:
        # macOS/Linux style ping. On macOS, `-W` isn't supported, so we rely on subprocess timeout.
        completed = subprocess.run(
            ["ping", "-c", str(count), host],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        raise NetworkTestError(f"Ping timed out after {timeout_s}s.") from e
    except FileNotFoundError as e:
        raise NetworkTestError("`ping` command not found on this system.") from e
    except Exception as e:
        raise NetworkTestError(f"Ping failed: {e}") from e

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    # If ping returns non-zero, we still might have partial samples; try to parse anyway.
    samples = [float(x) for x in _PING_TIME_RE.findall(stdout)]
    if not samples:
        msg = stderr.strip() or "No latency samples found. Check the host name and your network connection."
        raise NetworkTestError(msg)

    avg = sum(samples) / len(samples)
    return avg, samples


def measure_download_speed(url: str, timeout_s: int = 15) -> tuple[float, int, float]:
    """
    Download a URL and calculate throughput in Mbps.

    Download Speed (Mbps) = (file_size_bytes * 8) / (time_seconds * 1e6)
    """
    _validate_url(url)

    try:
        start = time.perf_counter()
        with requests.get(url, stream=True, timeout=timeout_s) as resp:
            resp.raise_for_status()
            total_bytes = 0
            for chunk in resp.iter_content(chunk_size=1024 * 64):
                if chunk:
                    total_bytes += len(chunk)
        end = time.perf_counter()
    except requests.exceptions.MissingSchema as e:
        raise NetworkTestError("Invalid URL. Please include http:// or https://") from e
    except requests.exceptions.InvalidURL as e:
        raise NetworkTestError("Invalid URL. Please check the URL and try again.") from e
    except requests.exceptions.Timeout as e:
        raise NetworkTestError(f"Download timed out after {timeout_s}s.") from e
    except requests.exceptions.ConnectionError as e:
        raise NetworkTestError("Network connection error while downloading. Check your internet and URL.") from e
    except requests.HTTPError as e:
        raise NetworkTestError(f"Server returned an error: {e}") from e
    except Exception as e:
        raise NetworkTestError(f"Download failed: {e}") from e

    seconds = max(end - start, 1e-9)
    speed_mbps = (total_bytes * 8) / (seconds * 1e6)
    return speed_mbps, total_bytes, seconds