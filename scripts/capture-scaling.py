"""Capture real HPA replicas alongside k6 VUs; never invent performance measurements.
Run while k6 writes JSON: python scripts/capture-scaling.py load.json 360
"""

import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

source = Path(sys.argv[1])
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 360
output = Path("docs/evidence/scaling.csv")
output.parent.mkdir(parents=True, exist_ok=True)
position = 0
vus = 0
with output.open("w") as handle:
    writer = csv.writer(handle)
    writer.writerow(
        [
            "timestamp",
            "elapsed_seconds",
            "offered_vus",
            "current_replicas",
            "desired_replicas",
        ]
    )
    start = time.monotonic()
    while time.monotonic() - start < duration:
        if source.exists():
            with source.open() as stream:
                stream.seek(position)
                for line in stream:
                    try:
                        point = json.loads(line)
                    except json.JSONDecodeError:
                        break  # Retry an incomplete final line on the next poll.
                    position += len(line.encode())
                    if point.get("metric") == "vus" and point.get("type") == "Point":
                        vus = point["data"]["value"]
        response = subprocess.check_output(
            ["kubectl", "get", "hpa", "backend", "-n", "civicpulse", "-o", "json"],
            text=True,
        )
        status = json.loads(response)["status"]
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                round(time.monotonic() - start, 1),
                vus,
                status.get("currentReplicas", 0),
                status.get("desiredReplicas", 0),
            ]
        )
        handle.flush()
        time.sleep(5)
print(output)
