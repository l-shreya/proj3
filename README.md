# Lightweight Network Bandwidth Measurement Tool (CLI)

A beginner-friendly Python CLI utility that measures:

- **Latency** (using `ping` via `subprocess`)
- **Download speed / throughput** (downloading a test file via `requests`)

It prints a clean table, supports **multiple runs** to compare results, and saves outputs to:

- `results/output.txt`
- `results/output.csv`

## What is latency?

**Latency** is the time it takes for a small packet to travel from your computer to a server and back.
Lower is better, and it’s measured in **milliseconds (ms)**.

In this project, we run `ping` and extract the per-packet `time=... ms` values, then compute the average.

## What is throughput (download speed)?

**Throughput** is how much data you can transfer per second.

We download a file and measure the time taken:

\[
\text{Download Speed (Mbps)} = \frac{\text{file\_size\_bytes} \times 8}{\text{time\_seconds} \times 10^6}
\]

## Setup

1) Create/activate a virtual environment (recommended).

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Run:

```bash
python main.py
```

## Example output

Example table (your numbers will differ):

| Run | Status | Avg Latency (ms) | Download Speed (Mbps) | Notes |
| --- | ------ | ---------------- | --------------------- | ----- |
| 1   | OK     | 12.34            | 85.20                 |       |
| 2   | OK     | 14.01            | 80.10                 |       |
| 3   | OK     | 13.22            | 83.77                 |       |

Saved files:

- `results/output.txt`
- `results/output.csv`

## Optional: simple graph

If you answer **yes** to the plot prompt, the tool will try to display a simple graph using `matplotlib`.

Install it (optional):

```bash
pip install matplotlib
```

## Folder structure

```
proj3/
├── main.py              # CLI entry point
├── network.py           # latency + download logic
├── utils.py             # helper functions (table + saving + prompts)
├── results/             # output folder (generated files are not committed)
├── requirements.txt
├── README.md
└── .gitignore
```
