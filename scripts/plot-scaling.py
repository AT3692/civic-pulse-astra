"""Render collected measurements; requires matplotlib, installed only for evidence work."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

path = Path("docs/evidence/scaling.csv")
rows = list(csv.DictReader(path.open()))
if len(rows) < 2:
    raise SystemExit("Capture real measurements first")
times = [float(row["elapsed_seconds"]) for row in rows]
fig, left = plt.subplots(figsize=(10, 4.8))
right = left.twinx()
left.plot(
    times,
    [float(row["offered_vus"]) for row in rows],
    color="#287d70",
    label="Offered VUs",
)
right.step(
    times,
    [int(row["current_replicas"]) for row in rows],
    where="post",
    color="#c46432",
    label="Backend replicas",
)
left.set(
    xlabel="Elapsed seconds",
    ylabel="Offered virtual users",
    title="CivicPulse: measured load and HPA response",
)
right.set_ylabel("Backend replicas")
left.grid(alpha=0.2)
fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88))
fig.tight_layout()
fig.savefig("docs/evidence/scaling.png", dpi=180)
